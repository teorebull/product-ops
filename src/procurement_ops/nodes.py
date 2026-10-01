"""LangGraph agent node implementations."""

from procurement_ops.models import SupervisorDecision
from procurement_ops.state import ProcurementState
from langchain_openai import ChatOpenAI

from procurement_ops.tools import discover_suppliers, fetch_web_page, search_procurement_knowledge
from procurement_ops.models import AnalysisResult, ResearchResult

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

    requirements = state.analysis.requirements
    query = (
        f"{requirements.product} supplier distributor "
        f"{requirements.category} "
        f"{requirements.location or ''} "
        f"{' '.join(requirements.technical_requirements)} "
        f"delivery within {requirements.delivery_deadline_days or ''} days"
    )

    # Find candidate suppliers using the discover_suppliers tool
    candidate_suppliers = discover_suppliers(query=query, max_results=10)
    
    # Once suppliers are found, go through them and see what information can be passed to ther LLM
    suppliers_information = []
    for candidate_supplier in candidate_suppliers["results"]:
        url = candidate_supplier.get("url")
        supplier_info = fetch_web_page(url)
        suppliers_information.append(supplier_info)

    research_llm = ChatOpenAI(model=model_name)
    structured_llm = research_llm.with_structured_output(ResearchResult)

    # Prepare the evidence for the LLM by combining the supplier information    
    page_evidence = "\n\n".join(
        f"URL: {page['url']}\n"
        f"Title: {page['title']}\n"
        f"Content: {page['content'][:8000]}"
        for page in suppliers_information
    )

    # Call LLM to analyze the suppliers and provide a recommendation based on the evidence and supplier information
    messages = [{
                    "role": "system",
                    "content": (
                        "Research suppliers using only the supplied page content. "
                        "Do not invent prices, delivery times, or technical details. "
                        "Use null when information is unavailable."
                    ),
                },
                {
                    "role": "human",
                    "content": (
                        f"Requirements:\n{requirements.model_dump_json()}\n\n"
                        f"Supplier pages:\n{page_evidence}"
                    ),
                },
            ]

    research_result = structured_llm.invoke(messages)
    
    return {"research": research_result}