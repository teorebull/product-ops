"""Pydantic domain models for procurement workflows."""

from typing import Literal

from pydantic import BaseModel, Field

class ProcurementRequest(BaseModel):
    """Represents a procurement request."""

    requester: str
    item: str
    quantity: int | None = Field(default=None, gt=0)
    budget_eur: float | None = Field(default=None, ge=0)
    location: str | None = None
    delivery_deadline_days: int | None = Field(default=None, gt=0)
    requirements: list[str] = Field(default_factory=list)

class ProcurementRequirements(BaseModel):
    """Structured requirements extracted from a procurement request."""

    category: str
    product: str
    quantity: int | None = Field(default=None, gt=0)
    budget_eur: float | None = Field(default=None, ge=0)
    max_unit_budget_eur: float | None = Field(default=None, ge=0)
    location: str | None = None
    delivery_deadline_days: int | None = Field(default=None, gt=0)
    technical_requirements: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)

class SupplierCandidate(BaseModel):
    """Represents a supplier candidate for a procurement request."""

    supplier: str
    pricing_evidence: dict | None = None
    delivery_evidence: dict | None = None
    technical_evidence: dict | None = None
    historical_contracts: list[dict] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)

class EvaluationResult(BaseModel):
    """Represents the evaluation result of a supplier candidate."""

    supplier: str
    compliance: dict
    score: float | None = None
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)

class RiskApprovalResult(BaseModel):
    """Represents risk and approval findings for a procurement request."""

    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    confidence: float = Field(ge=0, le=1)
    risk_factors: list[str] = Field(default_factory=list)
    approval_required: bool
    approval_type: str | None = None
    reasons: list[str] = Field(default_factory=list)

class FinalRecommendation(BaseModel):
    """Represents the final recommendation for a procurement request."""

    request_id: str
    status: Literal[
        "READY_TO_PROCEED",
        "HUMAN_REVIEW_REQUIRED",
        "NEEDS_INFORMATION",
    ]
    summary: str
    requirements: ProcurementRequirements
    suppliers_considered: list[SupplierCandidate]
    recommended_option: dict | None = None
    evaluation: list[EvaluationResult] = Field(default_factory=list)
    risk: RiskApprovalResult
    approval: dict
    evidence: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    recommendation: str
