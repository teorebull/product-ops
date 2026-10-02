# Tool Contracts

This document describes the tools and structured boundaries in the current MVP. The workflow intentionally adds capabilities incrementally rather than implementing every planned procurement integration at once.

## Workflow

```text
START
  -> supervisor_node
  -> analysis_node
  -> supervisor_node
  -> research_node
  -> supervisor_node
  -> recommendation_node
  -> supervisor_node
  -> END
```

All nodes communicate through `ProcurementState`. Specialist nodes return state updates; they do not call other specialist nodes directly.

## Supervisor

### Role

The Supervisor is deterministic routing logic, not an LLM agent. It checks which result is missing and sets `next_action`.

### Actions

```text
procurement_analysis
supplier_research
recommendation
needs_information
complete
```

### Routing Rules

```text
analysis is missing       -> procurement_analysis
required input is missing -> needs_information
research is missing       -> supplier_research
recommendation is missing -> recommendation
all results exist         -> complete
```

`needs_information` ends or pauses the workflow. The caller can ask the requester for the values listed in the analysis result and resume with an updated request.

The Supervisor does not search, calculate, evaluate suppliers, or generate recommendations.

## Procurement Analysis

### Role

`analysis_node` interprets the original request and retrieves relevant procurement guidance from the local RAG collection. It uses a structured LLM response because the output must conform to `AnalysisResult`.

### Input

```python
ProcurementState.original_request: ProcurementRequest
```

### Tool

#### `search_procurement_knowledge`

Searches the Chroma procurement knowledge collection.

```python
search_procurement_knowledge(query: str, top_k: int = 5) -> dict
```

Output:

```python
{
    "results": [
        {
            "content": str,
            "source": str | None,
            "page": int | None,
            "section": str | None,
            "distance": float,
        }
    ]
}
```

The evidence source and metadata are retained so the model can distinguish retrieved facts from generated interpretation.

### Output

```python
AnalysisResult(
    requirements=ProcurementRequirements(...),
    missing_information=list[str],
    applicable_policies=list[str],
    evidence=list[dict],
)
```

`calculate_unit_budget` is available as a deterministic helper for future analysis enhancements. It is not required for the current analysis node path.

## Supplier Research

### Role

`research_node` invokes the LangChain Supplier Research Agent. This is the one intentionally autonomous specialist because it must decide which search results deserve deeper investigation.

### Agent Tools

#### `discover_suppliers`

Uses DuckDuckGo to discover possible supplier pages.

```python
```

Output:

```python
{
    "results": [
        {
            "title": str | None,
            "url": str,
            "content": str | None,
        }
    ]
}
```

These are search results, not verified suppliers.

#### `fetch_web_page`

Fetches and cleans one selected supplier page.

```python
fetch_web_page(url: str) -> dict
```

Output:

```python
{
    "url": str,
    "title": str,
    "content": str,
}
```

The tool removes common non-content HTML elements. It does not decide whether a supplier matches the request; the Research Agent compares the page evidence with the requirements.

### Output

```python
ResearchResult(
    supplier_candidates=list[SupplierCandidate],
    historical_tenders=list[dict],
    evidence=list[dict],
)
```

The current supplier candidate contract is intentionally small:

```python
SupplierCandidate(
    supplier=str,
    estimated_price_eur=float | None,
    delivery_days=int | None,
    source=str | None,
)
```

The agent must use `None` when a page does not provide a value. It must not infer unsupported prices, delivery times, or technical details.

## Recommendation

### Role

`recommendation_node` combines analysis and research, performs deterministic constraint evaluation, and asks a structured LLM to write the final recommendation.

### Helper

#### `evaluate_supplier_candidates`

Compares each candidate with budget and delivery requirements.

```python
    requirements: ProcurementRequirements,
    candidates: list[SupplierCandidate],
) -> dict
```

Output:

```python
{
    "evaluations": [
        {
            "supplier": str,
            "within_budget": bool | None,
            "meets_deadline": bool | None,
            "eligible": bool | None,
            "reasons": list[str],
        }
    ]
}
```

Python performs these comparisons because deterministic calculations should not be delegated to the LLM. `None` means that the evidence needed for the comparison is unavailable.

### Output

```python
RecommendationResult(
    summary=str,
    recommendation=str,
    recommended_supplier=str | None,
    risks=list[str],
    uncertainties=list[str],
)
```

The LLM summarizes the evidence and uncertainty. It does not invent missing supplier facts or replace deterministic evaluations.

## Error and Evidence Principles

- External tools may fail; callers should preserve or surface the failure rather than fabricate data.
- Search snippets are discovery evidence, not verified supplier facts.
- Every supplier candidate retains a source URL where available.
- Unknown is different from false. Missing price or delivery data remains `None`.
- Tools perform bounded retrieval and calculations; agents interpret results.

## Deferred Work

The following are intentionally outside the current MVP:

- TED search and tender-detail tools.
- Supplier databases and company intelligence APIs.
- Weighted evaluation criteria.
- Dedicated risk and approval agents.
- Human-in-the-loop persistence and resume flows.
- Automatic purchasing actions.
