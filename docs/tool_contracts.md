# Tool Contracts

This document defines the tools available to each agent in V1.

The system uses **four genuine agents**:

* Supervisor Agent
* Procurement Analysis Agent
* Supplier Research Agent
* Evaluation & Risk Agent

Deterministic operations such as calculations, threshold checks, API requests, and vector search are implemented as **tools or workflow functions**, not as agents.

---

# 1. Supervisor Agent

## Purpose

Coordinate the complete procurement investigation.

The Supervisor reads the shared state and decides:

* which specialist agent should run next
* whether an agent should be called again
* whether enough evidence exists
* whether the workflow should stop
* whether human input is required

The Supervisor does not perform detailed procurement research itself.

## Available Tools

### `get_workflow_state`

Returns a summarized view of the current procurement investigation.

#### Output

```python
{
    "requirements_complete": bool,
    "policy_analysis_complete": bool,
    "supplier_research_complete": bool,
    "evaluation_complete": bool,
    "risk_assessment_complete": bool,
    "missing_information": list[str],
    "status": str
}
```

---

### `check_investigation_sufficiency`

Checks whether enough information exists to produce a reliable recommendation.

#### Input

```python
{
    "requirements": ProcurementRequirements | None,
    "applicable_policies": list[str],
    "supplier_candidates": list,
    "supplier_evaluations": list,
    "risks": list,
    "missing_information": list[str]
}
```

#### Output

```python
{
    "sufficient": bool,
    "missing_information": list[str],
    "reason": str
}
```

This may be implemented using structured model reasoning or Jev.

The Supervisor uses the result to determine whether to:

```text
continue investigation
repeat supplier research
repeat procurement analysis
proceed to final recommendation
request human input
```

---

# 2. Procurement Analysis Agent

## Purpose

Understand the purchase request and determine which procurement rules, criteria, and guidance are relevant.

This agent combines:

* request interpretation
* procurement policy research
* RAG
* evaluation-criteria discovery

It should reason about what information is relevant rather than performing a fixed set of searches.

---

## Available Tools

### `calculate_unit_budget`

Calculates the maximum available budget per item.

#### Input

```python
{
    "total_budget": float,
    "quantity": int
}
```

#### Output

```python
{
    "max_unit_budget": float
}
```

Deterministic Python operation.

---

### `search_procurement_knowledge`

Searches the procurement RAG knowledge base.

#### Input

```python
{
    "query": str,
    "top_k": int
}
```

#### Output

```python
{
    "results": [
        {
            "content": str,
            "source": str,
            "section": str | None,
            "score": float
        }
    ]
}
```

Possible sources include:

* EU procurement legislation
* World Bank Procurement Regulations
* Value for Money guidance
* Evaluating Bids and Proposals guidance
* Green Public Procurement criteria
* procurement case studies

---

### `retrieve_procurement_source`

Retrieves additional context from a source already identified through RAG.

#### Input

```python
{
    "source_id": str,
    "section": str | None
}
```

#### Output

```python
{
    "source": str,
    "content": str,
    "metadata": dict
}
```

This allows the agent to investigate a source in more depth instead of relying only on small retrieved chunks.

---

## Expected Agent Output

```python
{
    "requirements": ProcurementRequirements,

    "missing_information": list[str],

    "applicable_policies": list[str],

    "evaluation_criteria": [
        {
            "name": str,
            "weight": float,
            "description": str | None
        }
    ],

    "evidence": list[dict]
}
```

---

# 3. Supplier Research Agent

## Purpose

Investigate the supplier market and find evidence relevant to the purchase request.

This agent decides:

* what supplier information is required
* what historical tenders should be searched
* whether more searches are necessary
* whether a candidate has enough evidence to be evaluated

The agent may run multiple searches during a single workflow.

---

## Available Tools

### `search_tenders`

Searches TED for relevant procurement notices.

#### Input

```python
{
    "keywords": list[str],
    "country": str | None,
    "cpv_code": str | None,
    "date_from": str | None,
    "date_to": str | None,
    "limit": int
}
```

#### Output

```python
{
    "tenders": [
        {
            "notice_id": str,
            "title": str,
            "buyer": str | None,
            "country": str | None,
            "estimated_value": float | None,
            "awarded_value": float | None,
            "supplier": str | None,
            "publication_date": str | None,
            "source_url": str
        }
    ]
}
```

