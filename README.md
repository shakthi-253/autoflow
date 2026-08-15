# AutoFlow — Vehicle Service & Repair Workflow System

**Status: Stage 3 (AI Change Loop) complete.** Application built,
automated test suite generated and executed with a deliberate red run,
and a new feature (Service Priority Classification) implemented and
verified through an AI-assisted implement → test → diagnose → correct
loop. Stage 4 documentation (this set) is in progress.

## AI Tools Used

- **Claude (Anthropic)** — used for: building the backend and frontend
  (Stage 1); analyzing the existing codebase and generating/executing
  the pytest + Playwright test suite, including the deliberate
  backend red run (Stage 2); the initial implementation of Service
  Priority Classification (Stage 3); and drafting this documentation
  set (Stage 4).
- **ChatGPT** — used during Stage 3 to continue the AI change loop
  after Claude's usage limit was reached mid-workflow. ChatGPT
  diagnosed a real Playwright regression the initial implementation
  introduced, identified its root cause, guided the application fix,
  and verified the corrected test results. See
  [`docs/ai-change-loop.md`](docs/ai-change-loop.md) for the full,
  attributed record of which tool did what.

## Documentation Index

- [`docs/architecture.md`](docs/architecture.md) — components, data flow, technology choices
- [`docs/design.md`](docs/design.md) — data model, key flows, API design, error handling
- [`docs/user-guide.md`](docs/user-guide.md) — how to use AutoFlow (no technical background needed)
- [`docs/ai-testing-log.md`](docs/ai-testing-log.md) — Stage 2 AI test-generation record
- [`docs/ai-change-loop.md`](docs/ai-change-loop.md) — Stage 3 AI change-loop record, including the Playwright regression and fix
- [`docs/testing.md`](docs/testing.md) — Stage 2 deliberate backend red-run demonstration, plus current final test counts

## What is AutoFlow?

AutoFlow is a web application for a vehicle service center to manage a
vehicle's service journey from booking through inspection, repair, and
completion. It enforces valid workflow transitions on the backend, so
the state of a service can never be corrupted regardless of what the
frontend sends.

## Problem Statement

A service center needs a simple, reliable way to track vehicles moving
through a fixed workflow, prevent invalid state changes (e.g. jumping
straight from "Booked" to "Completed"), avoid double-booking the same
vehicle for the same time slot, and surface which jobs are urgent
without relying on staff to manually triage every ticket.

## Core Functionality

### Service workflow

```
BOOKED → INSPECTION → REPAIR → COMPLETED
   ↓          ↓
CANCELLED  CANCELLED
```

Valid transitions:
- `BOOKED → INSPECTION`, `BOOKED → CANCELLED`
- `INSPECTION → REPAIR`, `INSPECTION → CANCELLED`
- `REPAIR → COMPLETED`

Every other transition (e.g. `BOOKED → REPAIR`, `COMPLETED → REPAIR`) is
rejected by the backend with a `409` error, independent of the frontend.

### Service Priority Classification (added in Stage 3)

Every service is automatically labeled `HIGH`, `MEDIUM`, or `LOW`,
derived from case-insensitive, whole-word keyword matches against its
`issue_description`:

| Priority | Keywords |
|---|---|
| HIGH | engine failure, engine problem, brake failure, brake problem, brake, battery dead, vehicle won't start, vehicle will not start, overheating |
| MEDIUM | AC, air conditioning, cooling, electrical, tyre, tire, suspension |
| LOW | everything else |

Priority is computed once, at creation, entirely server-side. It is
**not** a field on the create request — a client cannot set it
directly, even by including a `priority` value in the request body.
See `backend/app/services/priority.py`.

## Technology Stack

| Layer      | Technology                     |
|------------|---------------------------------|
| Frontend   | React + Vite                    |
| Backend    | Python + FastAPI                |
| Database   | SQLite + SQLAlchemy ORM         |
| Testing    | pytest (backend), Playwright (E2E) |
| API        | REST (JSON)                     |

## Architecture Overview

```
React + Vite SPA  ──HTTP/JSON──▶  FastAPI backend  ──SQLAlchemy──▶  SQLite
```

Business logic (workflow transitions, booking conflict, priority
classification) lives entirely in `backend/app/services/`, separate
from HTTP routing — the frontend can only suggest actions (e.g. which
buttons to show); the backend is the sole authority on what's actually
allowed. Full detail, diagrams, and rationale in
[`docs/architecture.md`](docs/architecture.md).

## Project Structure

