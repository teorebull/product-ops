from langchain.agents import create_agent
from procurement_ops.tools import discover_suppliers, fetch_web_page
from procurement_ops.models import ResearchResult

RESEARCH_SYSTEM_PROMPT = """
You are a procurement supplier research agent.

Given procurement requirements:

1. Call discover_suppliers to find potential supplier pages.
2. Review the discovered results.
3. Select the most relevant supplier URLs.
4. Call fetch_web_page for promising URLs.
5. Compare the page content against the procurement requirements.
6. Return only suppliers supported by the fetched evidence.
7. Do not invent prices, delivery times, technical specifications, or supplier details.
8. Use null when information is unavailable.
9. Include the source URL for every supplier candidate.
"""


def create_research_agent(model_name: str = "gpt-5.6-luna"):
    """Create a research agent that discovers potential suppliers based on procurement requirements."""
    return create_agent(
    model=model_name,
    tools=[discover_suppliers, fetch_web_page],
    system_prompt=RESEARCH_SYSTEM_PROMPT,
    response_format=ResearchResult
    )
    