---

### `get_tender_details`

Retrieves detailed information about a specific tender.

#### Input

```python
{
    "notice_id": str
}
```

#### Output

```python
{
    "notice_id": str,
    "description": str | None,
    "technical_requirements": list[str],
    "award_criteria": list,
    "supplier": str | None,
    "contract_value": float | None,
    "source_url": str
}
```

---

### `search_supplier_information`

Retrieves public information about a supplier.

#### Input

```python
{
    "supplier_name": str,
    "country": str | None
}
```

#### Output

```python
{
    "supplier": str,
    "company_information": dict,
    "evidence": list,
    "sources": list[str]
}
```

V1 may initially provide limited supplier intelligence depending on available public APIs.

---

### `search_additional_supplier_candidates`

Runs another supplier/tender search when existing evidence is insufficient.

#### Input

```python
{
    "requirements": ProcurementRequirements,
    "existing_suppliers": list[str],
    "reason_for_additional_search": str
}
```

#### Output

```python
{
    "new_candidates": list[dict]
}
```

This can internally reuse TED and supplier-search functionality.

---

## Expected Agent Output

```python
{
    "supplier_candidates": [
        {
            "supplier": str,
            "pricing_evidence": dict | None,
            "delivery_evidence": dict | None,
            "technical_evidence": dict | None,
            "historical_contracts": list,
            "sources": list[str]
        }
    ],

    "historical_tenders": list,

    "missing_information": list[str],
    "evidence": list[dict],
    "research_completed": bool
}
```

---

# 4. Evaluation & Risk Agent

## Purpose

Evaluate supplier candidates and determine whether the procurement recommendation is sufficiently supported and safe to proceed.

This agent combines:

* supplier comparison
* compliance analysis
* weighted evaluation
* uncertainty assessment
* procurement risk
* approval requirements

It may request further research through the Supervisor.

---

## Available Tools

### `evaluate_requirement_compliance`

Checks a candidate against procurement requirements.

#### Input

```python
{
    "requirements": dict,
    "supplier_evidence": dict
}
```

#### Output

```python
{
    "requirements": [
        {
            "requirement": str,
            "status": "PASS | FAIL | UNKNOWN",
            "evidence": str | None
        }
    ],
    "overall_status": "PASS | FAIL | INCOMPLETE"
}
```

Important:

```text
UNKNOWN != FAIL
```

Missing evidence should remain explicit.

---

### `calculate_weighted_score`

Calculates a deterministic weighted score.

#### Input

```python
{
    "criteria": list[EvaluationCriterion],
    "scores": dict[str, float]
}
```

#### Output

```python
{
    "total_score": float,
    "weighted_scores": dict
}
```

Example:

```text
Price               35%
Technical fit       30%
Delivery            15%
Warranty            10%
Sustainability      10%
```

The LLM must not perform the arithmetic itself.

Scores use a 0-100 scale. Criterion weights use a 0-1 scale and must sum
to 1.0. Every criterion must have exactly one score.

---

### `check_approval_rules`

Applies explicit procurement approval rules.

#### Input

```python
{
    "purchase_value": float,
    "supplier_count": int,
    "missing_information": list[str],
    "risk_level": str | None
}
```

#### Output

```python
{
    "approval_required": bool,
    "approval_type": str | None,
    "reasons": list[str]
}
```

Example deterministic rules:

```text
purchase value exceeds a configured threshold
only one viable supplier exists
supplier risk is high
```

The rule for critical missing information is intentionally deferred. The
workflow currently routes missing request information to NEEDS_INFORMATION;
it does not infer approval from an arbitrary missing-information string.

Thresholds and approval-type mappings must be configuration values rather
than prompt instructions. This tool remains deferred until those values are
defined.

---

### `assess_procurement_risk`

Uses Jev to make a structured risk decision based on the accumulated evidence.

#### Input

```python
{
    "request": ProcurementRequest,
    "supplier_evaluations": list[EvaluationResult],
    "applicable_policies": list[str],
    "missing_information": list[str]
}
```

#### Output

