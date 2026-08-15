const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(message, status, code, details) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  let body = null;
  try {
    body = await res.json();
  } catch {
    // no body / not JSON
  }

  if (!res.ok) {
    const message = body?.message || `Request failed with status ${res.status}`;
    throw new ApiError(message, res.status, body?.error, body?.details);
  }

  return body;
}

export const api = {
  getDashboardStats: () => request("/services/stats/dashboard"),
  listServices: () => request("/services"),
  getService: (id) => request(`/services/${id}`),
  createService: (payload) =>
    request("/services", { method: "POST", body: JSON.stringify(payload) }),
  updateServiceStatus: (id, status) =>
    request(`/services/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
};

export { ApiError };
