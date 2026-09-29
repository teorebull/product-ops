# Next Steps

Implementation checklist for the V1 multi-agent procurement workflow.

## Architecture Rules

- Nodes perform agent reasoning.
- Tools perform bounded calculations, retrieval, API calls, and business rules.
- The supervisor performs routing only.
- Agents never call other agents directly.
- Nodes read shared state and return state updates.
- The graph controls execution order and loops.
- V1 must not place orders, transfer money, contact suppliers, sign contracts, or approve purchases.

## 1. Freeze the State Contract

**Status: Complete**

Finalize `ProcurementState` in `src/procurement_ops/state.py`.

Required state areas:

- Original request
- Structured requirements
- Missing information
- Applicable policies
- Evaluation criteria
- Supplier candidates
- Historical tenders
- Supplier evaluations
- Risk findings
- Approval information
- Evidence
- Agent history
- Next action
- Workflow status
- Final recommendation

Use one state convention consistently throughout the project: Pydantic model attributes or dictionaries.

## 2. Define Agent Output Models

**Status: Complete**

Add structured output models for:

- `ProcurementAnalysisResult`
- `SupplierResearchResult`
- `EvaluationRiskResult`
- `SupervisorDecision`

The procurement analysis result must include:

- Structured requirements
- Missing information
- Applicable policies
- Evaluation criteria
- Evidence

The models should be placed in `src/procurement_ops/models.py` and validated with tests.

## 3. Make the Project Runnable

**Status: Complete**

- Fix import issues.
- Declare every direct dependency in `pyproject.toml`.
- Resolve the duplicate `uuid4` import.
- Run the existing test suite successfully.

## 4. Implement Deterministic Tools

**Status: Not started**

Implement in `src/procurement_ops/tools.py`:

- `calculate_unit_budget`
- `calculate_weighted_score`
- `evaluate_requirement_compliance`

`check_approval_rules` is deferred until approval thresholds, approval types,
and critical-information rules are configured explicitly.

Tools must accept structured input and return structured output. They must not
contain agent-routing logic.

## 5. Implement the Procurement Analysis Node

**Status: Not started**

Implement `procurement_analysis_node` in `src/procurement_ops/nodes.py`.

Responsibilities:

1. Read `state.original_request`.
2. Send the request to the LLM.
3. Request structured output using `ProcurementAnalysisResult`.
4. Let the analysis determine requirements and missing information.
5. Retrieve policy guidance through tools when available.
6. Return updates for requirements, policies, criteria, missing information, and evidence.

The node must not decide which agent runs next.

## 6. Implement the Supervisor Node

**Status: Not started**

Implement `supervisor_node` in `src/procurement_ops/nodes.py`.

The supervisor reads the current state and routes to:

- `needs_information` when essential information is missing
- `procurement_analysis` when policy or analysis is incomplete
- `supplier_research` when supplier evidence is missing
- `evaluation_risk` when suppliers have not been evaluated
- `supplier_research` when evaluation requests more evidence
- `evaluation_risk` when risk has not been assessed
- `finalize` when sufficient evidence exists

The supervisor may use an LLM, but its output must be constrained by `SupervisorDecision`.

## 7. Implement Supplier Research

**Status: Not started**

Implement:

- `supplier_research_node`
- `search_tenders`
- `get_tender_details`
- `search_supplier_information`

Start with mocked or fixture data. Add TED integration after the local graph works.

The node must return:

- Supplier candidates
- Historical tenders
- Evidence
- Missing evidence
- Research completion status

## 8. Implement Evaluation and Risk

**Status: Not started**

Implement `evaluation_risk_node`.

Responsibilities:

1. Compare candidates against requirements.
2. Preserve `UNKNOWN` separately from `FAIL`.
3. Calculate weighted scores through tools.
4. Assess procurement risk.
5. Apply deterministic approval rules.
6. Indicate whether more research is required.

## 9. Implement Finalization

**Status: Not started**

Implement `build_final_recommendation`.

The final result must use one of:

- `READY_TO_PROCEED`
- `HUMAN_REVIEW_REQUIRED`
- `NEEDS_INFORMATION`

It must preserve facts, calculations, AI analysis, evidence, and unresolved questions.

## 10. Build the LangGraph

**Status: Not started**

Wire the graph in `src/procurement_ops/graph.py`:

```text
START
  -> procurement_analysis
  -> supervisor
```

Supervisor routes:

```text
procurement_analysis -> procurement_analysis
supplier_research   -> supplier_research
evaluation_risk     -> evaluation_risk
needs_information   -> finalize
finalize             -> END
```

Every specialist node returns control to the supervisor.

## 11. Test Routing and Agent Behavior

**Status: Not started**

Add tests for:

- Initial request routes to procurement analysis.
- Missing information routes to `needs_information`.
- Complete analysis routes to supplier research.
- Supplier results route to evaluation and risk.
- Insufficient evaluation evidence routes back to supplier research.
- Complete risk assessment routes to finalization.
- Approval requirements produce `HUMAN_REVIEW_REQUIRED`.
- No approval requirement produces `READY_TO_PROCEED`.

Mock LLM responses in unit tests. Tests must not require live model or external API access.

## 12. Add External Integrations

**Status: Not started**

Add these only after the local graph works:

- RAG knowledge search
- Procurement source retrieval
- TED API
- Supplier information APIs
- Production model configuration
- Persistence
- API layer
- Observability

## First Milestone

The first working vertical slice is:

```text
Request
  -> procurement_analysis_node
  -> supervisor_node
  -> NEEDS_INFORMATION
  -> finalization
```

Complete this path with mocked LLM output before implementing supplier research and evaluation.
