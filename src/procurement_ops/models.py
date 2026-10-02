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
        "recommendation",
        "complete",
        "needs_information",
    ]
    
class SupplierCandidate(BaseModel):
    """Represents a supplier candidate."""

    supplier: str
    estimated_price_eur: float | None = None
    delivery_days: int | None = None
    source: str | None = None


class AnalysisResult(BaseModel):
    requirements: ProcurementRequirements
    missing_information: list[str] = Field(default_factory=list)
    applicable_policies: list[str] = Field(default_factory=list)
    evidence: list[dict] = Field(default_factory=list)
    
class ResearchResult(BaseModel):
    supplier_candidates: list[SupplierCandidate] = Field(default_factory=list)
    historical_tenders: list[dict] = Field(default_factory=list)
    evidence: list[dict] = Field(default_factory=list)

class RecommendationResult(BaseModel):
    summary: str
    recommendation: str
    recommended_supplier: str | None = None
    risks: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)