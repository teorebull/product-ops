from procurement_ops import nodes
from procurement_ops.models import (
    AnalysisResult,
    ProcurementRequest,
    ProcurementRequirements,
    RecommendationResult,
    ResearchResult,
    SupplierCandidate,
)
from procurement_ops.state import ProcurementState


def make_state(
    *,
    analysis: AnalysisResult | None = None,
    research: ResearchResult | None = None,
    recommendation: RecommendationResult | None = None,
) -> ProcurementState:
    return ProcurementState(
        request_id="REQ-001",
        original_request=ProcurementRequest(
            requester="IT",
            item="Business laptops",
            quantity=40,
        ),
        analysis=analysis,
        research=research,
        recommendation=recommendation,
    )


def make_analysis(quantity: int | None = 40) -> AnalysisResult:
    return AnalysisResult(
        requirements=ProcurementRequirements(
            category="IT hardware",
            product="Business laptops",
            quantity=quantity,
        )
    )


def test_supervisor_routes_to_analysis_when_analysis_is_missing() -> None:
    result = nodes.supervisor_node(make_state())

    assert result == {
        "next_action": "procurement_analysis",
        "status": "IN_PROGRESS",
    }


def test_supervisor_requests_required_information() -> None:
    result = nodes.supervisor_node(make_state(analysis=make_analysis(None)))

    assert result == {
        "next_action": "needs_information",
        "status": "WAITING_FOR_INFORMATION",
    }


def test_supervisor_routes_through_remaining_nodes() -> None:
    analysis = make_analysis()
    research = ResearchResult()
    recommendation = RecommendationResult(
        summary="Summary",
        recommendation="Recommendation",
    )

    assert nodes.supervisor_node(make_state(analysis=analysis))["next_action"] == (
        "supplier_research"
    )
    assert nodes.supervisor_node(
        make_state(analysis=analysis, research=research)
    )["next_action"] == "recommendation"
    assert nodes.supervisor_node(
        make_state(
            analysis=analysis,
            research=research,
            recommendation=recommendation,
        )
    ) == {"next_action": "complete", "status": "COMPLETED"}


class FakeStructuredModel:
    def __init__(self, response):
        self.response = response

    def invoke(self, messages):
        return self.response


class FakeChatModel:
    def __init__(self, response):
        self.response = response

    def with_structured_output(self, schema):
        return FakeStructuredModel(self.response)


def test_analysis_node_returns_structured_analysis(monkeypatch) -> None:
    expected = make_analysis()

    monkeypatch.setattr(
        nodes,
        "search_procurement_knowledge",
        lambda query: {"results": [{"content": "policy evidence"}]},
    )
    monkeypatch.setattr(nodes, "ChatOpenAI", lambda model: FakeChatModel(expected))

    result = nodes.analysis_node(make_state(), model_name="test-model")

    assert result == {"analysis": expected}


def test_research_node_returns_agent_structured_response(monkeypatch) -> None:
    expected = ResearchResult(
        supplier_candidates=[SupplierCandidate(supplier="Example Supplier")]
    )

    class FakeResearchAgent:
        def invoke(self, payload):
            assert payload["messages"][0]["role"] == "user"
            return {"structured_response": expected}

    monkeypatch.setattr(
        nodes,
        "create_research_agent",
        lambda model_name: FakeResearchAgent(),
    )

    result = nodes.research_node(
        make_state(analysis=make_analysis()),
        model_name="test-model",
    )

    assert result == {"research": expected}


def test_recommendation_node_returns_structured_recommendation(monkeypatch) -> None:
    expected = RecommendationResult(
        summary="Summary",
        recommendation="Proceed with review.",
        recommended_supplier="Example Supplier",
    )
    research = ResearchResult(
        supplier_candidates=[SupplierCandidate(supplier="Example Supplier")]
    )

    monkeypatch.setattr(
        nodes,
        "evaluate_supplier_candidates",
        lambda requirements, candidates: {
            "evaluations": [
                {
                    "supplier": "Example Supplier",
                    "eligible": None,
                }
            ]
        },
    )
    monkeypatch.setattr(nodes, "ChatOpenAI", lambda model: FakeChatModel(expected))

    result = nodes.recommendation_node(
        make_state(analysis=make_analysis(), research=research),
        model_name="test-model",
    )

    assert result == {"recommendation": expected}
