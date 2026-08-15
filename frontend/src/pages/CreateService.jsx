import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { SERVICE_TYPE_LABELS } from "../statusConfig";

const REGISTRATION_PATTERN = /^[A-Za-z0-9][A-Za-z0-9\- ]{3,15}[A-Za-z0-9]$/;
const CONTACT_PATTERN = /^\+?\d{7,15}$/;

const INITIAL_FORM = {
  registration_number: "",
  owner_name: "",
  contact_number: "",
  vehicle_model: "",
  service_type: "",
  issue_description: "",
  appointment_date: "",
};

function validateField(name, value) {
  switch (name) {
    case "registration_number":
      if (!value.trim()) return "Registration number is required";
      if (!REGISTRATION_PATTERN.test(value.trim().toUpperCase()))
        return "Use 5-17 letters/numbers, e.g. TN09AB1234";
      return "";
    case "owner_name":
      if (!value.trim()) return "Owner name is required";
      if (value.length > 100) return "Must be at most 100 characters";
      return "";
    case "contact_number":
      if (!value.trim()) return "Contact number is required";
      if (!CONTACT_PATTERN.test(value.trim())) return "Enter 7-15 digits, optionally starting with +";
      return "";
    case "vehicle_model":
      if (!value.trim()) return "Vehicle model is required";
      if (value.length > 100) return "Must be at most 100 characters";
      return "";
    case "service_type":
      if (!value) return "Select a service type";
      return "";
    case "issue_description":
      if (!value.trim()) return "Issue description is required";
      if (value.length > 1000) return "Must be at most 1000 characters";
      return "";
    case "appointment_date":
      if (!value) return "Appointment date is required";
      return "";
    default:
      return "";
  }
}

export default function CreateService() {
  const navigate = useNavigate();
  const [form, setForm] = useState(INITIAL_FORM);
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
    if (errors[name]) {
      setErrors((er) => ({ ...er, [name]: validateField(name, value) }));
    }
  }

  function handleBlur(e) {
    const { name, value } = e.target;
    setErrors((er) => ({ ...er, [name]: validateField(name, value) }));
  }

  function validateAll() {
    const next = {};
    for (const key of Object.keys(form)) {
      const msg = validateField(key, form[key]);
      if (msg) next[key] = msg;
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitError("");
    if (!validateAll()) return;

    setSubmitting(true);
    try {
      const payload = {
        ...form,
        registration_number: form.registration_number.trim().toUpperCase(),
        appointment_date: new Date(form.appointment_date).toISOString().slice(0, 19),
      };
      const service = await api.createService(payload);
      navigate(`/services/${service.id}`);
    } catch (err) {
      if (err instanceof ApiError && err.code === "VALIDATION_ERROR" && err.details?.errors) {
        const fieldErrors = {};
        for (const fe of err.details.errors) {
          fieldErrors[fe.field] = fe.message.replace(/^Value error,\s*/, "");
        }
        setErrors((er) => ({ ...er, ...fieldErrors }));
      } else {
        setSubmitError(err.message || "Failed to create service");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <Link to="/" className="back-link">
        ← Back to dashboard
      </Link>
      <div className="page-header">
        <div>
          <div className="eyebrow">New Booking</div>
          <h1>Create Service</h1>
          <div className="subtitle">Register a vehicle and book a service appointment.</div>
        </div>
      </div>

      {submitError && <div className="banner banner-error">{submitError}</div>}

      <form className="panel" style={{ padding: "22px 24px" }} onSubmit={handleSubmit} noValidate>
        <div className="form-section-title">Vehicle Information</div>
        <div className="form-grid">
          <Field
            label="Registration Number"
            name="registration_number"
            value={form.registration_number}
            error={errors.registration_number}
            onChange={handleChange}
            onBlur={handleBlur}
            placeholder="TN09AB1234"
          />
          <Field
            label="Owner Name"
            name="owner_name"
            value={form.owner_name}
            error={errors.owner_name}
            onChange={handleChange}
            onBlur={handleBlur}
            placeholder="Ravi Kumar"
          />
          <Field
            label="Contact Number"
            name="contact_number"
            value={form.contact_number}
            error={errors.contact_number}
            onChange={handleChange}
            onBlur={handleBlur}
            placeholder="9876543210"
          />
          <Field
            label="Vehicle Model"
            name="vehicle_model"
            value={form.vehicle_model}
            error={errors.vehicle_model}
            onChange={handleChange}
            onBlur={handleBlur}
            placeholder="Honda City"
          />
        </div>

        <div className="form-section-title">Service Information</div>
        <div className="form-grid">
          <div className="field">
            <label htmlFor="service_type">Service Type</label>
            <select
              id="service_type"
              name="service_type"
              value={form.service_type}
              onChange={handleChange}
              onBlur={handleBlur}
              className={errors.service_type ? "has-error" : ""}
            >
              <option value="">Select a service type…</option>
              {Object.entries(SERVICE_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
            {errors.service_type && <div className="field-error">{errors.service_type}</div>}
          </div>
          <Field
            label="Appointment Date & Time"
            name="appointment_date"
            type="datetime-local"
            value={form.appointment_date}
            error={errors.appointment_date}
            onChange={handleChange}
            onBlur={handleBlur}
          />
          <div className="field field-full">
            <label htmlFor="issue_description">Issue Description</label>
            <textarea
              id="issue_description"
              name="issue_description"
              rows={4}
              value={form.issue_description}
              onChange={handleChange}
              onBlur={handleBlur}
              className={errors.issue_description ? "has-error" : ""}
              placeholder="Describe the issue or requested service…"
            />
            {errors.issue_description && (
              <div className="field-error">{errors.issue_description}</div>
            )}
          </div>
        </div>

        <div style={{ display: "flex", gap: 10, marginTop: 8 }}>
          <button type="submit" className="btn btn-accent" disabled={submitting}>
            {submitting ? "Creating…" : "Create Service"}
          </button>
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => navigate("/")}
            disabled={submitting}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

function Field({ label, name, value, error, onChange, onBlur, placeholder, type = "text" }) {
  return (
    <div className="field">
      <label htmlFor={name}>{label}</label>
      <input
        id={name}
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        placeholder={placeholder}
        className={error ? "has-error" : ""}
      />
      {error && <div className="field-error">{error}</div>}
    </div>
  );
}
