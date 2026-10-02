from procurement_ops.models import ProcurementRequest
from procurement_ops.state import ProcurementState, create_initial_state


def test_state_can_be_created_from_a_valid_request() -> None:
    request = ProcurementRequest(requester="IT", item="Laptops")

    state = ProcurementState(request_id="REQ-001", original_request=request)

    assert state.request_id == "REQ-001"
    assert state.original_request == request
    assert state.analysis is None
    assert state.research is None
    assert state.recommendation is None
    assert state.status == "NEW"


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
