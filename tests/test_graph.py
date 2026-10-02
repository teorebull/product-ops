from procurement_ops import nodes
from procurement_ops.graph import build_graph
from procurement_ops.models import (
    AnalysisResult,
    ProcurementRequest,
    ProcurementRequirements,
    RecommendationResult,
    ResearchResult,
    SupplierCandidate,
)
from procurement_ops.state import create_initial_state


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


def test_graph_runs_complete_pipeline_without_external_agents(monkeypatch) -> None:
    analysis = AnalysisResult(
        requirements=ProcurementRequirements(
            category="IT hardware",
            product="Business laptops",
            quantity=40,
        )
    )
    research = ResearchResult(
        supplier_candidates=[SupplierCandidate(supplier="Example Supplier")]
    )
    recommendation = RecommendationResult(
        summary="Summary",
        recommendation="Proceed with review.",
        recommended_supplier="Example Supplier",
    )
    responses = iter([analysis, recommendation])

    monkeypatch.setattr(
        nodes,
        "ChatOpenAI",
        lambda model: FakeChatModel(next(responses)),
    )
    monkeypatch.setattr(
        nodes,
        "search_procurement_knowledge",
        lambda query: {"results": [{"content": "policy evidence"}]},
    )
    monkeypatch.setattr(
        nodes,
        "evaluate_supplier_candidates",
        lambda requirements, candidates: {"evaluations": []},
    )

    class FakeResearchAgent:
        def invoke(self, payload):
            return {"structured_response": research}

    monkeypatch.setattr(
        nodes,
        "create_research_agent",
        lambda model_name: FakeResearchAgent(),
    )

    app = build_graph("test-model")
    result = app.invoke(
        create_initial_state(
            ProcurementRequest(
                requester="IT",
                item="Business laptops",
                quantity=40,
            )
        )
    )

    assert result["analysis"] == analysis
    assert result["research"] == research
    assert result["recommendation"] == recommendation
    assert result["next_action"] == "complete"
    assert result["status"] == "COMPLETED"
