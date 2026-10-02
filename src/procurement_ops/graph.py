"""LangGraph construction and execution entry points."""

from langgraph.graph import START, END, StateGraph

from procurement_ops.nodes import analysis_node, recommendation_node, supervisor_node, research_node
from procurement_ops.state import ProcurementState

def build_graph():
    g = StateGraph(ProcurementState)

    g.add_node("supervisor", supervisor_node)
    g.add_node("analysis", analysis_node)
    g.add_node("research", research_node)
    g.add_node("recommendation", recommendation_node)

    g.add_edge(START, "supervisor")
    g.add_conditional_edges("supervisor", lambda state: state.next_action,
                                {
                                    "procurement_analysis": "analysis",
                                    "supplier_research": "research",
                                    "recommendation": "recommendation",
                                    "complete": END,
                                    "needs_information": END
                                })

    g.add_edge("analysis", "supervisor")
    g.add_edge("research", "supervisor")
    g.add_edge("recommendation", "supervisor")

    graph = g.compile()
    
    return graph