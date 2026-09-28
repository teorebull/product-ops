import pytest
from pydantic import ValidationError

from procurement_ops.models import (
    FinalRecommendation,
    ProcurementRequest,
    ProcurementRequirements,
    RiskApprovalResult,
    SupplierCandidate,
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
