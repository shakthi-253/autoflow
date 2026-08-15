import { STATUS_ORDER, STATUS_META } from "../statusConfig";

export default function WorkflowStepper({ status }) {
  const isCancelled = status === "CANCELLED";
  const currentIndex = STATUS_ORDER.indexOf(status);

  return (
    <div className={`stepper${isCancelled ? " cancelled" : ""}`}>
      {STATUS_ORDER.map((s, i) => {
        const state = isCancelled
          ? ""
          : i < currentIndex
          ? "done"
          : i === currentIndex
          ? "current"
          : "";
        return (
          <div className={`step ${state}`} key={s}>
            <div className="step-line" />
            <div className="step-node">{i + 1}</div>
            <div className="step-label">{STATUS_META[s].label}</div>
          </div>
        );
      })}
      {isCancelled && (
        <div className="step">
          <div className="step-node" style={{ background: "var(--cancelled)", borderColor: "var(--cancelled)", color: "#fff" }}>
            ✕
          </div>
          <div className="step-label" style={{ color: "var(--cancelled)" }}>Cancelled</div>
        </div>
      )}
    </div>
  );
}
