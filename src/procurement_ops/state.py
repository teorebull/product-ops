"""Shared LangGraph state definitions."""

from uuid import uuid4
from typing import Literal

from pydantic import BaseModel, Field
from uuid_utils import uuid4
from procurement_ops.models import (
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
    evaluation_criteria: list[str] = Field(default_factory=list)
    supplier_candidates: list[SupplierCandidate] = Field(default_factory=list)
    historical_tenders: list[dict] = Field(default_factory=list)
    supplier_evaluations: list[EvaluationResult] = Field(default_factory=list)
    risks: list[RiskApprovalResult] = Field(default_factory=list)
    approval_required: bool | None = None
    approval_reason: str | None = None
    evidence: list[dict] = Field(default_factory=list)
    agent_history: list[dict] = Field(default_factory=list)
    next_action: str | None = None
    status: str = "NEW"
    final_recommendation: FinalRecommendation | None = None


class SupervisorDecision(BaseModel):
    next_action: Literal[
        "procurement_analysis",
        "supplier_research",
        "evaluation_risk",
        "finalize",
        "needs_information",
    ]
    reason: str

def create_initial_state(request: ProcurementRequest, request_id: str | None = None) -> ProcurementState:
    """Creates an initial state for a procurement workflow."""
    return ProcurementState(
        request_id = request_id or str(uuid4()),
        original_request=request
    )

def get_current_state(state: ProcurementState) -> dict:
    """Returns the current state as a dictionary."""
    return state.dict()