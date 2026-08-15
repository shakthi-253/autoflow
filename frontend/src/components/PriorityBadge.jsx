import { PRIORITY_META } from "../statusConfig";

export default function PriorityBadge({ priority }) {
  const meta = PRIORITY_META[priority] || {
    label: priority,
    color: "var(--ink-soft)",
    bg: "var(--panel-alt)",
  };
  return (
    <span className="status-badge" style={{ color: meta.color, background: meta.bg }}>
      <span className="status-dot" />
      {meta.label}
    </span>
  );
}
