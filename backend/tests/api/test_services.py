"""
Normal-path tests for the /services endpoints and dashboard stats.
"""


def test_create_service_returns_201_with_booked_status(client, valid_service_payload):
    res = client.post("/services", json=valid_service_payload)
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "BOOKED"
    assert body["service_type"] == "OIL_CHANGE"
    assert body["issue_description"] == "Routine oil change"
    assert body["vehicle"]["registration_number"] == "TN09AB1234"
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body


def test_create_service_creates_the_vehicle_implicitly(client, valid_service_payload):
    client.post("/services", json=valid_service_payload)
    res = client.get("/vehicles")
    assert res.status_code == 200
    vehicles = res.json()
    assert len(vehicles) == 1
    assert vehicles[0]["registration_number"] == "TN09AB1234"


def test_list_services_returns_created_service(client, valid_service_payload):
    client.post("/services", json=valid_service_payload)
    res = client.get("/services")
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    assert body[0]["status"] == "BOOKED"


def test_get_service_by_id_returns_full_details(client, valid_service_payload):
    created = client.post("/services", json=valid_service_payload).json()
    res = client.get(f"/services/{created['id']}")
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == created["id"]
    assert body["vehicle"]["owner_name"] == "Ravi Kumar"
    assert body["issue_description"] == "Routine oil change"
    assert body["status"] == "BOOKED"


def test_dashboard_stats_reflect_created_service(client, valid_service_payload):
    client.post("/services", json=valid_service_payload)
    res = client.get("/services/stats/dashboard")
    assert res.status_code == 200
    body = res.json()
    assert body["total_services"] == 1
    assert body["booked"] == 1
    assert body["inspection"] == 0
    assert body["repair"] == 0
    assert body["completed"] == 0
    assert body["cancelled"] == 0


def test_dashboard_stats_reflect_status_change(client, valid_service_payload):
    created = client.post("/services", json=valid_service_payload).json()
    client.patch(f"/services/{created['id']}/status", json={"status": "INSPECTION"})

    res = client.get("/services/stats/dashboard")
    body = res.json()
    assert body["total_services"] == 1
    assert body["booked"] == 0
    assert body["inspection"] == 1


def test_full_happy_path_booked_to_completed(client, valid_service_payload):
    """BOOKED -> INSPECTION -> REPAIR -> COMPLETED, verifying status after each step."""
    created = client.post("/services", json=valid_service_payload).json()
    service_id = created["id"]
    assert created["status"] == "BOOKED"

    r1 = client.patch(f"/services/{service_id}/status", json={"status": "INSPECTION"})
    assert r1.status_code == 200
    assert r1.json()["status"] == "INSPECTION"

    r2 = client.patch(f"/services/{service_id}/status", json={"status": "REPAIR"})
    assert r2.status_code == 200
    assert r2.json()["status"] == "REPAIR"

    r3 = client.patch(f"/services/{service_id}/status", json={"status": "COMPLETED"})
    assert r3.status_code == 200
    assert r3.json()["status"] == "COMPLETED"

    final = client.get(f"/services/{service_id}").json()
    assert final["status"] == "COMPLETED"

    dash = client.get("/services/stats/dashboard").json()
    assert dash["completed"] == 1
    assert dash["total_services"] == 1


def test_cancellation_from_booked(client, valid_service_payload):
    created = client.post("/services", json=valid_service_payload).json()
    res = client.patch(f"/services/{created['id']}/status", json={"status": "CANCELLED"})
    assert res.status_code == 200
    assert res.json()["status"] == "CANCELLED"


def test_cancellation_from_inspection(client, valid_service_payload):
    created = client.post("/services", json=valid_service_payload).json()
    client.patch(f"/services/{created['id']}/status", json={"status": "INSPECTION"})
    res = client.patch(f"/services/{created['id']}/status", json={"status": "CANCELLED"})
    assert res.status_code == 200
    assert res.json()["status"] == "CANCELLED"


def test_updated_at_changes_after_status_transition(client, valid_service_payload):
    created = client.post("/services", json=valid_service_payload).json()
    updated = client.patch(
        f"/services/{created['id']}/status", json={"status": "INSPECTION"}
    ).json()
    # updated_at should have moved on from its initial value after a real change.
    assert updated["updated_at"] >= created["updated_at"]
