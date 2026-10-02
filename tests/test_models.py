import pytest
from pydantic import ValidationError

from procurement_ops.models import (
    AnalysisResult,
    ProcurementRequest,
    ProcurementRequirements,
    RecommendationResult,
    ResearchResult,
    SupplierCandidate,
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
    assert request.requirements == ["16 GB RAM minimum", "3-year warranty"]


def test_procurement_request_allows_optional_information_to_be_missing() -> None:
    request = ProcurementRequest(requester="Finance", item="Monitors")

    assert request.quantity is None
    assert request.budget_eur is None
    assert request.requirements == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("quantity", 0),
        ("quantity", -1),
        ("budget_eur", -1),
        ("delivery_deadline_days", 0),
    ],
)
def test_procurement_request_rejects_invalid_values(
    field: str,
    value: int,
) -> None:
    with pytest.raises(ValidationError):
        ProcurementRequest(requester="IT", item="Laptops", **{field: value})


def test_analysis_result_defaults_collections() -> None:
    result = AnalysisResult(
        requirements=ProcurementRequirements(
            category="IT hardware",
            product="Business laptop",
        )
    )

    assert result.missing_information == []
    assert result.applicable_policies == []
    assert result.evidence == []


def test_research_result_contains_supplier_candidates() -> None:
    result = ResearchResult(
        supplier_candidates=[SupplierCandidate(supplier="Example Supplier")]
    )

    assert result.supplier_candidates[0].supplier == "Example Supplier"
    assert result.historical_tenders == []


def test_recommendation_result_defaults_collections() -> None:
    result = RecommendationResult(
        summary="A summary",
        recommendation="Proceed with further review.",
    )

    assert result.risks == []
    assert result.uncertainties == []


@pytest.mark.parametrize(
    "next_action",
    [
        "procurement_analysis",
        "supplier_research",
        "recommendation",
        "complete",
        "needs_information",
    ],
)
def test_supervisor_decision_accepts_valid_actions(next_action: str) -> None:
    decision = SupervisorDecision(next_action=next_action)

    assert decision.next_action == next_action


def test_supervisor_decision_rejects_invalid_action() -> None:
    with pytest.raises(ValidationError):
        SupervisorDecision(next_action="unknown_action")
