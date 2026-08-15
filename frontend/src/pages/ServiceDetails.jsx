import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import StatusBadge from "../components/StatusBadge";
import PriorityBadge from "../components/PriorityBadge";
import WorkflowStepper from "../components/WorkflowStepper";
import { SERVICE_TYPE_LABELS, NEXT_ACTIONS, formatDateTime } from "../statusConfig";

export default function ServiceDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [service, setService] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [updating, setUpdating] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await api.getService(id);
      setService(data);
    } catch (e) {
      setError(e.message || "Failed to load service");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleTransition(nextStatus) {
    setActionError("");
    setUpdating(true);
    try {
      const updated = await api.updateServiceStatus(id, nextStatus);
      setService(updated);
    } catch (e) {
      if (e instanceof ApiError) {
        setActionError(e.message);
      } else {
        setActionError("Failed to update status");
      }
    } finally {
      setUpdating(false);
    }
  }

  if (loading) return <div className="empty-state">Loading service…</div>;

  if (error || !service) {
    return (
      <div>
        <Link to="/" className="back-link">
          ← Back to dashboard
        </Link>
        <div className="banner banner-error">{error || "Service not found"}</div>
      </div>
    );
  }

  const actions = NEXT_ACTIONS[service.status] || [];

  return (
    <div>
      <Link to="/" className="back-link">
        ← Back to dashboard
      </Link>

      <div className="page-header">
        <div>
          <div className="eyebrow">Service #{service.id}</div>
          <h1>
            <span className="reg-plate" style={{ fontSize: 20 }}>
              {service.vehicle.registration_number}
            </span>
          </h1>
          <div className="subtitle">
            {service.vehicle.vehicle_model} · {SERVICE_TYPE_LABELS[service.service_type]}
          </div>
        </div>
        <StatusBadge status={service.status} />
      </div>

      <div className="panel detail-section">
        <WorkflowStepper status={service.status} />
      </div>

      {actionError && <div className="banner banner-error">{actionError}</div>}

      <div className="detail-grid">
        <div>
          <div className="panel detail-section">
            <h2>Vehicle &amp; Owner</h2>
            <div className="kv-grid">
              <div>
                <div className="kv-label">Registration Number</div>
                <div className="kv-value">{service.vehicle.registration_number}</div>
              </div>
              <div>
                <div className="kv-label">Vehicle Model</div>
                <div className="kv-value">{service.vehicle.vehicle_model}</div>
              </div>
              <div>
                <div className="kv-label">Owner Name</div>
                <div className="kv-value">{service.vehicle.owner_name}</div>
              </div>
              <div>
                <div className="kv-label">Contact Number</div>
                <div className="kv-value">{service.vehicle.contact_number}</div>
              </div>
            </div>
          </div>

          <div className="panel detail-section">
            <h2>Service Details</h2>
            <div className="kv-grid">
              <div>
                <div className="kv-label">Service Type</div>
                <div className="kv-value">{SERVICE_TYPE_LABELS[service.service_type]}</div>
              </div>
              <div>
                <div className="kv-label">Priority</div>
                <div className="kv-value">
                  <PriorityBadge priority={service.priority} />
                </div>
              </div>
              <div>
                <div className="kv-label">Appointment Date</div>
                <div className="kv-value">{formatDateTime(service.appointment_date)}</div>
              </div>
              <div style={{ gridColumn: "1 / -1" }}>
                <div className="kv-label">Issue Description</div>
                <div className="kv-value" style={{ fontWeight: 400 }}>
                  {service.issue_description}
                </div>
              </div>
            </div>
          </div>

          <div className="panel detail-section">
            <h2>Record Info</h2>
            <div className="kv-grid">
              <div>
                <div className="kv-label">Created</div>
                <div className="kv-value" style={{ fontWeight: 400 }}>
                  {formatDateTime(service.created_at)}
                </div>
              </div>
              <div>
                <div className="kv-label">Last Updated</div>
                <div className="kv-value" style={{ fontWeight: 400 }}>
                  {formatDateTime(service.updated_at)}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="panel action-panel">
          <h2>Actions</h2>
          {actions.length === 0 ? (
            <div className="subtitle">No further workflow action for this service.</div>
          ) : (
            actions.map((a) => (
              <button
                key={a.to}
                className={`btn ${a.variant}`}
                disabled={updating}
                onClick={() => handleTransition(a.to)}
              >
                {updating ? "Updating…" : a.label}
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
