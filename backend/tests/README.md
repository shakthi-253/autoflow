# AutoFlow Backend Test Suite

## Structure

```
tests/
├── conftest.py                    # isolated per-test SQLite DB + TestClient fixture
├── api/
│   ├── test_vehicles.py           # normal paths - /vehicles
│   ├── test_services.py           # normal paths - /services, dashboard, happy path
│   ├── test_status_transitions.py # business rules - every valid/invalid transition
│   ├── test_validation.py         # invalid inputs - required/format/length/type
│   ├── test_edge_cases.py         # boundary values, empty state, repeated ops
│   └── test_booking_conflict.py   # booking-conflict rule
└── README.md
```

## Isolation

Every test function gets a brand-new, empty SQLite database (a temp file
under pytest's `tmp_path`), wired in via FastAPI's `get_db` dependency
override. No test depends on data from another test or from a
developer's real `autoflow.db`. Order-independence is enforced by
`pytest-randomly`, which randomizes test order on every run.

## Running

From `backend/`, with the virtual environment set up:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

Run a single file or test:

```bash
pytest tests/api/test_status_transitions.py
pytest tests/api/test_status_transitions.py::test_valid_transition_succeeds
```

## What's covered

- **Normal paths**: creating vehicles/services, listing, retrieval by ID,
  the full BOOKED→INSPECTION→REPAIR→COMPLETED happy path, cancellation,
  dashboard stats reflecting state changes.
- **Business rules**: all 5 documented valid transitions and all 7
  documented invalid transitions (plus a few implied invalid ones, e.g.
  a status transitioning to itself), each checked for the correct HTTP
  code, error body shape, and that the service's actual status is
  unchanged after a rejection.
- **Invalid inputs**: every required field missing, empty strings,
  invalid formats (registration number, contact number, service type,
  date), over-length strings, malformed JSON, wrong ID types.
- **Edge cases**: exact boundary values for every length/format
  validator (both the shortest/longest *valid* values), empty-database
  dashboard/list responses, nonexistent/zero/negative IDs, repeated
  identical status updates, multiple services for the same vehicle on
  different dates.
- **Booking conflict**: the actual implemented rule (exact appointment
  timestamp match + active status only), including that COMPLETED/
  CANCELLED services don't block a rebooking, and that a rejected
  booking doesn't leave an extra row in the database.
