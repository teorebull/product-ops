"""Deterministic procurement tools."""

from procurement_ops.models import (
    EvaluationCriterion,
    ProcurementRequirements,
    SupplierCandidate,
)

def calculate_unit_budget(total_budget: float, quantity: int) -> dict:
    """Calculate the maximum available budget per item."""
    if total_budget < 0:
        raise ValueError("total_budget must be non-negative")
    if quantity <= 0:
        raise ValueError("quantity must be greater than zero")

    return {"max_unit_budget": total_budget / quantity}


def check_approval_rules(
    purchase_value: float,
    supplier_count: int,
    missing_information: list[str],
    risk_level: str | None,
) -> dict:
    """Deferred until approval thresholds and critical fields are configured."""
    raise NotImplementedError(
        "Approval rules require explicit procurement configuration before implementation."
    )


def calculate_weighted_score(
    criteria: list[EvaluationCriterion], scores: dict[str, float]
) -> dict:
    """Calculate a deterministic weighted score from 0-100 criterion scores."""
  


def evaluate_requirement_compliance(
    requirements: ProcurementRequirements, supplier_evidence: SupplierCandidate
) -> dict:
    """Evaluate supplier evidence against requirements once its schema is defined."""
    raise NotImplementedError(
        "Requirement compliance needs a typed PASS/FAIL/UNKNOWN result model."
    )