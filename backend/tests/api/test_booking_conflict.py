"""
Tests for the booking-conflict rule, derived directly from
app/services/workflow.py::check_booking_conflict:

A vehicle cannot have a SECOND service with the EXACT SAME
appointment_date while an existing service for that vehicle at that
timestamp is in an ACTIVE status (BOOKED, INSPECTION, or REPAIR).
COMPLETED and CANCELLED are not active, so they don't block a rebooking
at the same timestamp.
"""


def _base_payload(reg="TN22CD5678", appt="2027-05-10T09:00:00"):
    return {
        "registration_number": reg,
        "owner_name": "Anita",
        "contact_number": "9123456780",
        "vehicle_model": "Maruti Swift",
        "service_type": "BRAKE_SERVICE",
        "issue_description": "Squeaky brakes",
        "appointment_date": appt,
    }


def test_first_booking_succeeds(client):
    res = client.post("/services", json=_base_payload())
    assert res.status_code == 201
    assert res.json()["status"] == "BOOKED"


def test_conflicting_booking_same_vehicle_same_timestamp_is_rejected(client):
    client.post("/services", json=_base_payload())

    conflict_payload = _base_payload()
    conflict_payload["service_type"] = "TYRE_SERVICE"
    conflict_payload["issue_description"] = "Tyre check"
    res = client.post("/services", json=conflict_payload)

    assert res.status_code == 409
    body = res.json()
    assert body["error"] == "BOOKING_CONFLICT"
    assert "conflicting_service_id" in body["details"]


def test_conflicting_booking_does_not_create_a_second_service(client):
    """The database must not be left inconsistent after a rejected booking:
    exactly one service should exist, not two."""
    client.post("/services", json=_base_payload())
    client.post("/services", json=_base_payload())  # rejected

    services = client.get("/services").json()
    assert len(services) == 1


def test_non_conflicting_booking_different_timestamp_is_allowed(client):
    client.post("/services", json=_base_payload(appt="2027-05-10T09:00:00"))

    res = client.post("/services", json=_base_payload(appt="2027-05-10T09:01:00"))
    assert res.status_code == 201

    services = client.get("/services").json()
    assert len(services) == 2


def test_non_conflicting_booking_different_vehicle_same_timestamp_is_allowed(client):
    client.post("/services", json=_base_payload(reg="TN22CD5678"))

    res = client.post("/services", json=_base_payload(reg="TN22CD9999"))
    assert res.status_code == 201


def test_booking_same_timestamp_allowed_after_previous_service_completed(client):
    """A COMPLETED service is no longer 'active', so it should not block a
    new booking at the same timestamp for the same vehicle."""
    created = client.post("/services", json=_base_payload()).json()
    service_id = created["id"]
    client.patch(f"/services/{service_id}/status", json={"status": "INSPECTION"})
    client.patch(f"/services/{service_id}/status", json={"status": "REPAIR"})
    client.patch(f"/services/{service_id}/status", json={"status": "COMPLETED"})

    res = client.post("/services", json=_base_payload())
    assert res.status_code == 201


def test_booking_same_timestamp_allowed_after_previous_service_cancelled(client):
    """A CANCELLED service is likewise not 'active' and should not block a
    rebooking at the same timestamp."""
    created = client.post("/services", json=_base_payload()).json()
    service_id = created["id"]
    client.patch(f"/services/{service_id}/status", json={"status": "CANCELLED"})

    res = client.post("/services", json=_base_payload())
    assert res.status_code == 201


def test_conflict_blocked_while_existing_service_in_inspection(client):
    """The conflict check should apply while the earlier booking is in
    INSPECTION, not just BOOKED."""
    created = client.post("/services", json=_base_payload()).json()
    client.patch(f"/services/{created['id']}/status", json={"status": "INSPECTION"})

    res = client.post("/services", json=_base_payload())
    assert res.status_code == 409


def test_conflict_blocked_while_existing_service_in_repair(client):
    """The conflict check should apply while the earlier booking is in
    REPAIR too."""
    created = client.post("/services", json=_base_payload()).json()
    service_id = created["id"]
    client.patch(f"/services/{service_id}/status", json={"status": "INSPECTION"})
    client.patch(f"/services/{service_id}/status", json={"status": "REPAIR"})

    res = client.post("/services", json=_base_payload())
    assert res.status_code == 409
