"""LangGraph agent node implementations."""

from procurement_ops.models import RecommendationResult, SupervisorDecision
from procurement_ops.state import ProcurementState
from langchain_openai import ChatOpenAI

from procurement_ops.tools import discover_suppliers, evaluate_supplier_candidates, fetch_web_page, search_procurement_knowledge
from procurement_ops.models import AnalysisResult, ResearchResult
from procurement_ops.agents import create_research_agent

from procurement_ops.models import SupervisorDecision
from procurement_ops.state import ProcurementState


def supervisor_node(state: ProcurementState) -> dict:
    """Route the workflow based on completed state."""

    if state.analysis is None:
        action = "procurement_analysis"

    else:
        requirements = state.analysis.requirements
        missing_required_information = []

        if not requirements.product.strip():
            missing_required_information.append("product")

        if requirements.quantity is None:
            missing_required_information.append("quantity")

        if missing_required_information:
            return {
                "next_action": "needs_information",
                "status": "WAITING_FOR_INFORMATION",
            }

        if state.research is None:
            action = "supplier_research"

        elif state.recommendation is None:
            action = "recommendation"

        else:
            action = "complete"
    
    decision = SupervisorDecision(next_action=action)

    status = (
        "COMPLETED"
        if decision.next_action == "complete"
        else "IN_PROGRESS"
    )

    return {
        "next_action": decision.next_action,
        "status": status,
    }

def analysis_node(state: ProcurementState, model_name: str) -> dict:
    analysis_llm = ChatOpenAI(model=model_name)
    request = state.original_request
    query = (
        f"Procurement guidance for {request.item}. "
        f"Requirements: {request.requirements}. "
        f"Location: {request.location}. "
        f"Delivery deadline: {request.delivery_deadline_days} days."
    )
    
    evidence = search_procurement_knowledge(query)
    structured_llm = analysis_llm.with_structured_output(AnalysisResult)
    
    messages = [
                {"role": "system", "content": "Analyze the procurement request using only the provided evidence. "
                    "Identify requirements and missing information. Do not invent policies."},
                {"role": "human", "content": f"Request: {request.model_dump_json()}\n"
                    f"Retrieved evidence: {evidence}"},
            ]
    analysis_result = structured_llm.invoke(messages)
    
    return {"analysis": analysis_result}

def research_node(state: ProcurementState, model_name: str) -> dict:
    if state.analysis is None:
        raise ValueError("Analysis is required before supplier research.")
    
    agent = create_research_agent(model_name)
    
    result = agent.invoke({
        "messages": [{"role": "user", 
                     "content": "Research suppliers for these requirements:\n"
                    f"{state.analysis.requirements.model_dump_json()}"}]
    })
    
    return {"research": result["structured_response"]}

def recommendation_node(state: ProcurementState, model_name: str) -> dict:
    if state.analysis is None:
        raise ValueError("Analysis is required before making a recommendation.")
    if state.research is None:
        raise ValueError("Research is required before making a recommendation.")
    
    requirements = state.analysis.requirements
    candidates = state.research.supplier_candidates
    
    evaluations = evaluate_supplier_candidates(requirements, candidates)
    
    messages = [
        {"role": "system", 
         "content": ( 
             "Create a procurement recommendation using only the supplied "
             "analysis, supplier research, and evaluations. "
             "Do not invent supplier facts. "
             "Mention uncertainty when information is missing.")
         },
        {"role": "user", "content": (
                f"Analysis:\n{state.analysis.model_dump_json()}\n\n"
                f"Research:\n{state.research.model_dump_json()}\n\n"
                f"Evaluations:\n{evaluations}"
                )
        }
    ]
    
    recommendation_llm = ChatOpenAI(model=model_name)
    structured_llm = recommendation_llm.with_structured_output(RecommendationResult)
    
    response = structured_llm.invoke(messages)
    
    return {"recommendation": response}