import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import StatusBadge from "../components/StatusBadge";
import PriorityBadge from "../components/PriorityBadge";
import { SERVICE_TYPE_LABELS, formatDateTime } from "../statusConfig";

const STAT_CARDS = [
  { key: "total_services", label: "Total Services", accent: "var(--steel)" },
  { key: "booked", label: "Booked", accent: "var(--booked)" },
  { key: "inspection", label: "Inspection", accent: "var(--inspection)" },
  { key: "repair", label: "Repair", accent: "var(--repair)" },
  { key: "completed", label: "Completed", accent: "var(--completed)" },
  { key: "cancelled", label: "Cancelled", accent: "var(--cancelled)" },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [statsData, servicesData] = await Promise.all([
          api.getDashboardStats(),
          api.listServices(),
        ]);
        if (!cancelled) {
          setStats(statsData);
          setServices(servicesData);
        }
      } catch (e) {
        if (!cancelled) setError(e.message || "Failed to load dashboard data");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <div className="page-header">
        <div>
          <div className="eyebrow">Service Center Overview</div>
          <h1>Dashboard</h1>
          <div className="subtitle">Track every vehicle from booking to completion.</div>
        </div>
        <button className="btn btn-accent" onClick={() => navigate("/services/new")}>
          + New Service
        </button>
      </div>

      {error && <div className="banner banner-error">{error}</div>}

      <div className="stat-grid">
        {STAT_CARDS.map((card) => (
          <div className="stat-card" style={{ "--card-accent": card.accent }} key={card.key}>
            <div className="stat-value">{stats ? stats[card.key] : "—"}</div>
            <div className="stat-label">{card.label}</div>
          </div>
        ))}
      </div>

      <div className="panel">
        <div style={{ padding: "16px 20px 4px" }}>
          <h2>Services</h2>
        </div>
        {loading ? (
          <div className="empty-state">Loading services…</div>
        ) : services.length === 0 ? (
          <div className="empty-state">
            No services yet. Create the first one to get started.
          </div>
        ) : (
          <table className="service-table">
            <thead>
              <tr>
                <th>Registration</th>
                <th>Owner</th>
                <th>Vehicle Model</th>
                <th>Service Type</th>
                <th>Priority</th>
                <th>Appointment</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {services.map((s) => (
                <tr key={s.id} onClick={() => navigate(`/services/${s.id}`)}>
                  <td>
                    <span className="reg-plate">{s.vehicle.registration_number}</span>
                  </td>
                  <td>{s.vehicle.owner_name}</td>
                  <td>{s.vehicle.vehicle_model}</td>
                  <td>{SERVICE_TYPE_LABELS[s.service_type] || s.service_type}</td>
                  <td>
                    <PriorityBadge priority={s.priority} />
                  </td>
                  <td>{formatDateTime(s.appointment_date)}</td>
                  <td>
                    <StatusBadge status={s.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
