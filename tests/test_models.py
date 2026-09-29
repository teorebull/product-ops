import pytest
from pydantic import ValidationError

from procurement_ops.models import (
    EvaluationCriterion,
    EvaluationResult,
    EvaluationCriterion,
    EvaluationRiskResult,
    FinalRecommendation,
    ProcurementAnalysisResult,
    ProcurementRequest,
    ProcurementRequirements,
    RiskApprovalResult,
    SupplierCandidate,
    SupplierResearchResult,
    SupervisorDecision,
)


def test_procurement_request_accepts_documented_example() -> None:
    request = ProcurementRequest(
        requester="IT Department",
        item="Business laptops",
        quantity=40,
        budget_eur=45000,
        location="Barcelona, Spain",
        delivery_deadline_days=21,
        requirements=["16 GB RAM minimum", "3-year warranty"],
    )

    assert request.quantity == 40
    assert request.budget_eur == 45000


def test_procurement_request_allows_missing_optional_information() -> None:
    request = ProcurementRequest(requester="Finance", item="Monitors")

    assert request.quantity is None
    assert request.requirements == []


@pytest.mark.parametrize(
    ("field", "value"),
    [("quantity", 0), ("quantity", -1), ("budget_eur", -1), ("delivery_deadline_days", 0)],
)
def test_procurement_request_rejects_invalid_positive_values(
    field: str, value: int
) -> None:
    with pytest.raises(ValidationError):
        ProcurementRequest(requester="IT", item="Laptops", **{field: value})


def test_supplier_candidate_defaults_evidence_collections() -> None:
    candidate = SupplierCandidate(supplier="Example Supplier")

    assert candidate.pricing_evidence is None
    assert candidate.historical_contracts == []
    assert candidate.sources == []


def test_risk_result_validates_level_and_confidence() -> None:
    result = RiskApprovalResult(
        risk_level="MEDIUM",
        confidence=0.8,
        approval_required=True,
    )

    assert result.risk_factors == []

    with pytest.raises(ValidationError):
        RiskApprovalResult(
            risk_level="UNKNOWN",
            confidence=0.8,
            approval_required=False,
        )

    with pytest.raises(ValidationError):
        RiskApprovalResult(
            risk_level="LOW",
            confidence=1.1,
            approval_required=False,
        )


def test_final_recommendation_accepts_structured_components() -> None:
    recommendation = FinalRecommendation(
        request_id="REQ-001",
        status="NEEDS_INFORMATION",
        summary="More information is required.",
        requirements=ProcurementRequirements(category="IT hardware", product="Laptop"),
        suppliers_considered=[],
        risk=RiskApprovalResult(
            risk_level="LOW",
            confidence=0.5,
            approval_required=False,
        ),
        approval={},
        recommendation="Collect the missing procurement information.",
    )

    assert recommendation.evaluation == []
    assert recommendation.recommended_option is None


def test_procurement_analysis_result_accepts_structured_output() -> None:
    result = ProcurementAnalysisResult(
        requirements=ProcurementRequirements(
            category="IT hardware",
            product="Business laptop",
            quantity=40,
        ),
        missing_information=["delivery deadline"],
        applicable_policies=["EU procurement guidance"],
        evaluation_criteria=[
            EvaluationCriterion(
                name="technical compliance",
                weight=0.3,
                description="Compliance with the technical requirements.",
            )
        ],
        evidence=[{"source": "procurement guidance", "reference": "section 1"}],
    )

    assert result.requirements.product == "Business laptop"
    assert result.missing_information == ["delivery deadline"]
    assert result.evaluation_criteria[0].weight == 0.3
    assert result.evidence[0]["source"] == "procurement guidance"


def test_procurement_analysis_result_defaults_collections() -> None:
    result = ProcurementAnalysisResult(
        requirements=ProcurementRequirements(
            category="IT hardware",
            product="Monitor",
        )
    )

    assert result.missing_information == []
    assert result.applicable_policies == []
    assert result.evaluation_criteria == []
    assert result.evidence == []


def test_supplier_research_result_accepts_candidates_and_tenders() -> None:
    result = SupplierResearchResult(
        supplier_candidates=[SupplierCandidate(supplier="Example Supplier")],
        historical_tenders=[{"notice_id": "TED-001"}],
        missing_information=["delivery evidence"],
        evidence=[{"source": "TED", "reference": "TED-001"}],
        research_completed=True,
    )

    assert result.supplier_candidates[0].supplier == "Example Supplier"
    assert result.historical_tenders[0]["notice_id"] == "TED-001"
    assert result.research_completed is True


def test_supplier_research_result_defaults_collections() -> None:
    result = SupplierResearchResult()

    assert result.supplier_candidates == []
    assert result.historical_tenders == []
    assert result.missing_information == []
    assert result.evidence == []
    assert result.research_completed is False


def test_evaluation_risk_result_accepts_evaluations_and_risks() -> None:
    evaluation = EvaluationResult(
        supplier="Example Supplier",
        compliance={"technical_requirements": "PASS"},
    )
    risk = RiskApprovalResult(
        risk_level="MEDIUM",
        confidence=0.8,
        approval_required=True,
        approval_type="PROCUREMENT_REVIEW",
    )

    result = EvaluationRiskResult(
        supplier_evaluations=[evaluation],
        risks=[risk],
        approval_required=True,
    )

    assert result.supplier_evaluations[0].supplier == "Example Supplier"
    assert result.risks[0].risk_level == "MEDIUM"
    assert result.approval_required is True


def test_evaluation_risk_result_defaults_optional_fields() -> None:
    result = EvaluationRiskResult()

    assert result.supplier_evaluations == []
    assert result.risks == []
    assert result.approval_required is None


@pytest.mark.parametrize(
    "next_action",
    [
        "procurement_analysis",
        "supplier_research",
        "evaluation_risk",
        "finalize",
        "needs_information",
    ],
)
def test_supervisor_decision_accepts_valid_actions(next_action: str) -> None:
    decision = SupervisorDecision(next_action=next_action, reason="Continue analysis.")

    assert decision.next_action == next_action


def test_supervisor_decision_rejects_invalid_action() -> None:
    with pytest.raises(ValidationError):
        SupervisorDecision(next_action="unknown_action", reason="Invalid route.")
