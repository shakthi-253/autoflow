"""
Tests for the SERVICE PRIORITY CLASSIFICATION feature.

Split into two layers:
- Unit tests directly against app.services.priority.calculate_priority,
  covering the exact keyword rules from the spec (case-insensitivity,
  word-boundary matching, HIGH-before-MEDIUM precedence, and the LOW
  fallback).
- API-level tests confirming the priority is actually computed and
  returned end-to-end through POST/GET /services, and that it cannot be
  set directly by the client.
"""
import pytest

from app.models.service import ServicePriority
from app.services.priority import calculate_priority


# ---------------------------------------------------------------------
# Unit tests: calculate_priority()
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "description",
    [
        "Engine failure, vehicle won't start",
        "Brake problem",
        "brake failure while driving",
        "BRAKE",  # bare keyword, uppercase
        "battery dead this morning",
        "Vehicle will not start at all",
        "Car is overheating on the highway",
        "General engine problem noticed",
    ],
)
def test_high_priority_keywords_are_detected(description):
    assert calculate_priority(description) == ServicePriority.HIGH


@pytest.mark.parametrize(
    "description",
    [
        "AC not cooling properly",
        "Tyre replacement",
        "tire looks worn",
        "air conditioning making noise",
        "electrical fault in dashboard",
        "suspension feels loose",
        "engine cooling system check",  # "cooling" is MEDIUM
    ],
)
def test_medium_priority_keywords_are_detected(description):
    assert calculate_priority(description) == ServicePriority.MEDIUM


@pytest.mark.parametrize(
    "description",
    [
        "Oil change",
        "General service",
        "Routine maintenance check",
        "Wiper blades need replacing",
        "Interior cleaning requested",
    ],
)
def test_low_priority_is_the_fallback(description):
    assert calculate_priority(description) == ServicePriority.LOW


def test_matching_is_case_insensitive():
    assert calculate_priority("ENGINE FAILURE") == ServicePriority.HIGH
    assert calculate_priority("Ac Not Cooling") == ServicePriority.MEDIUM
    assert calculate_priority("engine failure") == ServicePriority.HIGH


def test_high_takes_precedence_over_medium_when_both_present():
    # "brake" (HIGH) and "tyre" (MEDIUM) both appear; HIGH must win.
    assert calculate_priority("Brake and tyre check requested") == ServicePriority.HIGH


def test_word_boundary_avoids_false_positive_substring_match():
    """
    "AC" must match as a standalone word, not as a substring of an
    unrelated word - e.g. "space" or "replace" should NOT trigger MEDIUM
    just because they contain the letters "ac".
    """
    assert calculate_priority("Need more space in the trunk") == ServicePriority.LOW
    assert calculate_priority("Replace the wiper blades") == ServicePriority.LOW


# ---------------------------------------------------------------------
# API-level tests
# ---------------------------------------------------------------------


def _payload(issue_description, **overrides):
    payload = {
        "registration_number": "TN09AB1234",
        "owner_name": "Ravi Kumar",
        "contact_number": "9876543210",
        "vehicle_model": "Honda City",
        "service_type": "GENERAL_SERVICE",
        "issue_description": issue_description,
        "appointment_date": "2027-03-15T10:00:00",
    }
    payload.update(overrides)
    return payload


def test_create_service_response_includes_derived_priority(client):
    res = client.post("/services", json=_payload("Engine failure, vehicle won't start"))
    assert res.status_code == 201
    assert res.json()["priority"] == "HIGH"


def test_get_service_returns_priority(client):
    created = client.post("/services", json=_payload("AC not cooling properly")).json()
    res = client.get(f"/services/{created['id']}")
    assert res.status_code == 200
    assert res.json()["priority"] == "MEDIUM"


def test_list_services_includes_priority_for_each_service(client):
    client.post("/services", json=_payload("Oil change"))
    res = client.get("/services")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    assert body[0]["priority"] == "LOW"


def test_priority_field_in_request_body_is_ignored_not_user_settable(client):
    """
    The client cannot set priority directly - even if a 'priority' field
    is included in the POST body, the server-computed value (derived
    from issue_description) must win.
    """
    payload = _payload("Oil change", priority="HIGH")
    res = client.post("/services", json=payload)
    assert res.status_code == 201
    # issue_description is "Oil change" -> LOW, regardless of the
    # attempted client-supplied "HIGH" override.
    assert res.json()["priority"] == "LOW"


def test_priority_survives_status_transitions_unchanged(client):
    """Priority is derived once at creation and must not change as the
    service moves through the workflow."""
    created = client.post("/services", json=_payload("Brake problem")).json()
    assert created["priority"] == "HIGH"

    updated = client.patch(
        f"/services/{created['id']}/status", json={"status": "INSPECTION"}
    ).json()
    assert updated["priority"] == "HIGH"
