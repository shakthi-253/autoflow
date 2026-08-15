# AI Testing Log — Stage 2

> **Scope note**: this document covers Stage 2 only — AI-generated test
> automation and the deliberate backend red run. The Stage 3 AI change
> loop (implementing Service Priority Classification, the Playwright
> regression it introduced, and its correction) is recorded separately
> in [`docs/ai-change-loop.md`](ai-change-loop.md) — the two are not
> merged here.

## AI tool used

Claude (Anthropic), used interactively in an agentic coding session with
direct read/write access to the repository and a sandboxed Linux
container to actually run commands (not just generate text).

## Prompt used

The person supplied a structured "Phase 2 only" brief instructing the AI
to: analyze the existing AutoFlow repository (not assume the original
spec matches the code), generate a layered pytest + Playwright test
suite covering normal paths / edge cases / invalid inputs / business
rules / booking conflict / security-validation, actually run the tests,
fix genuine issues rather than fabricate results, and stop before
introducing any deliberate defect. Full prompt preserved in the
conversation history that produced this repository.

## What the AI analyzed

Before writing a single test, the AI read the actual source files rather
than relying on the prompt's description of the rules:

- `app/schemas/vehicle.py` — registration number regex
  (`^[A-Za-z0-9][A-Za-z0-9\- ]{3,15}[A-Za-z0-9]$`, effectively 5–17
  characters) and contact number regex (`^\+?\d{7,15}$`, 7–15 digits).
- `app/schemas/service.py` — issue description max length (1000 chars),
  appointment date bounds (`2000-01-01` to Dec 31 of `current_year + 2`,
  computed from real system time).
- `app/models/service.py` — the `ALLOWED_TRANSITIONS` dict (the literal
  source of truth for valid/invalid status transitions) and
  `ACTIVE_STATUSES`.
- `app/services/workflow.py` — the booking-conflict rule, confirmed to
  be an **exact appointment-timestamp match** against active-status
  services only, not a time-range overlap.
- `app/routers/services.py` and `vehicles.py` — actual endpoint
  behavior, including that `POST /vehicles` is idempotent by
  registration number (returns the existing record rather than
  erroring), and that `POST /services` upserts the vehicle's
  contact/owner/model fields on repeat bookings.
- `app/services/exceptions.py` and `app/main.py` — the exact structured
  error shape (`{error, message, details}`) and status codes per error
  type, and confirmation that unhandled exceptions never leak a raw
  stack trace to the client.
- `app/database.py` — confirmed a standard SQLAlchemy session-per-request
  pattern suitable for a `get_db` dependency override in tests.
- Frontend `pages/ServiceDetails.jsx`, `Dashboard.jsx`,
  `CreateService.jsx`, `App.jsx`, and `statusConfig.js` — to write E2E
  tests against real labels, button text, and routes rather than
  guessed selectors.

## What tests it generated

91 backend pytest tests across 6 files (`test_vehicles.py`,
`test_services.py`, `test_status_transitions.py`, `test_validation.py`,
`test_edge_cases.py`, `test_booking_conflict.py`), plus 9 Playwright E2E
tests across 3 spec files. See `evidence/testing/test-summary.md` for
the full category breakdown.

## Modifications made by the AI during generation

- Added `httpx` and `pytest-randomly` as backend dev dependencies
  (required by FastAPI's `TestClient` and used to prove order-
  independence), captured in a new `backend/requirements-dev.txt` kept
  separate from the production `requirements.txt`.
- Added `@playwright/test` as a frontend dev dependency and a
  `playwright.config.ts` that boots both the backend (against an
  isolated SQLite file, not the developer's real `autoflow.db`) and the
  frontend dev server automatically.
- No production application code was modified.

## Problems discovered and how they were corrected

1. **E2E locator ambiguity (test-authoring bug, caught before "running"
   evidence, not an application bug).** The first draft of the E2E specs
   asserted status text like `"Booked"` with `page.getByText(..., {exact:
   true})`. Cross-checking against `WorkflowStepper.jsx` showed the same
   word also appears as a step label in the workflow stepper, so the
   locator would have matched two elements and thrown a Playwright
   strict-mode error regardless of whether the app was correct. Fixed by
   scoping status assertions to `page.locator(".status-badge")` (a
   unique element) and using `.first()` where a registration number
   legitimately appears twice on the service detail page (header +
   details table). This was caught by re-reading the component source,
   not by execution, since execution wasn't possible — see below.

2. **Startup-event side file.** The app's `Base.metadata.create_all()`
   startup event runs against whatever `DATABASE_URL` is set at import
   time, independent of the per-test database override. Without
   handling this, running the suite would have left a stray `.db` file
   in the `backend/` working directory. Fixed with a session-scoped
   autouse fixture in `conftest.py` that points that startup-only URL at
   a uniquely named file and deletes it after the full test session.
   Verified by listing `backend/*.db` after a full run — none remain.

3. **Playwright browser binaries could not be downloaded.**
   `npx playwright install chromium` failed with a 403 from
   `cdn.playwright.dev`, which is not on this sandbox's network egress
   allowlist. This is an environment limitation, not a code defect.
   The AI did **not** fabricate a passing (or failing) E2E result. The
   9 E2E tests were still written, and their validity was checked with
   `npx playwright test --list`, which parses and loads the config and
   confirms all 9 tests are discovered without syntax or import errors
   — the strongest verification possible without a working browser
   binary in this environment.

## Actual Stage 2 test results

### Backend

Backend tests were executed successfully during the Stage 2 testing
session:

**91 passed, 2 warnings, 2.35s**

Full output is preserved in:

`evidence/testing/baseline-test-run.txt`

A deliberate, temporary test-only sanity break was also introduced and
executed to confirm that the test harness could detect a failure:

**5 failed, 14 passed, 2 warnings, 0.81s**

The temporary change was then reverted and the backend suite was
re-verified at the 91-passed baseline.

### Frontend E2E — Stage 2 environment limitation

The Playwright E2E suite was **not executed during the original Stage 2
sandbox session** because the required Chromium browser binary could not
be downloaded. The sandbox network policy blocked access to
`cdn.playwright.dev`.

This was an environment limitation specific to the Stage 2 testing
session and was not treated as an application failure.

The 9 Playwright tests were still generated and their configuration and
test discovery were verified using:

```text
npx playwright test --list

All 9 tests were successfully discovered with no syntax or import
errors.

No Playwright pass/fail result was claimed for the Stage 2 sandbox run.

### Later Stage 3 E2E verification

The Playwright suite was subsequently executed locally during Stage 3.

The initial Stage 3 implementation produced a real frontend regression:

**7 passed, 2 failed**

The failures were caused by the new `PriorityBadge` component reusing
the existing `.status-badge` class.

The application was corrected by changing the priority component to use
a dedicated `.priority-badge` class.

The Playwright suite was then executed again:

**9 passed**

The final Stage 3 backend suite was also executed:

**119 passed, 2 warnings**

The complete Stage 3 regression and correction history is documented in:
`docs/ai-change-loop.md`