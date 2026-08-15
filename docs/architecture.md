# AutoFlow — Architecture Document

## 1. What AutoFlow is

AutoFlow is a web application for a vehicle service center to manage a
vehicle's service journey — booking, inspection, repair, and completion
— with server-enforced workflow rules and a derived priority
classification per service.

## 2. AI tools used

AI tools were used throughout the assessment workflow, with different
tools contributing at different stages.

**Claude (Anthropic)** was used for:
- Stage 1: scaffolding and writing the backend (FastAPI/SQLAlchemy) and
  frontend (React/Vite) from the written specification, followed by
  manual verification of the running application.
- Stage 2: analyzing the existing codebase to derive test cases from
  the actual validator and business-rule implementation, generating
  the pytest and Playwright test suites, and executing the deliberate
  backend RED run.
- Stage 3: implementing the Service Priority Classification feature
  and performing the initial test execution.
- Stage 4: drafting the initial architecture, design, and user-guide
  documentation.

Claude reached its usage limit during the Stage 3 workflow.

**ChatGPT** was then used to continue the Stage 3 AI change loop,
including:
- diagnosing the Playwright regression;
- identifying the `.status-badge` selector collision;
- determining the application-level correction;
- guiding the change from `.status-badge` to `.priority-badge`;
- verifying the final test results; and
- reviewing and refining the final documentation.

The final Stage 3 verification was:

- Backend: **119 passed**
- Playwright E2E: **9 passed**

The application tests were not weakened or modified to hide the
regression. The complete Stage 3 history is documented in
`docs/ai-change-loop.md`.

## 3. Components

```
┌─────────────────────┐         HTTP/JSON          ┌──────────────────────┐
│   React + Vite SPA   │ ──────────────────────────▶│   FastAPI backend    │
│   (frontend/)        │◀────────────────────────── │   (backend/app/)     │
└─────────────────────┘                             └───────────┬──────────┘
                                                                  │ SQLAlchemy ORM
                                                                  ▼
                                                        ┌──────────────────┐
                                                        │  SQLite database │
                                                        │   (autoflow.db)  │
                                                        └──────────────────┘
```

| Component | Technology | Responsibility |
|---|---|---|
| Frontend | React 19 + Vite + `react-router-dom` | Dashboard, service creation form, service detail/actions. No business logic — every rule is re-checked by the backend. |
| Backend API | FastAPI + Pydantic | Request validation, business rules (workflow transitions, booking conflict, priority classification), structured error responses. |
| Data layer | SQLAlchemy ORM + SQLite | Two tables (`vehicles`, `services`), one foreign key relationship. |
| Test suite | pytest (backend), Playwright (E2E) | 119 backend tests, 9 E2E tests. |

## 4. Why this stack

- **FastAPI**: automatic request validation via Pydantic, built-in
  OpenAPI docs (`/docs`), and a `TestClient` that made isolated,
  fast API testing straightforward without a running server.
- **SQLite**: zero setup for a scenario this size (single service
  center); no separate database server for a reviewer to install. The
  ORM layer (SQLAlchemy) means swapping to Postgres later is a
  connection-string change, not a rewrite.
- **React + Vite**: fast dev feedback loop, minimal boilerplate for a
  three-screen app, and Vite's `npm run build` gives a static,
  deployable bundle.
- **No framework for state management, no CSS framework**: the app has
  three screens and one cross-cutting concern (status/priority
  display); Redux, Tailwind, etc. would be unjustified weight for this
  scope. Plain CSS custom properties (`index.css`) cover the design
  system.
- **No authentication**: deliberately not added. A single-location
  internal tool like this typically sits behind a company network or a
  reverse-proxy auth layer, and the brief only asks for auth "where
  relevant." Documented as a known limitation rather than silently
  omitted.

## 5. Data flow — creating and progressing a service

1. **Create**: frontend `POST /services` → backend looks up the vehicle
   by registration number (creates it if new, updates contact/owner
   info if it already exists) → checks the booking-conflict rule →
   computes `priority` from `issue_description` → inserts the `Service`
   row with `status=BOOKED` → returns the full `ServiceResponse`
   (including the joined vehicle).
2. **Transition**: frontend `PATCH /services/{id}/status` → backend
   loads the service → validates the requested transition against
   `ALLOWED_TRANSITIONS` (the single source of truth, independent of
   what buttons the frontend happens to show) → updates `status` and
   `updated_at` → returns the updated record.
3. **Read**: `GET /services`, `GET /services/{id}`, and
   `GET /services/stats/dashboard` are simple reads; the dashboard
   endpoint aggregates counts server-side rather than shipping every
   record to the client to count.

## 6. Business logic placement

All business rules live in `backend/app/services/` (workflow.py,
priority.py, exceptions.py), separate from the HTTP routing layer
(`app/routers/`). This means:
- The frontend can only ever *suggest* actions (e.g. which buttons to
  show); the backend is the only place a transition, a booking
  conflict, or a priority value is actually decided.
- The same rules are exercised identically whether the caller is the
  React app, a test, or someone hitting the API directly with curl —
  verified explicitly in the test suite (e.g.
  `test_priority_field_in_request_body_is_ignored_not_user_settable`).

## 7. Error handling architecture

A single global exception handler (`app/main.py`) maps every error to a
structured `{error, message, details}` JSON body with an appropriate
HTTP status code:

| Error type | HTTP status | Example |
|---|---|---|
| `VehicleNotFoundError` / `ServiceNotFoundError` | 404 | Unknown ID |
| `InvalidTransitionError` | 409 | `BOOKED → COMPLETED` |
| `BookingConflictError` | 409 | Same vehicle, same exact appointment timestamp, still active |
| Pydantic `RequestValidationError` | 422 | Missing field, bad format, wrong type |
| Anything else (unhandled) | 500 | Internal error — stack trace is logged server-side only, never returned to the client |

## 8. Known constraints / deliberate simplifications

- No pagination on list endpoints — acceptable at this data scale.
- Booking conflict is an exact-timestamp match, not a duration/overlap
  check — chosen for explainability, per the original brief.
- No formal DB migration tool (e.g. Alembic) is currently used.
  Schema changes such as the Stage 3 `priority` column may require
  recreating the local SQLite database or applying a manual schema
  migration. This is acceptable for the current assessment scope but
  would be addressed before production deployment.
