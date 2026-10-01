"""LangGraph agent node implementations."""

from procurement_ops.models import SupervisorDecision
from procurement_ops.state import ProcurementState
from langchain_openai import ChatOpenAI

from procurement_ops.tools import discover_suppliers, fetch_web_page, search_procurement_knowledge
from procurement_ops.models import AnalysisResult, ResearchResult
from procurement_ops.agents import create_research_agent

def supervisor_node(state: ProcurementState, prompt: str) -> dict:
    """Supervisor node implementation."""

    pass

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