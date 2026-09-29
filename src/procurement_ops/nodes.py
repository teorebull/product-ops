"""LangGraph agent node implementations."""

from procurement_ops.state import SupervisorDecision, get_current_state
from langchain.openai import ChatOpenAI


def supervisor_node(state, prompt: str) -> SupervisorDecision:
    """Supervisor node implementation."""
    # Implement the logic for the supervisor node here

    current_state = get_current_state(state)

    # Get message history from the current state
    message_history = current_state.get("agent_history", [])
    llm = ChatOpenAI(model="gpt-5.6-luna")

    message_history.append({"role": "user", "content": prompt})

    # Get supervisor's decision based on the current state
    decision_template = llm.with_structured_output(SupervisorDecision)
    decision = decision_template.invoke(messages=message_history)
    

    return {"next_action": decision.next_action, "reason": decision.reason}

    




