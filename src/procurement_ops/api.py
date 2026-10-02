"""HTTP API for the procurement workflow.

FastAPI is only the web layer in this project. It receives HTTP requests and
passes them to the compiled LangGraph workflow. The graph still owns all
procurement logic and state transitions.
"""

import json
import os
from collections.abc import Iterator
from typing import Any

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from procurement_ops.graph import build_graph
from procurement_ops.models import ProcurementRequest
from procurement_ops.state import ProcurementState, create_initial_state


# Keeping the model name in an environment variable means that changing the
# model does not require changing the API code. The default is useful for local
# development and can be replaced in deployment configuration.
MODEL_NAME = os.getenv("PROCUREMENT_MODEL", "gpt-5.6-luna")


# Compile the graph once when the API module starts. Compiling the graph does
# not call the LLM; it only creates the workflow that later handles requests.
workflow = build_graph(MODEL_NAME)


app = FastAPI(
    title="Procurement Operations API",
    version="0.1.0",
    description="HTTP access to the procurement LangGraph workflow.",
)


class HealthResponse(BaseModel):
    """Small response returned by the health endpoint."""

    status: str


def _json_default(value: Any) -> Any:
    """Convert Pydantic values into objects that ``json.dumps`` can handle."""

    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")

    # Raising TypeError tells json.dumps that the value is not serializable.
    # This is preferable to silently converting an unknown object to text.
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _sse_event(payload: dict[str, Any]) -> str:
    """Format one Server-Sent Event message.

    SSE messages contain one or more ``data:`` lines and end with a blank line.
    The browser uses that blank line to know that one event is complete.
    """

    return f"data: {json.dumps(payload, default=_json_default)}\n\n"


def _run_stream(request: ProcurementRequest) -> Iterator[str]:
    """Run the graph and yield progress events as the graph advances."""

    # Each request gets its own state object. This prevents two API requests
    # from sharing procurement data with one another.
    initial_state = create_initial_state(request)

    # We keep a lightweight copy of the latest state while processing updates.
    # LangGraph's ``updates`` stream returns only the changes made by each node.
    state_data = initial_state.model_dump()

    yield _sse_event(
        {
            "type": "workflow",
            "status": "started",
            "request_id": initial_state.request_id,
        }
    )

    try:
        # ``stream_mode=\"updates\"`` yields data after each node runs. The
        # result looks like: {"analysis": {"analysis": AnalysisResult(...)}}.
        for update in workflow.stream(initial_state, stream_mode="updates"):
            for node_name, node_update in update.items():
                if isinstance(node_update, BaseModel):
                    node_update = node_update.model_dump()

                if isinstance(node_update, dict):
                    state_data.update(node_update)

                yield _sse_event(
                    {
                        "type": "stage",
                        "stage": node_name,
                        "status": "completed",
                        "update": node_update,
                    }
                )

        # Validate the accumulated state before returning it. This catches
        # malformed node updates at the API boundary instead of returning an
        # invalid final response to the client.
        final_state = ProcurementState.model_validate(state_data)

        yield _sse_event(
            {
                "type": "result",
                "status": "completed",
                "result": final_state,
            }
        )
    except Exception as error:
        # The client receives a structured error event. In production, the
        # detailed exception should be logged server-side rather than exposed.
        yield _sse_event(
            {
                "type": "error",
                "status": "failed",
                "error": str(error),
            }
        )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Confirm that the API process is running."""

    return HealthResponse(status="ok")


@app.post("/api/procure", response_model=ProcurementState)
def procure(request: ProcurementRequest) -> ProcurementState:
    """Run the workflow and return the final state after it completes."""

    initial_state = create_initial_state(request)
    result = workflow.invoke(initial_state)

    # LangGraph normally returns a dictionary of state values. Validating it
    # here gives the API a stable response shape and catches bad node updates.
    return ProcurementState.model_validate(result)


@app.post("/api/procure/stream")
def procure_stream(request: ProcurementRequest) -> StreamingResponse:
    """Run the workflow while streaming stage updates to the caller."""

    return StreamingResponse(
        _run_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # Prevents some reverse proxies from buffering the events.
            "X-Accel-Buffering": "no",
        },
    )
