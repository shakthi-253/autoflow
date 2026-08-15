# AutoFlow — Stage 3 AI Change Loop: Service Priority Classification

## Feature request

Add a derived `priority` (`HIGH` / `MEDIUM` / `LOW`) to every service,
computed deterministically from the issue description using the
keyword rules supplied in the prompt. Not user-editable. Returned
through the API and displayed on the dashboard and service detail page.
Existing workflow, validation, and booking-conflict behavior must be
preserved unchanged.

## Baseline before this change

Backend: `91 passed`. Playwright E2E: `9 passed`. Both verified before
starting this feature.

## Files changed

| File | Change |
|---|---|
| `backend/app/services/priority.py` (new) | Pure `calculate_priority()` function implementing the keyword rules |
| `backend/app/models/service.py` | New `ServicePriority` enum; new non-nullable `priority` column on `Service` |
| `backend/app/models/__init__.py` | Export `ServicePriority` |
| `backend/app/schemas/service.py` | `priority` added to `ServiceResponse` only — **not** to `ServiceCreate` |
| `backend/app/routers/services.py` | `create_service` now computes `priority=calculate_priority(payload.issue_description)` |
| `backend/tests/api/test_priority.py` (new) | 28 new tests: unit tests for the classifier + API-level tests |
| `frontend/src/statusConfig.js` | New `PRIORITY_META` (labels/colors) |
| `frontend/src/components/PriorityBadge.jsx` (new) | Renders a priority badge |
| `frontend/src/pages/ServiceDetails.jsx` | Priority row added to the Service Details panel |
| `frontend/src/pages/Dashboard.jsx` | Priority column added to the service table |
| `frontend/src/index.css` | New color tokens (`--priority-high/medium/low` + `-bg` variants) and a dedicated `.priority-badge` style, added during the correction below |
| `README.md` | Noted the schema change requires deleting a pre-existing local `autoflow.db` (no migration tooling in this project) |

`CreateService.jsx` was deliberately **not** touched — no input field
for priority, since it must be derived, not entered. No changes were
made to `app/services/workflow.py`, `app/services/exceptions.py`,
`app/routers/vehicles.py`, or `app/schemas/vehicle.py`.

## Priority rules implemented

Matching is case-insensitive and word-boundary-aware (so `"AC"` matches
only as a standalone word/phrase, not as a substring of something like
`"space"`). HIGH keywords are checked before MEDIUM; there is no overlap
between the two lists as specified.

```
HIGH:   engine failure, engine problem, brake failure, brake problem,
        brake, battery dead, vehicle won't start, vehicle will not
        start, overheating
MEDIUM: AC, air conditioning, cooling, electrical, tyre, tire,
        suspension
LOW:    everything else
```

## AI tools involved

- **Claude (Anthropic)**: initial implementation (model/schema/router
  changes, new backend tests, frontend `PriorityBadge` component and
  its integration into the Dashboard/ServiceDetails pages).
- **ChatGPT**: continued the loop after Claude reached its usage limit
  mid-workflow — specifically, the diagnosis of the Playwright
  regression described below, identifying its root cause, and guiding
  the application-side correction.

This split is recorded explicitly so the evidence log doesn't
misattribute work: Claude did not perform the regression diagnosis or
fix described in this document — ChatGPT did.

## Change-loop execution

### Attempt 1 — initial implementation (Claude)

1. **Implemented** the model/schema/router/frontend changes above.
2. **Ran the existing backend suite**: all 91 pre-existing tests
   passed immediately, with no failures to diagnose.
3. **Added `tests/api/test_priority.py`** (28 new tests: keyword
   matching, case-insensitivity, word-boundary false-positive
   avoidance, HIGH-over-MEDIUM precedence, and API-level checks that
   the field is returned, correctly derived, not client-overridable,
   and stable across status transitions).
4. **Ran the full backend suite again**:
   ```
   119 passed, 2 warnings
   ```
5. **Ran the existing Playwright suite**:
   ```
   7 passed, 2 failed
   ```

**This is a genuine, real failure introduced by the Stage 3
implementation** — not fabricated, not hidden.

### Regression — root cause

The new `PriorityBadge` component reused the existing `.status-badge`
CSS class (the same class `StatusBadge` uses for the service's
workflow status). On the service detail page, this meant **two**
elements matched the `.status-badge` selector: one showing the
service's status (e.g. `BOOKED`) and one showing its priority (e.g.
`LOW`).

Existing Playwright tests that located the status badge via
`.status-badge` — written and passing in Stage 2, before priority
existed — began matching two elements instead of one, which Playwright
treats as a strict-mode violation and reports as a failure.

### Diagnosis and correction (ChatGPT)

ChatGPT identified the `.status-badge` collision as the root cause and
guided the fix:

- `PriorityBadge.jsx` was changed to use `className="priority-badge"`
  instead of `"status-badge"`.
- A corresponding `.priority-badge` CSS rule was added, styled
  identically to `.status-badge` but as a distinct class.
- `StatusBadge.jsx` and its `.status-badge` class were **left
  unchanged** — it continues to represent service status exclusively.

**No test files, test assertions, or Playwright selectors were
modified to reach this result.** The existing tests still assert
against `.status-badge` expecting it to uniquely identify the service
status — that assertion is true again once `PriorityBadge` stopped
using the same class. The fix was entirely in the application.

### Final verification

Both suites were re-run after the correction:

```
Backend:    119 passed, 2 warnings
Playwright: 9 passed
```

## Number of implementation/fix attempts

**2 attempts total**: the initial implementation (Claude, which passed
the backend suite but introduced a genuine Playwright regression), and
one correction (ChatGPT, which fixed the regression without touching
any test).

## Was manual intervention required?

**Yes, in the sense that a second AI tool (ChatGPT) had to complete the
loop** after Claude reached its usage limit mid-workflow. The person
directed the handoff and verified the final results locally. This is
recorded transparently rather than presented as a single continuous
Claude-only session.

## Final result

| Suite | Result |
|---|---|
| Backend/API (`pytest`) | **119 passed, 0 failed** (91 pre-existing + 28 new) |
| Playwright E2E (`npx playwright test`) | **9 passed** (after the `.priority-badge` correction; 7 passed / 2 failed before it) |
