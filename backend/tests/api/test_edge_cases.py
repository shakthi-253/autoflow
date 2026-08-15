"""
Edge-case tests: values right at the boundary of what the actual
validators accept, plus edge behaviors of the workflow/dashboard logic.
"""
from datetime import datetime


def test_dashboard_stats_on_empty_database(client):
    res = client.get("/services/stats/dashboard")
    assert res.status_code == 200
    body = res.json()
    assert body == {
        "total_services": 0,
        "booked": 0,
        "inspection": 0,
        "repair": 0,
        "completed": 0,
        "cancelled": 0,
    }


def test_list_services_on_empty_database_returns_empty_list(client):
    res = client.get("/services")
    assert res.status_code == 200
    assert res.json() == []


def test_get_nonexistent_service_returns_404(client):
    res = client.get("/services/999999")
    assert res.status_code == 404
    assert res.json()["error"] == "SERVICE_NOT_FOUND"


def test_get_nonexistent_vehicle_returns_404(client):
    res = client.get("/vehicles/999999")
    assert res.status_code == 404
    assert res.json()["error"] == "VEHICLE_NOT_FOUND"


def test_get_service_with_zero_id_returns_404_not_error(client):
    res = client.get("/services/0")
    assert res.status_code == 404


def test_get_service_with_negative_id_returns_404(client):
    res = client.get("/services/-1")
    assert res.status_code == 404


def test_registration_number_minimum_valid_length(client, valid_service_payload):
    """5 characters is the shortest string the pattern accepts."""
    payload = dict(valid_service_payload)
    payload["registration_number"] = "AB123"
    res = client.post("/services", json=payload)
    assert res.status_code == 201
    assert res.json()["vehicle"]["registration_number"] == "AB123"


def test_registration_number_maximum_valid_length(client, valid_service_payload):
    """17 characters is the longest string the regex pattern accepts."""
    payload = dict(valid_service_payload)
    reg = "A" * 17
    payload["registration_number"] = reg
    res = client.post("/services", json=payload)
    assert res.status_code == 201
    assert res.json()["vehicle"]["registration_number"] == reg


def test_contact_number_minimum_valid_length(client, valid_service_payload):
    """7 digits is the minimum accepted by the pattern."""
    payload = dict(valid_service_payload)
    payload["contact_number"] = "1234567"
    res = client.post("/services", json=payload)
    assert res.status_code == 201


def test_contact_number_maximum_valid_length(client, valid_service_payload):
    """15 digits is the maximum accepted by the pattern."""
    payload = dict(valid_service_payload)
    payload["contact_number"] = "1" * 15
    res = client.post("/services", json=payload)
    assert res.status_code == 201


def test_contact_number_with_leading_plus_is_accepted(client, valid_service_payload):
    payload = dict(valid_service_payload)
    payload["contact_number"] = "+919876543210"
    res = client.post("/services", json=payload)
    assert res.status_code == 201


def test_issue_description_at_exact_max_length_is_accepted(client, valid_service_payload):
    payload = dict(valid_service_payload)
    payload["issue_description"] = "A" * 1000
    res = client.post("/services", json=payload)
    assert res.status_code == 201


def test_appointment_date_at_exact_minimum_boundary_is_accepted(client, valid_service_payload):
    payload = dict(valid_service_payload)
    payload["appointment_date"] = "2000-01-01T00:00:00"
    res = client.post("/services", json=payload)
    assert res.status_code == 201


def test_appointment_date_at_exact_maximum_boundary_is_accepted(client, valid_service_payload):
    payload = dict(valid_service_payload)
    max_date = datetime(datetime.now().year + 2, 12, 31).isoformat()
    payload["appointment_date"] = max_date
    res = client.post("/services", json=payload)
    assert res.status_code == 201


def test_multiple_services_for_same_vehicle_different_dates_allowed(
    client, valid_service_payload
):
    """The booking-conflict rule only blocks the SAME exact appointment
    date/time; a second, different appointment for the same vehicle
    should succeed."""
    first_payload = dict(valid_service_payload)
    res1 = client.post("/services", json=first_payload)
    assert res1.status_code == 201

    second_payload = dict(valid_service_payload)
    second_payload["appointment_date"] = "2027-04-20T09:00:00"
    second_payload["service_type"] = "TYRE_SERVICE"
    res2 = client.post("/services", json=second_payload)
    assert res2.status_code == 201

    vehicles = client.get("/vehicles").json()
    assert len(vehicles) == 1  # same vehicle, not duplicated

    services = client.get("/services").json()
    assert len(services) == 2


def test_repeated_status_transition_calls_are_idempotently_rejected(
    client, valid_service_payload
):
    """Calling the same valid transition twice: the second call finds the
    service already past that state, so it must be rejected, not silently
    re-applied."""
    created = client.post("/services", json=valid_service_payload).json()
    service_id = created["id"]

    first = client.patch(f"/services/{service_id}/status", json={"status": "INSPECTION"})
    assert first.status_code == 200

    second = client.patch(f"/services/{service_id}/status", json={"status": "INSPECTION"})
    assert second.status_code == 409


def test_service_type_is_case_sensitive_enum(client, valid_service_payload):
    """Lowercase variants of a valid enum value should NOT be silently
    accepted - the enum values are uppercase and Pydantic enum matching
    is case-sensitive by default."""
    payload = dict(valid_service_payload)
    payload["service_type"] = "oil_change"
    res = client.post("/services", json=payload)
    assert res.status_code == 422
