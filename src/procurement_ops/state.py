"""Shared LangGraph state definitions."""

from uuid import uuid4
from pydantic import BaseModel, Field
from procurement_ops.models import (
    EvaluationCriterion,
    FinalRecommendation,
    ProcurementRequest,
    ProcurementRequirements,
    SupplierCandidate,
    EvaluationResult,
    RiskApprovalResult,
)


class ProcurementState(BaseModel):
    """Represents the state of a procurement workflow."""

    request_id: str
    original_request: ProcurementRequest
    requirements: ProcurementRequirements | None = None
    missing_information: list[str] = Field(default_factory=list)
    applicable_policies: list[str] = Field(default_factory=list)
    evaluation_criteria: list[EvaluationCriterion] = Field(default_factory=list)
    supplier_candidates: list[SupplierCandidate] = Field(default_factory=list)
    historical_tenders: list[dict] = Field(default_factory=list)
    supplier_evaluations: list[EvaluationResult] = Field(default_factory=list)
    risks: list[RiskApprovalResult] = Field(default_factory=list)
    approval_required: bool | None = None
    evidence: list[dict] = Field(default_factory=list)
    agent_history: list[dict] = Field(default_factory=list)
    next_action: str | None = None
    status: str = "NEW"
    final_recommendation: FinalRecommendation | None = None


def create_initial_state(request: ProcurementRequest, request_id: str | None = None) -> ProcurementState:
    """Creates an initial state for a procurement workflow."""
    return ProcurementState(
        request_id = request_id or str(uuid4()),
        original_request=request
    )
