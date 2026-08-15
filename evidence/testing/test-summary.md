# AutoFlow — Phase 2 Test Summary

## Frameworks used

- **Backend/API**: pytest 9.1.1 + FastAPI `TestClient` (httpx-backed), `pytest-randomly` for order randomization.
- **Frontend/E2E**: Playwright (`@playwright/test`) — written but not executed in this environment (see "E2E execution status" below).

## What was tested

### 1. Normal paths (`tests/api/test_vehicles.py`, `test_services.py`)
- Vehicle creation, listing, retrieval by ID, registration-number normalization to uppercase.
- Service creation (implicitly creating the vehicle), listing, retrieval by ID.
- Dashboard stats reflecting a newly created service and a status change.
- Full happy path: `BOOKED → INSPECTION → REPAIR → COMPLETED`, asserting the returned status after every step.
- Cancellation from `BOOKED` and from `INSPECTION`.

### 2. Edge cases (`tests/api/test_edge_cases.py`)
- Exact boundary values that the actual validators accept: registration number at 5 and 17 characters, contact number at 7 and 15 digits (and with a leading `+`), issue description at exactly 1000 characters, appointment date at exactly `2000-01-01` and at exactly `Dec 31` of `(current year + 2)`.
- Empty-database dashboard stats and empty service list.
- Nonexistent, zero, and negative service/vehicle IDs.
- Multiple services for the same vehicle on different appointment dates (allowed).
- Repeated identical status-transition calls (second call correctly rejected).
- Case-sensitivity of the `service_type` enum.

### 3. Invalid inputs (`tests/api/test_validation.py`)
- Every required field missing (parametrized across all 7 fields).
- Empty-string values for text fields.
- Invalid `service_type`, invalid date format, invalid contact-number formats (letters, separators, too short, too long, malformed `+`), invalid registration-number formats (too short, too long, disallowed characters).
- Over-length `owner_name`, `vehicle_model`, `issue_description`.
- Appointment date outside the accepted range (both directions).
- Malformed JSON body, non-integer ID in a path parameter, wrong data type for a field.
- Confirms a rejected request leaves no partial record in the database.

### 4. Business rules — status transitions (`tests/api/test_status_transitions.py`)
- All 5 documented valid transitions (parametrized).
- All 7 documented invalid transitions (parametrized), plus 4 additional invalid transitions implied by the code's `ALLOWED_TRANSITIONS` map but not explicitly listed in the spec (e.g. a status transitioning to itself).
- For every invalid transition: asserts HTTP 409, the `INVALID_TRANSITION` error code, the `details.current_status`/`details.requested_status` payload, **and** that the service's actual status is unchanged afterward.
- Invalid status value in the PATCH body → 422, status unchanged.
- Transition on a nonexistent service → 404.

### 5. Booking conflict (`tests/api/test_booking_conflict.py`)
- A valid booking succeeds; an exact-timestamp conflict for the same vehicle is rejected with `409 BOOKING_CONFLICT` and doesn't create a second row.
- A different timestamp, or a different vehicle at the same timestamp, is allowed.
- Confirms the actual rule: only `BOOKED`/`INSPECTION`/`REPAIR` (active) services block a rebooking — a `COMPLETED` or `CANCELLED` service at the same timestamp does **not** block a new booking.

### 6. Security/validation
Covered as part of categories 3–5 above: every check is server-side (the test suite calls the API directly, bypassing any frontend), enum values are validated, malformed payloads are rejected, and no raw stack traces are exposed (the app's global exception handler was inspected and confirmed to strip internal error detail unless `DEBUG=true`). No authentication tests were added, because the application does not implement authentication.

## Actual test count and result (backend)

```
91 passed, 2 warnings in 2.35s
```

Full terminal output: `evidence/testing/baseline-test-run.txt`.

The 2 warnings are `DeprecationWarning`s from FastAPI about `@app.on_event("startup")` being deprecated in favor of lifespan handlers — this is a maintenance note, not a test failure or a functional bug, and was left as-is per the instruction not to change application logic during test generation unless the application is genuinely wrong.

## Test-suite sanity check (not the deliberate defect)

Before finalizing, one assertion in `test_status_transitions.py` was **temporarily** changed to an intentionally wrong expected value (application code untouched) to confirm the suite can genuinely fail:

```
5 failed, 14 passed, 2 warnings in 0.81s
```

The assertion was then reverted and the full suite re-run to confirm the 91-passed baseline was restored. This satisfies "demonstrate the test suite can actually fail" without touching business logic — it is **not** the deliberate application-level defect requested for a later phase.

## E2E execution status — IMPORTANT (Stage 2 sandbox limitation, since resolved)

> **Update**: this section describes the situation *at the time this
> Stage 2 evidence was captured*, inside the sandboxed environment used
> to generate the repository. It was subsequently run successfully
> outside that sandbox, on the person's own machine — see
> [`../../docs/ai-change-loop.md`](../../docs/ai-change-loop.md) for
> the Stage 3 record, which includes the first real Playwright run
> (`9 passed`) and the later regression/fix cycle. This section is left
> unedited below as an accurate record of the Stage 2 sandbox
> constraint, not as the current state of the E2E suite.

Three Playwright spec files (9 tests total) were written and cover the
same three categories through the real browser UI: full workflow,
service creation/dashboard listing/action visibility, and frontend
validation. `npx playwright test --list` confirms the config is valid
and all 9 tests are discovered correctly.

**They could not be executed in this environment** (i.e. the sandbox
that produced Stage 2). `npx playwright
install chromium` fails because this sandbox's network egress allowlist
blocks `cdn.playwright.dev`, the host Playwright downloads browser
binaries from:

```
Error: Download failed: server returned code 403 body 'Host not in
allowlist: cdn.playwright.dev. Add this host to your network egress
settings to allow access.'
```

No E2E pass/fail result is claimed **for this Stage 2 sandbox run**. To
run them on a machine with normal internet access:

```bash
cd frontend
npm install
npx playwright install chromium
npx playwright test
```

This is a real, verifiable environment limitation, not a shortcut —
see `docs/ai-testing-log.md` for the full record.
