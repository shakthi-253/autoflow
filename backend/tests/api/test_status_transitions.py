"""
Business rule tests for status transitions - the core of AutoFlow's
workflow enforcement. Mirrors app/models/service.py::ALLOWED_TRANSITIONS.

For every invalid transition we assert:
- HTTP 409
- error code INVALID_TRANSITION
- the details payload names current_status/requested_status
- the service's status in the database is UNCHANGED afterwards
"""
import pytest

VALID_TRANSITIONS = [
    ("BOOKED", "INSPECTION"),
    ("BOOKED", "CANCELLED"),
    ("INSPECTION", "REPAIR"),
    ("INSPECTION", "CANCELLED"),
    ("REPAIR", "COMPLETED"),
]

INVALID_TRANSITIONS = [
    ("BOOKED", "REPAIR"),
    ("BOOKED", "COMPLETED"),
    ("INSPECTION", "COMPLETED"),
    ("COMPLETED", "REPAIR"),
    ("COMPLETED", "CANCELLED"),
    ("CANCELLED", "REPAIR"),
    ("CANCELLED", "COMPLETED"),
    # Additional cases not explicitly listed in the spec but implied by
    # ALLOWED_TRANSITIONS: a status can never transition to itself, and
    # BOOKED can't be re-reached from anywhere.
    ("BOOKED", "BOOKED"),
    ("INSPECTION", "BOOKED"),
    ("REPAIR", "BOOKED"),
    ("REPAIR", "INSPECTION"),
]

# Path of transitions needed to DRIVE a fresh BOOKED service to a given
# starting status before testing the next transition from there.
PATH_TO_STATUS = {
    "BOOKED": [],
    "INSPECTION": ["INSPECTION"],
    "REPAIR": ["INSPECTION", "REPAIR"],
    "COMPLETED": ["INSPECTION", "REPAIR", "COMPLETED"],
    "CANCELLED": ["CANCELLED"],
}


def _drive_to_status(client, service_id, target_status):
    for step in PATH_TO_STATUS[target_status]:
        res = client.patch(f"/services/{service_id}/status", json={"status": step})
        assert res.status_code == 200, f"setup transition to {step} failed: {res.text}"


@pytest.mark.parametrize("current,target", VALID_TRANSITIONS)
def test_valid_transition_succeeds(client, valid_service_payload, current, target):
    created = client.post("/services", json=valid_service_payload).json()
    service_id = created["id"]
    _drive_to_status(client, service_id, current)

    res = client.patch(f"/services/{service_id}/status", json={"status": target})
    assert res.status_code == 200
    assert res.json()["status"] == target


@pytest.mark.parametrize("current,target", INVALID_TRANSITIONS)
def test_invalid_transition_is_rejected(client, valid_service_payload, current, target):
    created = client.post("/services", json=valid_service_payload).json()
    service_id = created["id"]
    _drive_to_status(client, service_id, current)

    res = client.patch(f"/services/{service_id}/status", json={"status": target})

    assert res.status_code == 409
    body = res.json()
    assert body["error"] == "INVALID_TRANSITION"
    assert body["details"]["current_status"] == current
    assert body["details"]["requested_status"] == target

    # The service's actual status must be unchanged after a rejected transition.
    unchanged = client.get(f"/services/{service_id}").json()
    assert unchanged["status"] == current


def test_repeated_identical_status_update_from_terminal_state_is_rejected(
    client, valid_service_payload
):
    """Calling PATCH with the service's OWN current terminal status is still
    a no-op transition and should be rejected, not silently accepted."""
    created = client.post("/services", json=valid_service_payload).json()
    service_id = created["id"]
    client.patch(f"/services/{service_id}/status", json={"status": "CANCELLED"})

    res = client.patch(f"/services/{service_id}/status", json={"status": "CANCELLED"})
    assert res.status_code == 409


def test_status_transition_on_nonexistent_service_returns_404(client):
    res = client.patch("/services/999999/status", json={"status": "INSPECTION"})
    assert res.status_code == 404
    body = res.json()
    assert body["error"] == "SERVICE_NOT_FOUND"


def test_status_transition_with_invalid_status_value_returns_422(
    client, valid_service_payload
):
    created = client.post("/services", json=valid_service_payload).json()
    res = client.patch(
        f"/services/{created['id']}/status", json={"status": "NOT_A_REAL_STATUS"}
    )
    assert res.status_code == 422
    body = res.json()
    assert body["error"] == "VALIDATION_ERROR"

    # Status must remain unchanged.
    unchanged = client.get(f"/services/{created['id']}").json()
    assert unchanged["status"] == "BOOKED"