```
autoflow/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, error handlers
│   │   ├── database.py        # SQLAlchemy engine/session
│   │   ├── models/            # Vehicle, Service ORM models + transition map
│   │   ├── schemas/           # Pydantic request/response validation
│   │   ├── routers/           # /vehicles, /services endpoints
│   │   └── services/          # workflow.py, priority.py (business rules), exceptions.py
│   ├── tests/                 # pytest suite (119 tests)
│   ├── requirements.txt
│   ├── requirements-dev.txt   # + pytest, httpx, pytest-randomly
│   ├── .env.example
│   └── venv/                  # created locally, not committed
│
├── frontend/
│   ├── src/
│   │   ├── api/client.js      # fetch wrapper for the backend API
│   │   ├── pages/             # Dashboard, CreateService, ServiceDetails
│   │   ├── components/        # StatusBadge, PriorityBadge, WorkflowStepper
│   │   ├── statusConfig.js    # shared status/priority label metadata
│   │   ├── App.jsx            # routes
│   │   └── index.css          # design system
│   ├── e2e/                   # Playwright spec files (9 tests)
│   ├── playwright.config.ts
│   ├── package.json
│   └── .env.example
│
├── docs/                      # architecture, design, user guide, AI logs
├── evidence/testing/          # captured terminal output from test runs
├── .env.example
├── .gitignore
└── README.md
```

## Prerequisites

- Python 3.10+
- Node.js 18+ and npm

## Installation & Setup

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

The default `.env` uses a local SQLite file (`autoflow.db`) and allows
CORS from `http://localhost:5173` (the Vite dev server). Edit `.env` if
you need different values — nothing is hardcoded in the source.

> **If you have a pre-existing local `autoflow.db` from before Stage 3:**
> delete it before starting the backend. The new `priority` column was
> added to the `Service` table, and this project has no migration
> tooling — `Base.metadata.create_all()` only creates missing tables,
> not missing columns on existing ones.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env
```

`.env` sets `VITE_API_URL=http://localhost:8000`, matching the backend's
default port.

## Running the Application

**Start the backend** (from `backend/`, with the venv activated):

```bash
uvicorn app.main:app --reload --port 8000
```

- API base URL: `http://localhost:8000`
- Interactive API docs: `http://localhost:8000/docs`
- Tables are created automatically on startup — no manual migration step.

**Start the frontend** (from `frontend/`, in a separate terminal):

```bash
npm run dev
```

- App: `http://localhost:5173`

## Running the Tests

**Backend** (from `backend/`, with the venv activated):

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Windows note: use `python -m pytest` rather than a bare `pytest` — this
ensures the venv's own Python (and its installed packages) is used
rather than a `pytest` on your system PATH.

**Frontend E2E** (from `frontend/`, needs Playwright's browser binary
installed once):

```bash
npm install
npx playwright install chromium
npx playwright test
```

This starts both the backend and the frontend dev server automatically using `playwright.config.ts`; you don't need either running beforehand.
## Using the Application

1. Open `http://localhost:5173`. The dashboard shows service counts by
   status and a table of all services, including each one's priority.
2. Click **+ New Service** to register a vehicle and book an appointment.
   Both the form and the backend validate every field (registration
   number format, contact number format, required fields, valid service
   type, valid date). Priority is calculated automatically from the
   issue description — there is no priority field to fill in.
3. Click any row to open the service's detail page. The page shows a
   workflow stepper, the service's priority, and only the action
   buttons that are valid for the current status (e.g. a `BOOKED`
   service shows "Start Inspection" and "Cancel").
4. Booking the same vehicle for the same appointment date/time while it
   already has an active (non-terminal) service is rejected with a
   clear error.

## API Endpoints

| Method | Path                        | Description                          |
|--------|-----------------------------|---------------------------------------|
| POST   | `/vehicles`                 | Create a vehicle                      |
| GET    | `/vehicles`                 | List vehicles                         |
| GET    | `/vehicles/{id}`            | Get a vehicle                         |
| POST   | `/services`                 | Create a service (finds/creates vehicle, computes priority) |
| GET    | `/services`                 | List services                         |
| GET    | `/services/{id}`            | Get a service                         |
| PATCH  | `/services/{id}/status`     | Change a service's status             |
| GET    | `/services/stats/dashboard` | Dashboard counts by status            |

All errors return a structured body: `{"error": "CODE", "message": "...", "details": {...}}`.

## Database Schema

**Vehicle**: `id, registration_number (unique), owner_name, contact_number, vehicle_model, created_at`

**Service**: `id, vehicle_id (FK), service_type, issue_description, appointment_date, status, priority, created_at, updated_at`

A vehicle can have many services; vehicle info is stored once and
referenced by `vehicle_id`, not duplicated per service. `priority` is
derived server-side from `issue_description` at creation time — see
Business Rules below — and is never accepted as client input.

## Business Rules Implemented

1. **Workflow transitions** — enforced in `app/services/workflow.py` and
   checked by the `PATCH /services/{id}/status` endpoint. The frontend
   only shows relevant buttons; the backend independently rejects any
   invalid transition even if called directly.
2. **Booking conflict rule** — a vehicle cannot have two active
   (`BOOKED`/`INSPECTION`/`REPAIR`) services for the same appointment
   date/time.
3. **Validation** — required fields, format checks (registration number,
   contact number), max lengths, valid enum values, and a reasonable date
   range are all validated on the backend regardless of what the frontend
   sends.
