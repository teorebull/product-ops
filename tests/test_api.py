from fastapi.testclient import TestClient

from procurement_ops import api
from procurement_ops.models import (
    AnalysisResult,
    ProcurementRequest,
    ProcurementRequirements,
    RecommendationResult,
    ResearchResult,
    SupplierCandidate,
)
from procurement_ops.state import ProcurementState


class FakeWorkflow:
    """Small fake graph used to test the HTTP layer without real agents."""

    def __init__(self, final_state: ProcurementState):
        self.final_state = final_state

    def invoke(self, state: ProcurementState) -> dict:
        """Return a final state just like a compiled LangGraph would."""

        assert state.original_request.item == "Business laptops"
        return self.final_state.model_dump()

    def stream(self, state: ProcurementState, stream_mode: str):
        """Yield representative node updates for the streaming endpoint."""

        assert stream_mode == "updates"
        yield {"supervisor": {"next_action": "procurement_analysis"}}
        yield {"analysis": {"analysis": self.final_state.analysis}}
        yield {"research": {"research": self.final_state.research}}
        yield {
            "recommendation": {
                "recommendation": self.final_state.recommendation
            }
        }
        yield {"supervisor": {"next_action": "complete", "status": "COMPLETED"}}


def make_final_state() -> ProcurementState:
    """Create a valid final state for API response tests."""

    return ProcurementState(
        request_id="REQ-001",
        original_request=ProcurementRequest(
            requester="IT",
            item="Business laptops",
            quantity=40,
        ),
        analysis=AnalysisResult(
            requirements=ProcurementRequirements(
                category="IT hardware",
                product="Business laptops",
                quantity=40,
            )
        ),
        research=ResearchResult(
            supplier_candidates=[
                SupplierCandidate(supplier="Example Supplier")
            ]
        ),
        recommendation=RecommendationResult(
            summary="Summary",
            recommendation="Proceed with review.",
            recommended_supplier="Example Supplier",
        ),
        next_action="complete",
        status="COMPLETED",
    )


def test_health_endpoint() -> None:
    client = TestClient(api.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_procure_endpoint_returns_final_state(monkeypatch) -> None:
    monkeypatch.setattr(api, "workflow", FakeWorkflow(make_final_state()))
    client = TestClient(api.app)

    response = client.post(
        "/api/procure",
        json={
            "requester": "IT",
            "item": "Business laptops",
            "quantity": 40,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"
    assert response.json()["recommendation"]["recommended_supplier"] == (
        "Example Supplier"
    )


def test_stream_endpoint_returns_workflow_events(monkeypatch) -> None:
    monkeypatch.setattr(api, "workflow", FakeWorkflow(make_final_state()))
    client = TestClient(api.app)

    response = client.post(
        "/api/procure/stream",
        json={
            "requester": "IT",
            "item": "Business laptops",
            "quantity": 40,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert '"stage": "analysis"' in response.text
    assert '"stage": "research"' in response.text
    assert '"stage": "recommendation"' in response.text
    assert '"type": "result"' in response.text