```python
{
    "risk_level": "LOW | MEDIUM | HIGH",
    "confidence": float,
    "risk_factors": list[str]
}
```

Jev provides the structured decision.

The supporting factual evidence remains stored separately.

---

## Expected Agent Output

```python
{
    "supplier_evaluations": list[EvaluationResult],
    "risks": list[RiskApprovalResult],
    "approval_required": bool | None
}
```

---

# 5. Finalization Workflow

Finalization is **not an agent** in V1.

Once the Supervisor determines that the investigation is complete, a workflow step builds the final response from the shared state.

## `build_final_recommendation`

### Input

```python
{
    "procurement_state": ProcurementState
}
```

### Output

```python
{
    "request_id": str,

    "status": (
        "READY_TO_PROCEED"
        "HUMAN_REVIEW_REQUIRED"
        "NEEDS_INFORMATION"
    ),

    "summary": str,

    "requirements": ProcurementRequirements,

    "suppliers_considered": list[SupplierCandidate],

    "recommended_option": dict | None,

    "evaluation": list[EvaluationResult],

    "risk": RiskApprovalResult,

    "approval": dict,

    "evidence": list[str],

    "unresolved_questions": list[str],

    "recommendation": str
}
```

The output should clearly distinguish:

* retrieved facts
* deterministic calculations
* AI-generated analysis
* unresolved uncertainty

---

# 6. Multi-Agent Interaction

Agents do not normally invoke one another directly.

They return results to the shared state.

The Supervisor then decides what happens next.

```text
Supervisor
    ↓
Procurement Analysis Agent
    ↓
Shared State
    ↓
Supervisor
    ↓
Supplier Research Agent
    ↓
Shared State
    ↓
Supervisor
    ↓
Evaluation & Risk Agent
    ↓
Shared State
    ↓
Supervisor
```

A workflow can revisit an earlier agent.

Example:

```text
Supplier Research Agent
        ↓
Evaluation & Risk Agent
        ↓
"Insufficient pricing evidence"
        ↓
Supervisor
        ↓
Supplier Research Agent
        ↓
new evidence
        ↓
Evaluation & Risk Agent
```

This iterative behavior is a core part of the agentic workflow.

---

# 7. Agent / Tool Map

| Agent                      | Tools                                                                                                            |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Supervisor Agent           | `get_workflow_state`, `check_investigation_sufficiency`                                                          |
| Procurement Analysis Agent | `calculate_unit_budget`, `search_procurement_knowledge`, `retrieve_procurement_source`                           |
| Supplier Research Agent    | `search_tenders`, `get_tender_details`, `search_supplier_information`, `search_additional_supplier_candidates`   |
| Evaluation & Risk Agent    | `evaluate_requirement_compliance`, `calculate_weighted_score`, `assess_procurement_risk`, `check_approval_rules` |
| Finalization workflow      | `build_final_recommendation`                                                                                     |

---

# 8. Tool Design Principles

## Agents reason; tools execute

Agents determine what needs to happen.

Tools perform bounded operations.

---

## Deterministic logic stays outside the LLM

Use Python for:

* calculations
* thresholds
* validation
* scoring formulas
* state transformations

---

## External information must preserve provenance

RAG, TED, and supplier-data tools must return source information with their results.

---

## Tools use structured schemas

Inputs and outputs should use Pydantic models wherever practical.

---

## Errors must be explicit

Example:

```python
{
    "success": False,
    "error": "TED_API_UNAVAILABLE",
    "message": "Unable to query TED."
}
```

An agent should never fabricate a result because a tool failed.

---

## No consequential actions in V1

Tools may:

* search
* retrieve
* calculate
* evaluate
* classify

Tools may not:

* place purchase orders
* transfer money
* contact suppliers
* sign contracts
* approve purchases

---

# 9. Initial Implementation Order

Build tools only as they become necessary.

Recommended order:

```text
1. calculate_unit_budget

2. search_procurement_knowledge
3. retrieve_procurement_source

4. search_tenders
5. get_tender_details

6. evaluate_requirement_compliance
7. calculate_weighted_score

8. assess_procurement_risk
9. check_approval_rules

10. check_investigation_sufficiency

11. build_final_recommendation
```

`search_supplier_information` and broader supplier intelligence can be added once the core procurement flow works.
