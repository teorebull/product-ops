from procurement_ops.models import ProcurementRequest
from procurement_ops.state import ProcurementState, create_initial_state


def test_state_can_be_created_from_a_valid_request() -> None:
    request = ProcurementRequest(requester="IT", item="Laptops")

    state = ProcurementState(request_id="REQ-001", original_request=request)

    assert state.request_id == "REQ-001"
    assert state.original_request == request
    assert state.requirements is None
    assert state.status == "NEW"
    assert state.approval_required is None
    assert state.final_recommendation is None


def test_state_collections_start_empty() -> None:
    request = ProcurementRequest(requester="IT", item="Laptops")
    state = ProcurementState(request_id="REQ-001", original_request=request)

    assert state.missing_information == []
    assert state.applicable_policies == []
    assert state.evaluation_criteria == []
    assert state.supplier_candidates == []
    assert state.historical_tenders == []
    assert state.supplier_evaluations == []
    assert state.risks == []
    assert state.evidence == []
    assert state.agent_history == []


def test_state_collections_are_not_shared_between_instances() -> None:
    request = ProcurementRequest(requester="IT", item="Laptops")
    first = ProcurementState(request_id="REQ-001", original_request=request)
    second = ProcurementState(request_id="REQ-002", original_request=request)

    first.missing_information.append("delivery location")
    first.agent_history.append({"agent": "Supervisor"})

    assert second.missing_information == []
    assert second.agent_history == []


def test_create_initial_state_uses_supplied_request_id() -> None:
    request = ProcurementRequest(requester="IT", item="Laptops")

    state = create_initial_state(request, request_id="REQ-001")

    assert state.request_id == "REQ-001"
    assert state.original_request == request
    assert state.status == "NEW"


def test_create_initial_state_generates_request_id() -> None:
    request = ProcurementRequest(requester="IT", item="Laptops")

    state = create_initial_state(request)

    assert state.request_id
    assert state.original_request == request
