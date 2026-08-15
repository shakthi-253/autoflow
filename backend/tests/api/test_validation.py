"""
Invalid-input tests for POST /services, derived directly from the
validators in app/schemas/vehicle.py and app/schemas/service.py:

- registration_number: ^[A-Za-z0-9][A-Za-z0-9\\- ]{3,15}[A-Za-z0-9]$ (5-17 chars)
- contact_number: ^\\+?\\d{7,15}$ (7-15 digits, optional leading +)
- owner_name / vehicle_model: required, max 100 chars
- issue_description: required, max 1000 chars
- appointment_date: 2000-01-01 .. Dec 31 of (this year + 2)
- service_type: must be one of the 5 defined enum values

All of these are enforced server-side via Pydantic, which our global
RequestValidationError handler turns into a 422 with
{"error": "VALIDATION_ERROR", "message": ..., "details": {"errors": [...]}}.
"""
import pytest

REQUIRED_FIELDS = [
    "registration_number",
    "owner_name",
    "contact_number",
    "vehicle_model",
    "service_type",
    "issue_description",
    "appointment_date",
]


@pytest.mark.parametrize("missing_field", REQUIRED_FIELDS)
def test_missing_required_field_returns_422(client, valid_service_payload, missing_field):
    payload = dict(valid_service_payload)
    del payload[missing_field]

    res = client.post("/services", json=payload)
    assert res.status_code == 422
    body = res.json()
    assert body["error"] == "VALIDATION_ERROR"
    fields = [e["field"] for e in body["details"]["errors"]]
    assert missing_field in fields


@pytest.mark.parametrize(
    "field,empty_value",
    [
        ("registration_number", ""),
        ("owner_name", ""),
        ("contact_number", ""),
        ("vehicle_model", ""),
        ("issue_description", ""),
    ],
)
def test_empty_string_field_returns_422(client, valid_service_payload, field, empty_value):
    payload = dict(valid_service_payload)
    payload[field] = empty_value
    res = client.post("/services", json=payload)
    assert res.status_code == 422


def test_invalid_service_type_returns_422(client, valid_service_payload):
    payload = dict(valid_service_payload)
    payload["service_type"] = "NOT_A_REAL_TYPE"
    res = client.post("/services", json=payload)
    assert res.status_code == 422
    body = res.json()
    assert body["error"] == "VALIDATION_ERROR"


def test_invalid_date_format_returns_422(client, valid_service_payload):
    payload = dict(valid_service_payload)
    payload["appointment_date"] = "not-a-date"
    res = client.post("/services", json=payload)
    assert res.status_code == 422


@pytest.mark.parametrize(
    "bad_number",
    [
        "abcdefg",       # letters, not digits
        "123-456-7890",  # dashes not allowed by the pattern
        "12345",         # only 5 digits, below the 7-digit minimum
        "1234567890123456",  # 16 digits, above the 15-digit maximum
        "++911234567890",    # malformed leading symbol
    ],
)
def test_invalid_contact_number_format_returns_422(client, valid_service_payload, bad_number):
    payload = dict(valid_service_payload)
    payload["contact_number"] = bad_number
    res = client.post("/services", json=payload)
    assert res.status_code == 422


@pytest.mark.parametrize(
    "bad_reg",
    [
        "AB1",       # 3 chars, below 5-char minimum
        "A" * 21,    # far above the max
        "TN 09 AB!", # '!' is not an allowed character
    ],
)
def test_invalid_registration_number_returns_422(client, valid_service_payload, bad_reg):
    payload = dict(valid_service_payload)
    payload["registration_number"] = bad_reg
    res = client.post("/services", json=payload)
    assert res.status_code == 422


def test_owner_name_over_max_length_returns_422(client, valid_service_payload):
    payload = dict(valid_service_payload)
    payload["owner_name"] = "A" * 101
    res = client.post("/services", json=payload)
    assert res.status_code == 422


def test_vehicle_model_over_max_length_returns_422(client, valid_service_payload):
    payload = dict(valid_service_payload)
    payload["vehicle_model"] = "A" * 101
    res = client.post("/services", json=payload)
    assert res.status_code == 422


def test_issue_description_over_max_length_returns_422(client, valid_service_payload):
    payload = dict(valid_service_payload)
    payload["issue_description"] = "A" * 1001
    res = client.post("/services", json=payload)
    assert res.status_code == 422


def test_appointment_date_before_minimum_returns_422(client, valid_service_payload):
    payload = dict(valid_service_payload)
    payload["appointment_date"] = "1999-12-31T00:00:00"
    res = client.post("/services", json=payload)
    assert res.status_code == 422


def test_appointment_date_far_in_future_returns_422(client, valid_service_payload):
    from datetime import datetime

    payload = dict(valid_service_payload)
    too_far = datetime(datetime.now().year + 3, 1, 1).isoformat()
    payload["appointment_date"] = too_far
    res = client.post("/services", json=payload)
    assert res.status_code == 422


def test_malformed_json_body_returns_422(client):
    res = client.post(
        "/services",
        content="{not valid json",
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code == 422


def test_get_service_with_non_integer_id_returns_422(client):
    res = client.get("/services/not-an-id")
    assert res.status_code == 422


def test_invalid_data_type_for_field_returns_422(client, valid_service_payload):
    """registration_number as a number instead of a string."""
    payload = dict(valid_service_payload)
    payload["registration_number"] = 12345
    res = client.post("/services", json=payload)
    assert res.status_code == 422


def test_invalid_request_does_not_create_a_service(client, valid_service_payload):
    """A rejected request must not leave a partial/invalid record behind."""
    payload = dict(valid_service_payload)
    payload["service_type"] = "NOT_A_REAL_TYPE"
    client.post("/services", json=payload)

    res = client.get("/services")
    assert res.json() == []

    dash = client.get("/services/stats/dashboard").json()
    assert dash["total_services"] == 0
