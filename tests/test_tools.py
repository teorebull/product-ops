from procurement_ops.models import ProcurementRequirements, SupplierCandidate
from procurement_ops.tools import evaluate_supplier_candidates


def test_evaluate_supplier_candidates_checks_budget_and_deadline() -> None:
    result = evaluate_supplier_candidates(
        ProcurementRequirements(
            category="IT hardware",
            product="Business laptops",
            quantity=40,
            budget_eur=45000,
            delivery_deadline_days=21,
        ),
        [
            SupplierCandidate(
                supplier="Eligible Supplier",
                estimated_price_eur=40000,
                delivery_days=14,
            ),
            SupplierCandidate(
                supplier="Ineligible Supplier",
                estimated_price_eur=50000,
                delivery_days=28,
            ),
        ],
    )

    evaluations = result["evaluations"]

    assert evaluations[0]["eligible"] is True
    assert evaluations[1]["eligible"] is False


def test_evaluate_supplier_candidates_preserves_unknown_values() -> None:
    result = evaluate_supplier_candidates(
        ProcurementRequirements(
            category="IT hardware",
            product="Business laptops",
        ),
        [SupplierCandidate(supplier="Unknown Supplier")],
    )

    evaluation = result["evaluations"][0]

    assert evaluation["within_budget"] is None
    assert evaluation["meets_deadline"] is None
    assert evaluation["eligible"] is None
