import { Routes, Route, Link } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import CreateService from "./pages/CreateService";
import ServiceDetails from "./pages/ServiceDetails";

export default function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="brand">
          <span className="brand-mark" />
          <span className="brand-name">AutoFlow</span>
          <span className="brand-tagline">Vehicle Service &amp; Repair Workflow</span>
        </Link>
      </header>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/services/new" element={<CreateService />} />
          <Route path="/services/:id" element={<ServiceDetails />} />
        </Routes>
      </main>
    </div>
  );
}
