"""LangGraph agent node implementations."""

from procurement_ops.models import SupervisorDecision
from procurement_ops.state import ProcurementState
from langchain_openai import ChatOpenAI

def procurement_analysis_node(state: ProcurementState) -> dict:
    requirements = state.requirements
    missing_information = state.missing_information

    return {
        "requirements": requirements,
        "missing_information": missing_information,
    }


def supervisor_node(state: ProcurementState, prompt: str) -> dict:
    """Supervisor node implementation."""

    current_state = state.model_dump()

    # Get message history from the current state
    message_history = current_state.get("agent_history", [])
    llm = ChatOpenAI(model="gpt-5.6-luna")

    message_history.append({"role": "user", "content": prompt})

    # Get supervisor's decision based on the current state
    decision_template = llm.with_structured_output(SupervisorDecision)
    decision = decision_template.invoke(message_history)

    return {"next_action": decision.next_action}
