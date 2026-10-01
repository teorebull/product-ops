"""Deterministic procurement tools."""

# import boto3 maybe later
from procurement_ops.models import (
    ProcurementRequirements,
    SupplierCandidate,
)
from procurement_ops.state import ProcurementState
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