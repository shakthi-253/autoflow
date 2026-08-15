# AutoFlow — Stage 2 Controlled RED Run Demonstration

This document records a single, intentional cycle performed during
Stage 2:

```
GREEN → deliberate application defect → RED → restore → GREEN
```

performed to demonstrate that the Stage 2 automated test suite actually
detects a real business-rule regression, not just that it runs.

> **Current status note**: the backend test count below (91) reflects
> the suite as it stood at the time of this Stage 2 demonstration. The
> suite has since grown to 119 tests following the Stage 3 Priority
> Classification feature (28 new tests added; none of the 91 shown
> here were modified or removed). The Stage 2 evidence below is
> preserved unchanged as historical record — it is not the current
> total test count. For the current final results (backend **119
> passed**, Playwright **9 passed**, including the Stage 3 regression
> and fix), see [`docs/ai-change-loop.md`](ai-change-loop.md) and the
> README's Testing section.

## 1. GREEN baseline

Command: `pytest` (from `backend/`, with `requirements-dev.txt` installed)

```
======================== 91 passed, 2 warnings in 2.02s ========================
```

## 2. Intentional defect

**File**: `backend/app/models/service.py`
**Logic**: the `ALLOWED_TRANSITIONS` dict (the single source of truth for
the status workflow, consumed by `app/services/workflow.py` and enforced
in `PATCH /services/{id}/status`).

**Correct behavior (before)**:
```python
ServiceStatus.BOOKED: {ServiceStatus.INSPECTION, ServiceStatus.CANCELLED},
```
`BOOKED → COMPLETED` is not in the set, so it's rejected with `409
INVALID_TRANSITION`.

**Defect introduced (temporary, one line)**:
```python
ServiceStatus.BOOKED: {ServiceStatus.INSPECTION, ServiceStatus.CANCELLED, ServiceStatus.COMPLETED},
```
This makes `BOOKED → COMPLETED` succeed, which violates the documented
workflow (a service must go through `INSPECTION` and `REPAIR` first).
No test files, test data, test configuration, or Playwright selectors
were touched — only this one application file.

## 3. RED result

Targeted run: `pytest tests/api/test_status_transitions.py -v`

```
tests/api/test_status_transitions.py::test_invalid_transition_is_rejected[BOOKED-COMPLETED] FAILED
...
=================== 1 failed, 18 passed, 2 warnings in 0.81s ===================
```

Full suite: `pytest`

```
FAILED tests/api/test_status_transitions.py::test_invalid_transition_is_rejected[BOOKED-COMPLETED]
=================== 1 failed, 90 passed, 2 warnings in 1.96s ===================
```

### Failure detail

```
current = 'BOOKED', target = 'COMPLETED'
    res = client.patch(f"/services/{service_id}/status", json={"status": target})
    assert res.status_code == 409
E   assert 200 == 409
E    +  where 200 = <Response [200 OK]>.status_code
```

- **Test**: `test_invalid_transition_is_rejected[BOOKED-COMPLETED]`
- **Expected**: `409` with `error: "INVALID_TRANSITION"`.
- **Actual (defective app)**: `200 OK`, and the service's status was
  actually persisted as `COMPLETED` (confirmed via the logged
  `PATCH .../status "HTTP/1.1 200 OK"` request).
- **Why this proves detection**: the test asserts the exact contract the
  business rule promises. Widening the `BOOKED` transition set changed
  real, observable runtime behavior, and the unmodified test caught the
  divergence precisely — exactly one test failed (the one that exercises
  `BOOKED → COMPLETED`), and the other 90 tests, including every other
  transition case, were unaffected. This shows the failure is isolated
  to the injected defect rather than a broad or coincidental breakage.

## 4. Restoration

`ALLOWED_TRANSITIONS[ServiceStatus.BOOKED]` was reverted to its exact
original value:
```python
ServiceStatus.BOOKED: {ServiceStatus.INSPECTION, ServiceStatus.CANCELLED},
```
Verified byte-for-byte identical to the pre-defect version by direct
inspection of the file (not just re-running tests).

## 5. Final GREEN result

Targeted run:
```
======================== 19 passed, 2 warnings in 0.74s ========================
```

Full suite:
```
======================== 91 passed, 2 warnings in 1.96s ========================
```

Re-run a second time immediately after to confirm stability (not a
fluke):
```
======================== 91 passed, 2 warnings in 1.95s ========================
```

## Summary

| Stage | Command | Result |
|---|---|---|
| Baseline | `pytest` | 91 passed |
| Defect injected | `pytest` | **1 failed, 90 passed** |
| Restored | `pytest` | 91 passed (confirmed twice) |

Evidence files: `evidence/testing/red-run.txt` (full RED terminal
output), `evidence/testing/restored-green-run.txt` (full restored
GREEN terminal output).

## Scope note

This cycle covered the backend/API suite only, which is where the
`ALLOWED_TRANSITIONS` business rule lives and is directly testable. The
Playwright E2E layer was not re-run as part of this demonstration —
doing so was outside the scope of "run the tests that verify invalid
status transitions... run the complete backend/API suite as well," and
re-running E2E against a temporarily broken backend was not requested.
This Stage 2 red run was a **backend/pytest** run — it should not be
confused with the separate, later **Playwright** red/green cycle that
occurred during Stage 3 (see below).

## Current overall test status (post-Stage 3)

For clarity, since this document's Stage 2 numbers above are now
historical:

| Suite | Current result |
|---|---|
| Backend/API (`pytest`) | **119 passed, 2 warnings** |
| Playwright E2E (`npx playwright test`) | **9 passed** |

Stage 3 also produced its own real red/green cycle — a genuine
Playwright regression (`7 passed, 2 failed`) caused by a `.status-badge`
class collision between the new `PriorityBadge` and the existing
`StatusBadge`, corrected by giving `PriorityBadge` its own
`.priority-badge` class. That cycle is documented in full, including
which AI tool performed the diagnosis and fix, in
[`docs/ai-change-loop.md`](ai-change-loop.md) — it is a distinct event
from the backend `ALLOWED_TRANSITIONS` red run documented above and is
not merged into it.
