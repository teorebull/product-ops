"""LangGraph construction and execution entry points."""

from functools import partial

from langgraph.graph import END, START, StateGraph

from procurement_ops.nodes import (
    analysis_node,
    recommendation_node,
    research_node,
    supervisor_node,
)
from procurement_ops.state import ProcurementState


def build_graph(model_name: str):
    """Build the procurement workflow for the selected chat model."""

    workflow = StateGraph(ProcurementState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node(
        "analysis",
        partial(analysis_node, model_name=model_name),
    )
    workflow.add_node(
        "research",
        partial(research_node, model_name=model_name),
    )
    workflow.add_node(
        "recommendation",
        partial(recommendation_node, model_name=model_name),
    )

    workflow.add_edge(START, "supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state.next_action,
        {
            "procurement_analysis": "analysis",
            "supplier_research": "research",
            "recommendation": "recommendation",
            "complete": END,
            "needs_information": END,
        },
    )

    workflow.add_edge("analysis", "supervisor")
    workflow.add_edge("research", "supervisor")
    workflow.add_edge("recommendation", "supervisor")

    return workflow.compile()
