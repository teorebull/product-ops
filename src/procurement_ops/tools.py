"""Deterministic procurement tools."""

# import boto3 maybe later
from procurement_ops.models import (
    ProcurementRequirements,
    SupplierCandidate,
)
from procurement_ops.state import ProcurementState
from procurement_ops.models import ProcurementRequirements, SupplierCandidate
from procurement_ops.rag import search_collection

import pymupdf
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool

# Analysis Agent Tools

def calculate_unit_budget(total_budget: float, quantity: int) -> dict:
    """Calculate the maximum available budget per item.
    Used by agent: Analysis Agent"""
    if total_budget < 0:
        raise ValueError("total_budget must be non-negative")
    if quantity <= 0:
        raise ValueError("quantity must be greater than zero")

    return {"max_unit_budget": total_budget / quantity}


def search_procurement_knowledge(query: str, top_k: int = 5) -> dict:
    """Search the procurement knowledge base for relevant information.
    Used by agent: Analysis Agent"""
    results = search_collection("my_collection", query, top_k)
    
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    return {
        "results": [
            {
                "content": document,
                "source": metadata.get("source"),
                "page": metadata.get("page_number"),
                "section": metadata.get("section"),
                "distance": distance,
            }
            for document, metadata, distance in zip(
                documents,
                metadatas,
                distances,
            )
        ]
    }
    
    
# Research Agent Tools
@tool  
def discover_suppliers(query: str, max_results: int = 10) -> dict:
    """Discover potential suppliers based on the procurement requirements.
    Used by agent: Research Agent"""
    # Initialize the searcher with your desired configuration.
    searcher = DDGS(timeout=20)
    results = searcher.text(query, safesearch="moderate", max_results=max_results)
    
    seen_urls = set()
    supplier_candidates = []
    
    for result in results:
        url = result["href"]  

        if url in seen_urls:
            continue
        
        seen_urls.add(url)
        
        supplier_candidates.append({
            "title": result.get("title"),
            "url": url,
            "content": result.get("body")})
    
    return {"results": supplier_candidates}

@tool
def fetch_web_page(url: str) -> dict:
    """Fetch the content of a web page.
    Used by agent: Research Agent"""
    if not url.startswith(("http://", "https://")):
        raise ValueError("Invalid URL provided for supplier research.")

    response = requests.get(url, timeout=10, headers={"User-Agent": "procurement-ops-research/0.1"})
    response.raise_for_status()
    
    # Create a BeautifulSoup object to parse the HTML content
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Remove unwanted tags to clean up the content
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
        
    # Extract the main content text
    content = soup.get_text(separator=" ", strip=True)
    
    return {
        "url": url,
        "title": soup.title.string if soup.title else "No Title Found",
        "content": content,
    }
    
# Recommendation agent

def evaluate_supplier_candidates(
    requirements: ProcurementRequirements,
    candidates: list[SupplierCandidate],
) -> dict:
    """Evaluate supplier candidates against the procurement requirements.
    Used by agent: Recommendation Agent"""
    evaluations = []

    for candidate in candidates:
        reasons = []

        if (
            candidate.estimated_price_eur is None
            or requirements.budget_eur is None
        ):
            within_budget = None
            reasons.append("Budget comparison is unavailable.")
        elif candidate.estimated_price_eur <= requirements.budget_eur:
            within_budget = True
            reasons.append("Estimated price is within budget.")
        else:
            within_budget = False
            reasons.append("Estimated price exceeds the available budget.")

        if (
            candidate.delivery_days is None
            or requirements.delivery_deadline_days is None
        ):
            meets_deadline = None
            reasons.append("Delivery deadline comparison is unavailable.")
        elif candidate.delivery_days <= requirements.delivery_deadline_days:
            meets_deadline = True
            reasons.append("Delivery time meets the required deadline.")
        else:
            meets_deadline = False
            reasons.append("Delivery time exceeds the required deadline.")

        if within_budget is False or meets_deadline is False:
            eligible = False
        elif within_budget is True and meets_deadline is True:
            eligible = True
        else:
            eligible = None

        evaluations.append({
            "supplier": candidate.supplier,
            "within_budget": within_budget,
            "meets_deadline": meets_deadline,
            "eligible": eligible,
            "reasons": reasons,
        })

    return {"evaluations": evaluations}