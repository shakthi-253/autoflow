# AutoFlow — Design Document

## 1. Data model

### `vehicles`

| Column | Type | Constraints |
|---|---|---|
| `id` | integer | primary key |
| `registration_number` | string(20) | unique, indexed |
| `owner_name` | string(100) | not null |
| `contact_number` | string(20) | not null |
| `vehicle_model` | string(100) | not null |
| `created_at` | datetime | default: now (UTC) |

### `services`

| Column | Type | Constraints |
|---|---|---|
| `id` | integer | primary key |
| `vehicle_id` | integer | foreign key → `vehicles.id`, `ON DELETE CASCADE`, indexed |
| `service_type` | enum | `GENERAL_SERVICE`, `OIL_CHANGE`, `BRAKE_SERVICE`, `ENGINE_REPAIR`, `TYRE_SERVICE` |
| `issue_description` | text | not null, ≤1000 chars |
| `appointment_date` | datetime | not null, bounded `2000-01-01` .. `Dec 31` of (this year + 2) |
| `status` | enum | `BOOKED`, `INSPECTION`, `REPAIR`, `COMPLETED`, `CANCELLED` |
| `priority` | enum | `HIGH`, `MEDIUM`, `LOW` — derived, never client-supplied |
| `created_at` | datetime | default: now (UTC) |
| `updated_at` | datetime | default: now, updated on every change |

One vehicle has many services (1:N); vehicle contact/owner info is
stored once and updated in place on repeat bookings, never duplicated
per service.

## 2. Key flows

### 2.1 Status workflow (state machine)

```
BOOKED --> INSPECTION --> REPAIR --> COMPLETED
  |             |
  v             v
CANCELLED   CANCELLED
```

Enforced by a single lookup table (`ALLOWED_TRANSITIONS` in
`app/models/service.py`), not scattered conditionals:

```python
{
  BOOKED:     {INSPECTION, CANCELLED},
  INSPECTION: {REPAIR, CANCELLED},
  REPAIR:     {COMPLETED},
  COMPLETED:  {},
  CANCELLED:  {},
}
```

Any transition not in this table - including a status "changing" to
itself - is rejected with `409 INVALID_TRANSITION`, regardless of
whether the request came from the UI or a direct API call.

### 2.2 Booking-conflict rule

A vehicle cannot have a second service at the exact same
`appointment_date` while an earlier service for that vehicle at that
timestamp is still active (`BOOKED`, `INSPECTION`, or `REPAIR`).
`COMPLETED` and `CANCELLED` services don't block a rebooking at the
same slot. This is intentionally a simple equality check rather than a
duration/overlap calculation, favoring explainability over precision -
documented as a deliberate simplification, not an oversight.

### 2.3 Priority classification

Computed once, at creation, from `issue_description` - never editable
afterward, never accepted as client input:

| Priority | Trigger (case-insensitive, whole-word match) |
|---|---|
| HIGH | engine failure, engine problem, brake failure, brake problem, brake, battery dead, vehicle won't start, vehicle will not start, overheating |
| MEDIUM | AC, air conditioning, cooling, electrical, tyre, tire, suspension |
| LOW | everything else |

HIGH is checked before MEDIUM. Matching is case-insensitive and uses
word boundaries to avoid false positives from short keywords such as
"AC". Matching uses word boundaries (`\bkeyword\b`) rather
than raw substring search, so short tokens like `"AC"` don't
false-positive inside unrelated words like `"space"`.

### 2.4 Vehicle upsert on service creation

`POST /services` looks up the vehicle by `registration_number`. If
found, it updates that vehicle's `owner_name` / `contact_number` /
`vehicle_model` to the newly submitted values (handles a returning
customer whose contact details changed) and reuses the same
`vehicle_id`. If not found, a new `Vehicle` row is created. This keeps
vehicle data de-duplicated across repeat visits.

## 3. API design

| Method | Path | Purpose | Success | Key errors |
|---|---|---|---|---|
| POST | `/vehicles` | Pre-register a vehicle | 201 | 422 validation |
| GET | `/vehicles` | List vehicles | 200 | - |
| GET | `/vehicles/{id}` | Get one vehicle | 200 | 404 |
| POST | `/services` | Create a service (+ vehicle upsert) | 201 | 422 validation, 409 booking conflict |
| GET | `/services` | List services (newest first) | 200 | - |
| GET | `/services/{id}` | Get one service | 200 | 404 |
| PATCH | `/services/{id}/status` | Transition workflow status | 200 | 404, 409 invalid transition, 422 invalid status value |
| GET | `/services/stats/dashboard` | Aggregate counts by status | 200 | - |

Design choices:
- **`priority` is response-only.** It appears in `ServiceResponse` but
  has no field in `ServiceCreate` - the schema itself makes the
  "not user-editable" requirement structurally true, not just
  enforced by convention. A client that sends `"priority": "HIGH"` in
  the request body has it silently ignored (Pydantic drops unknown
  fields by default); the real value is always server-computed.
- **Dashboard stats is a dedicated endpoint** rather than making the
  frontend fetch and count every service client-side - keeps the
  aggregation logic in one place and scales better if the service list
  grows.
- **PATCH, not PUT, for status changes** - a status transition is a
  partial, rule-checked update, not a full record replacement.

## 4. Error handling design

Every error response has the same shape:

```json
{
  "error": "INVALID_TRANSITION",
  "message": "Cannot change status from BOOKED to COMPLETED",
  "details": { "current_status": "BOOKED", "requested_status": "COMPLETED" }
}
```

This is enforced by one global FastAPI exception handler rather than
per-endpoint try/except blocks, so:
- every error code maps to exactly one HTTP status, consistently;
- validation errors (Pydantic) are flattened into the same
  `{error, message, details}` shape as business-rule errors, so the
  frontend has one error-handling code path (`ApiError` in
  `api/client.js`) regardless of error origin;
- unhandled exceptions are caught, logged server-side, and returned as
  a generic `500 INTERNAL_ERROR` with no stack trace or internal detail
  leaked to the client.

## 5. Frontend design

Three screens, one shared design system (`index.css`, CSS custom
properties):
- **Dashboard** - status counts + a service table (now including a
  Priority column).
- **Create Service** - client-side validation mirrors the backend's
  rules field-for-field, but every rule is re-checked server-side
  before anything is persisted (client validation is a UX convenience,
  never the source of truth).
- **Service Detail** - a workflow stepper, vehicle/service details
  (now including a Priority row), and only the action buttons valid
  for the current status. The backend independently rejects an invalid
  transition even if a button were somehow shown or the API were
  called directly - the UI's button visibility and the backend's
  `ALLOWED_TRANSITIONS` check are two independent layers, not one
  relying on the other.
