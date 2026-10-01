"""Shared LangGraph state definitions."""

from uuid import uuid4
from pydantic import BaseModel, Field
from procurement_ops.models import (
    ProcurementRequest,
    ProcurementRequirements,
    AnalysisResult,
    ResearchResult,
    RecommendationResult,
)


class ProcurementState(BaseModel):
    """Represents the state of a procurement workflow."""
    request_id: str
    original_request: ProcurementRequest

    analysis: AnalysisResult | None = None
    research: ResearchResult | None = None
    recommendation: RecommendationResult | None = None

    next_action: str | None = None
    status: str = "NEW"

def create_initial_state(request: ProcurementRequest, request_id: str | None = None) -> ProcurementState:
    """Creates an initial state for a procurement workflow."""
    return ProcurementState(
        request_id = request_id or str(uuid4()),
        original_request=request
        )
