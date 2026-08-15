"""
Shared pytest fixtures for the AutoFlow backend test suite.

Isolation strategy: every test function gets its own throwaway SQLite
file (via pytest's tmp_path), with the FastAPI `get_db` dependency
overridden to use it. This means tests never touch a developer's real
autoflow.db, never depend on data left over from another test, and can
run in any order.

We set DATABASE_URL before importing the app so the app's own
module-level engine also points at an isolated file rather than the
default ./autoflow.db - this only matters for the startup event's
`create_all` call, since every actual request in a test uses the
per-test override below.
"""
import gc
import os
import time
import uuid

os.environ.setdefault("DATABASE_URL", f"sqlite:///./_test_startup_{uuid.uuid4().hex}.db")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db, DATABASE_URL
from app.database import engine as startup_engine


@pytest.fixture(scope="session", autouse=True)
def _cleanup_startup_db():
    """
    Remove the throwaway file the app's startup event creates tables on
    (app.database reads DATABASE_URL at import time; every real test
    request uses the per-test override below instead of this file).

    On Windows, SQLite keeps an OS-level lock on the file for as long as
    any connection from the pool is open. `app.database.engine` is a
    module-level object that's never explicitly disposed elsewhere (the
    app has no shutdown handler that does it), so its pooled connection
    can still be holding the file open at this point - harmless on
    Linux/macOS, but a PermissionError on Windows. Disposing the engine
    closes those pooled connections and releases the OS lock before we
    try to delete the file.
    """
    yield
    startup_engine.dispose()
    gc.collect()  # ensure any connection objects pending GC are released too

    if DATABASE_URL.startswith("sqlite:///./"):
        path = DATABASE_URL.replace("sqlite:///./", "", 1)
        if os.path.exists(path):
            # The OS may take a moment to actually release the file handle
            # after dispose() on Windows; retry briefly instead of failing
            # outright on a timing race.
            last_error = None
            for attempt in range(5):
                try:
                    os.remove(path)
                    break
                except PermissionError as exc:
                    last_error = exc
                    time.sleep(0.2)
            else:
                raise last_error


@pytest.fixture()
def client(tmp_path):
    """A TestClient backed by a fresh, isolated SQLite database."""
    db_path = tmp_path / "test_autoflow.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture()
def valid_service_payload():
    """A minimal, valid POST /services payload. Tests override individual
    fields as needed rather than duplicating the whole literal each time."""
    return {
        "registration_number": "TN09AB1234",
        "owner_name": "Ravi Kumar",
        "contact_number": "9876543210",
        "vehicle_model": "Honda City",
        "service_type": "OIL_CHANGE",
        "issue_description": "Routine oil change",
        "appointment_date": "2027-03-15T10:00:00",
    }


def create_service(client, payload_overrides=None, base_payload=None):
    """Helper: POST a service and return the parsed response body."""
    payload = dict(base_payload or {
        "registration_number": "TN09AB1234",
        "owner_name": "Ravi Kumar",
        "contact_number": "9876543210",
        "vehicle_model": "Honda City",
        "service_type": "OIL_CHANGE",
        "issue_description": "Routine oil change",
        "appointment_date": "2027-03-15T10:00:00",
    })
    if payload_overrides:
        payload.update(payload_overrides)
    res = client.post("/services", json=payload)
    return res
