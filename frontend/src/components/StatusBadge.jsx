import { STATUS_META } from "../statusConfig";

export default function StatusBadge({ status }) {
  const meta = STATUS_META[status] || { label: status, color: "var(--ink-soft)", bg: "var(--panel-alt)" };
  return (
    <span
      className="status-badge"
      style={{ color: meta.color, background: meta.bg }}
    >
      <span className="status-dot" />
      {meta.label}
    </span>
  );
}
