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
    location: str | None = None
    delivery_deadline_days: int | None = Field(default=None, gt=0)
    technical_requirements: list[str] = Field(default_factory=list)

class SupervisorDecision(BaseModel):
    """Represents the decision made by the supervisor node."""

    next_action: Literal[
        "procurement_analysis",
        "supplier_research",
        "evaluation_risk",
        "finalize",
        "needs_information",
    ]


class AnalysisResult(BaseModel):
    requirements: ProcurementRequirements
    missing_information: list[str] = []
    applicable_policies: list[str] = []
    evidence: list[dict] = []
class ResearchResult(BaseModel):
    supplier_candidates: list[dict] = []
    historical_tenders: list[dict] = []
    evidence: list[dict] = []
class RecommendationResult(BaseModel):
    summary: str
    recommendation: str
    recommended_supplier: str | None = None
    risks: list[str] = []
    uncertainties: list[str] = []