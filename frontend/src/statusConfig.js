// Mirrors the backend's ServiceStatus + ALLOWED_TRANSITIONS. This is used
// only to decide which buttons to SHOW - the backend independently
// enforces which transitions are actually allowed.
export const STATUS_ORDER = ["BOOKED", "INSPECTION", "REPAIR", "COMPLETED"];

export const STATUS_META = {
  BOOKED: { label: "Booked", color: "var(--booked)", bg: "var(--booked-bg)" },
  INSPECTION: { label: "Inspection", color: "var(--inspection)", bg: "var(--inspection-bg)" },
  REPAIR: { label: "Repair", color: "var(--repair)", bg: "var(--repair-bg)" },
  COMPLETED: { label: "Completed", color: "var(--completed)", bg: "var(--completed-bg)" },
  CANCELLED: { label: "Cancelled", color: "var(--cancelled)", bg: "var(--cancelled-bg)" },
};

export const SERVICE_TYPE_LABELS = {
  GENERAL_SERVICE: "General Service",
  OIL_CHANGE: "Oil Change",
  BRAKE_SERVICE: "Brake Service",
  ENGINE_REPAIR: "Engine Repair",
  TYRE_SERVICE: "Tyre Service",
};

// Mirrors the backend's ServicePriority. Priority is always derived
// server-side from the issue description (see app/services/priority.py)
// - there is no user input for it anywhere in the frontend.
export const PRIORITY_META = {
  HIGH: { label: "High", color: "var(--priority-high)", bg: "var(--priority-high-bg)" },
  MEDIUM: { label: "Medium", color: "var(--priority-medium)", bg: "var(--priority-medium-bg)" },
  LOW: { label: "Low", color: "var(--priority-low)", bg: "var(--priority-low-bg)" },
};

// Next-step actions available per status, shown as buttons on the
// service detail page. Mirrors the backend's ALLOWED_TRANSITIONS.
export const NEXT_ACTIONS = {
  BOOKED: [
    { to: "INSPECTION", label: "Start Inspection", variant: "btn-primary" },
    { to: "CANCELLED", label: "Cancel Service", variant: "btn-danger" },
  ],
  INSPECTION: [
    { to: "REPAIR", label: "Start Repair", variant: "btn-primary" },
    { to: "CANCELLED", label: "Cancel Service", variant: "btn-danger" },
  ],
  REPAIR: [{ to: "COMPLETED", label: "Complete Service", variant: "btn-accent" }],
  COMPLETED: [],
  CANCELLED: [],
};

export function formatDateTime(iso) {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
