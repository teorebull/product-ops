# V1 Workflow

## 1. Objective

V1 focuses on **internal IT hardware procurement requests**.

The system receives a purchase request, investigates the relevant procurement rules and supplier options, evaluates the available evidence, and produces a structured recommendation.

The system does **not** autonomously place orders or approve high-impact purchases.

---

# 2. Example Input

```json
{
  "requester": "IT Department",
  "item": "Business laptops",
  "quantity": 40,
  "budget_eur": 45000,
  "location": "Barcelona, Spain",
  "delivery_deadline_days": 21,
  "requirements": [
    "16 GB RAM minimum",
    "3-year warranty",
    "business-grade device"
  ]
}
```

Not every request must contain all fields.

The Requirements Agent is responsible for extracting available information and identifying anything important that is missing.

---

# 3. Shared Procurement State

All agents operate on a shared LangGraph state.

Conceptually:

```python
ProcurementState = {
    "request_id": str,
    "original_request": dict,

    "requirements": {},
    "missing_information": [],

    "applicable_policies": [],
    "evaluation_criteria": [],

    "supplier_candidates": [],
    "historical_tenders": [],

    "supplier_evaluations": [],
    "risks": [],

    "approval_required": bool | None,
    "approval_reason": str | None,

    "evidence": [],
    "agent_history": [],

    "next_action": str | None,
    "status": str,

    "final_recommendation": {}
}
```

The shared state allows different agents to collaborate during the same procurement run.

---

# 4. Agents

## Procurement Supervisor

The Supervisor coordinates the workflow.

Responsibilities:

* inspect the current state
* decide which agent should run next
* determine whether additional investigation is required
* avoid unnecessary agent calls
* determine when enough evidence has been gathered
* trigger the final recommendation

The Supervisor does not perform specialist procurement analysis itself.

---

## Requirements Agent

Purpose:

Convert the original purchase request into structured procurement requirements.

Responsibilities:

* extract product or service requirements
* extract quantity
* extract budget
* extract location
* extract delivery constraints
* extract technical requirements
* identify missing information

Example output:

```json
{
  "category": "IT hardware",
  "product": "business laptop",
  "quantity": 40,
  "budget_eur": 45000,
  "max_unit_price_eur": 1125,
  "delivery_deadline_days": 21,
  "requirements": [
    "16 GB RAM minimum",
    "3-year warranty"
  ],
  "missing_information": []
}
```

---

## Policy Agent

Purpose:

Determine which procurement guidance and evaluation criteria are relevant.

Primary source:

* RAG knowledge base

Responsibilities:

* retrieve relevant procurement guidance
* retrieve applicable evaluation principles
* identify sustainability criteria
* identify value-for-money considerations
* provide evidence and citations

The Policy Agent should not invent procurement rules that are not supported by the knowledge base.

---

## Supplier Research Agent

Purpose:

Find realistic supplier and market information.

Possible tools:

* TED API
* supplier/company APIs
* historical procurement search
* external supplier data sources

Responsibilities:

* search comparable procurements
* identify potential suppliers
* gather available pricing or contract information
* gather delivery or capability information where available
* return evidence supporting each candidate

The agent may be called more than once if the available supplier evidence is insufficient.

---

## Evaluation Agent

Purpose:

Compare supplier candidates against the procurement requirements and evaluation criteria.

Responsibilities:

* compare price
* compare compliance with requirements
* compare non-price factors
* identify advantages and disadvantages
* identify insufficient evidence
* rank or score options when appropriate

The Evaluation Agent may determine that more supplier research is required.

In that case, the Supervisor can route the workflow back to the Supplier Research Agent.

---

## Risk & Approval Agent

Purpose:

Determine whether the procurement request contains important risks or requires human review.

Inputs may include:

* purchase value
* supplier evidence
* policy findings
* uncertainty
* missing information
* evaluation results

The agent uses:

* Jev structured decisions
* deterministic Python business rules

Possible outputs:

```json
{
  "risk_level": "MEDIUM",
  "approval_required": true,
  "approval_type": "PROCUREMENT_REVIEW",
  "reason": "Purchase value exceeds configured approval threshold."
}
```

Human approval rules remain explicit and deterministic where possible.