4. **Priority classification** — every service is automatically
   labeled `HIGH`, `MEDIUM`, or `LOW`, derived from keyword matches in
   `issue_description` (see `app/services/priority.py`). Computed once
   at creation; not user-editable; a `priority` value sent by the
   client in the request body is ignored in favor of the computed one.

## Testing

### Stage 2 — AI-generated test automation

Claude analyzed the actual implementation (not assumptions) to derive
test cases, then generated and executed a pytest suite covering normal
paths, edge cases, invalid inputs, business rules, and the
booking-conflict rule, plus a Playwright E2E suite. A **deliberate red
run** was performed against the backend: `ALLOWED_TRANSITIONS` was
temporarily modified to incorrectly allow `BOOKED → COMPLETED`, which
the test suite caught immediately (`1 failed, 90 passed`), before the
application was restored to green. Full record in
[`docs/ai-testing-log.md`](docs/ai-testing-log.md) and
[`docs/testing.md`](docs/testing.md).

### Stage 3 — AI change loop

Claude implemented Service Priority Classification and ran the existing
backend suite, which passed immediately (`119 passed`). The Playwright
suite, however, initially returned `7 passed, 2 failed`: the new
`PriorityBadge` component reused the existing `.status-badge` CSS
class, so a page could contain two elements matching that selector
(status and priority), causing a Playwright strict-mode violation on
tests that expected `.status-badge` to uniquely identify the service
status. ChatGPT (Claude having reached its usage limit) diagnosed this
root cause and guided the fix: `PriorityBadge` now uses a distinct
`.priority-badge` class, leaving `.status-badge` exclusively for
service status. Re-running both suites after the fix produced
`119 passed` (backend) and `9 passed` (Playwright). No test files were
modified to reach this result — only the application's CSS class
usage. Full record in
[`docs/ai-change-loop.md`](docs/ai-change-loop.md).

### Final test results

| Suite | Result |
|---|---|
| Backend/API (`pytest`) | **119 passed, 2 warnings** |
| Playwright E2E (`npx playwright test`) | **9 passed** |

These are two separately-run suites, not one combined test command —
report them as such (119 + 9), not as a single merged figure.

## What Was Manually Verified

Verified against a running backend + frontend:

- Creating a service produces a `BOOKED` record with the correct
  derived priority, and appears on the dashboard and in the service
  list.
- Full happy path: `BOOKED → INSPECTION → REPAIR → COMPLETED`, each step
  returning `200` and the correct new status.
- Cancellation from `BOOKED` and from `INSPECTION`.
- Every listed invalid transition (`BOOKED → REPAIR`, `REPAIR → CANCELLED`,
  `COMPLETED → REPAIR`, etc.) is rejected with `409 INVALID_TRANSITION`.
- Missing required field, invalid service type, and invalid contact
  number are rejected with `422 VALIDATION_ERROR` and field-level
  messages.
- Booking the same vehicle for the same appointment date/time twice is
  rejected with `409 BOOKING_CONFLICT`.
- Unknown vehicle/service IDs return `404` with structured errors.
- CORS is confirmed working between the Vite dev server
  (`http://localhost:5173`) and the FastAPI backend
  (`http://localhost:8000`).
- `npm run build` completes with no errors.
- Priority is correctly derived for representative issue descriptions
  across all three levels, is not overridable by client input, and
  survives status transitions unchanged.

## Known Limitations

- Authentication is not implemented. The assessment states auth is only
  needed if genuinely relevant; a single-service-center internal tool
  like this typically sits behind a company network or a separate
  auth layer, so it wasn't added at this stage. This can be revisited if
  the interview scenario calls for multi-user access control.
- The booking-conflict rule matches on exact appointment timestamp, not a
  time-range/duration overlap — kept intentionally simple and explainable,
  as instructed.
- No pagination on `GET /services` or `GET /vehicles` — acceptable at
  this data scale; would be added if the dataset grows.
- No migration tooling (e.g. Alembic) is used — tables are created via
  `Base.metadata.create_all()`, which only creates missing tables, not
  missing columns on existing ones. The `priority` column added for
  Service Priority Classification (Stage 3) means a pre-existing local
  `autoflow.db` from before that change must be deleted (or the schema
  migrated by hand) before starting the backend again.
- Priority is calculated once at creation and does not update if the
  issue description were ever edited after the fact — not a concern
  today since there is no edit-issue-description endpoint, but worth
  noting if one is added later.

## Future Improvements

- Add pagination to list endpoints as data volume grows.
- Add a proper migration tool (Alembic) instead of relying on
  `create_all()`.
- Consider an auth layer if AutoFlow is ever exposed outside a single
  trusted internal network.
- Consider making the booking-conflict rule duration-aware rather than
  exact-timestamp-only, if real scheduling needs it.
- Presentation deck is included in `presentation/`.
- Demo video provided as a public link in the final submission/README.

## Unresolved Issues

None outstanding in the current codebase. One issue *was* found and
resolved during Stage 3 (the Playwright `.status-badge` collision
described above under Testing) — it is preserved here as historical
record, not hidden, since the assessment specifically values honest
handling-of-failure evidence.
