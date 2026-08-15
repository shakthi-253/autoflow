"""
Normal-path tests for the /vehicles endpoints.
"""


def test_create_vehicle_returns_201_and_persisted_fields(client):
    payload = {
        "registration_number": "TN09AB1234",
        "owner_name": "Ravi Kumar",
        "contact_number": "9876543210",
        "vehicle_model": "Honda City",
    }
    res = client.post("/vehicles", json=payload)
    assert res.status_code == 201
    body = res.json()
    assert body["registration_number"] == "TN09AB1234"
    assert body["owner_name"] == "Ravi Kumar"
    assert body["contact_number"] == "9876543210"
    assert body["vehicle_model"] == "Honda City"
    assert "id" in body
    assert "created_at" in body


def test_registration_number_is_normalized_to_uppercase(client):
    res = client.post(
        "/vehicles",
        json={
            "registration_number": "tn09ab1234",
            "owner_name": "Ravi Kumar",
            "contact_number": "9876543210",
            "vehicle_model": "Honda City",
        },
    )
    assert res.status_code == 201
    assert res.json()["registration_number"] == "TN09AB1234"


def test_list_vehicles_returns_created_vehicle(client):
    client.post(
        "/vehicles",
        json={
            "registration_number": "TN09AB1234",
            "owner_name": "Ravi Kumar",
            "contact_number": "9876543210",
            "vehicle_model": "Honda City",
        },
    )
    res = client.get("/vehicles")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    assert body[0]["registration_number"] == "TN09AB1234"


def test_get_vehicle_by_id(client):
    create_res = client.post(
        "/vehicles",
        json={
            "registration_number": "TN09AB1234",
            "owner_name": "Ravi Kumar",
            "contact_number": "9876543210",
            "vehicle_model": "Honda City",
        },
    )
    vehicle_id = create_res.json()["id"]

    res = client.get(f"/vehicles/{vehicle_id}")
    assert res.status_code == 200
    assert res.json()["id"] == vehicle_id


def test_creating_vehicle_twice_with_same_registration_returns_existing(client):
    """
    The router looks up by registration_number first and returns the
    existing record rather than erroring or creating a duplicate - this
    documents that actual (idempotent) behavior.
    """
    payload = {
        "registration_number": "TN09AB1234",
        "owner_name": "Ravi Kumar",
        "contact_number": "9876543210",
        "vehicle_model": "Honda City",
    }
    first = client.post("/vehicles", json=payload)
    second = client.post("/vehicles", json=payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]

    res = client.get("/vehicles")
    assert len(res.json()) == 1