---

# 5. Workflow

The default workflow is:

```text
Purchase Request
      ↓
Requirements Agent
      ↓
Supervisor
      ↓
Policy Agent
      ↓
Supervisor
      ↓
Supplier Research Agent
      ↓
Supervisor
      ↓
Evaluation Agent
      ↓
Supervisor
      ↓
Risk & Approval Agent
      ↓
Supervisor
      ↓
Final Recommendation
```

This is not a fixed pipeline.

The Supervisor may skip, repeat, or revisit agents depending on the current state.

Example:

```text
Supplier Research
      ↓
Evaluation
      ↓
Insufficient supplier evidence
      ↓
Supervisor
      ↓
Supplier Research
      ↓
Evaluation
```

---

# 6. Routing Logic

The Supervisor should base routing on the current state.

Initial rules:

### Missing requirements

If essential purchase information is missing:

```text
Requirements Agent
→ mark request as NEEDS_INFORMATION
→ stop investigation
```

### Procurement guidance missing

If no relevant policy or evaluation guidance has been retrieved:

```text
→ Policy Agent
```

### No supplier evidence

If no viable supplier candidates exist:

```text
→ Supplier Research Agent
```

### Suppliers not evaluated

If supplier candidates exist but no comparison has been completed:

```text
→ Evaluation Agent
```

### Evaluation identifies missing evidence

If the Evaluation Agent determines that evidence is insufficient:

```text
→ Supplier Research Agent
```

### Risk not assessed

Once sufficient evidence exists:

```text
→ Risk & Approval Agent
```

### Enough evidence

When requirements, policy context, supplier evidence, evaluation, and risk assessment are available:

```text
→ Final Recommendation
```

---

# 7. Human-in-the-Loop

The V1 system can produce three broad outcomes.

## Ready to Proceed

The system has enough evidence and no configured approval condition has been triggered.

```text
status = READY_TO_PROCEED
```

## Human Review Required

The analysis is complete but the request requires review.

Possible reasons:

* high purchase value
* elevated supplier risk
* unusual procurement conditions
* conflicting evidence
* low decision confidence

```text
status = HUMAN_REVIEW_REQUIRED
```

## More Information Required

The system cannot produce a reliable analysis because important information is missing.

```text
status = NEEDS_INFORMATION
```

---

# 8. Final Output

The final output should be structured and auditable.

Example:

```json
{
  "request_id": "REQ-001",
  "status": "HUMAN_REVIEW_REQUIRED",

  "summary": "Purchase of 40 business laptops for the Barcelona office.",

  "requirements": {
    "quantity": 40,
    "budget_eur": 45000,
    "delivery_deadline_days": 21
  },

  "recommended_supplier": {
    "name": "Example Supplier",
    "estimated_cost_eur": 42000
  },

  "alternatives_considered": 4,

  "evaluation": {
    "price": "compliant",
    "delivery": "compliant",
    "technical_requirements": "compliant",
    "sustainability": "partially verified"
  },

  "risk_level": "MEDIUM",

  "approval": {
    "required": true,
    "type": "PROCUREMENT_REVIEW",
    "reason": "Purchase value exceeds configured threshold."
  },

  "evidence": [
    {
      "source": "EU procurement guidance",
      "reference": "..."
    },
    {
      "source": "TED procurement notice",
      "reference": "..."
    }
  ],

  "recommendation": "Proceed with Supplier A subject to procurement review."
}
```

---

# 9. V1 Boundaries

V1 will support:

* IT hardware procurement
* one procurement request per run
* multiple collaborating agents
* RAG over official procurement material
* public procurement data
* supplier comparison
* risk assessment
* human escalation
* structured recommendations

V1 will not support:

* automatic purchases
* payment execution
* contract signing
* unrestricted web browsing
* fully autonomous approval
* every procurement category
* supplier negotiation

---

# 10. Success Criteria

V1 is successful when the system can:

1. interpret a realistic IT procurement request
2. retrieve relevant procurement guidance
3. find relevant supplier or historical tender information
4. evaluate more than one option
5. identify missing or weak evidence
6. revisit previous steps when additional investigation is required
7. determine whether human review is needed
8. produce a structured recommendation with supporting evidence
