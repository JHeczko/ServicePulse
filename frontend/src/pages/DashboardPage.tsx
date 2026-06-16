import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  getServices,
  getServiceChecks,
  getActiveIncidents,
  createService,
  deleteService,
} from "../api/client";
import type { ServiceResponse, CheckResponse, IncidentResponse, ServiceWithStatus, ServiceStatus } from "../types";
import StatusBadge from "../components/StatusBadge";
import ServiceModal from "../components/ServiceModal";

// Derive status from the most recent check
function deriveStatus(checks: CheckResponse[]): ServiceStatus {
  if (!checks.length) return "unknown";
  const last = checks[0];
  return last.status_code >= 200 && last.status_code < 400 ? "up" : "down";
}

// Calculate uptime % from last N checks
function calcUptime(checks: CheckResponse[]): number {
  if (!checks.length) return 0;
  const up = checks.filter((c) => c.status_code >= 200 && c.status_code < 400).length;
  return Math.round((up / checks.length) * 100);
}

// Format a date string nicely
function formatRelative(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const seconds = Math.floor(diff / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}

export default function DashboardPage() {
  const navigate = useNavigate();

  const [services, setServices] = useState<ServiceWithStatus[]>([]);
  const [activeIncidents, setActiveIncidents] = useState<IncidentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      const [rawServices, incidents] = await Promise.all([
        getServices(),
        getActiveIncidents(),
      ]);

      // Fetch recent checks for every service in parallel
      const checkResults = await Promise.all(
        rawServices.map((s) => getServiceChecks(s.id, 50).catch(() => [] as CheckResponse[]))
      );

      const enriched: ServiceWithStatus[] = rawServices.map((s, i) => {
        const checks = checkResults[i];
        return {
          ...s,
          status: deriveStatus(checks),
          lastCheck: checks[0],
          uptime: calcUptime(checks),
        };
      });

      setServices(enriched);
      setActiveIncidents(incidents);
    } catch (e) {
      console.error("Failed to load dashboard data", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    // Refresh every 30 seconds
    const timer = setInterval(fetchAll, 30_000);
    return () => clearInterval(timer);
  }, [fetchAll]);

  async function handleCreate(data: { name: string; url: string; interval: number }) {
    await createService(data);
    await fetchAll();
  }

  async function handleDelete(e: React.MouseEvent, id: number) {
    e.stopPropagation(); // Don't navigate to detail
    if (!confirm("Delete this service and all its history?")) return;
    setDeletingId(id);
    try {
      await deleteService(id);
      setServices((prev) => prev.filter((s) => s.id !== id));
    } finally {
      setDeletingId(null);
    }
  }

  // Summary counts
  const total   = services.length;
  const upCount = services.filter((s) => s.status === "up").length;
  const downCount = services.filter((s) => s.status === "down").length;
  const avgUptime = total
    ? Math.round(services.reduce((acc, s) => acc + (s.uptime ?? 0), 0) / total)
    : 0;

  if (loading) {
    return (
      <div className="loading-screen" style={{ height: "60vh" }}>
        <div className="spinner" />
      </div>
    );
  }

  return (
    <>
      {/* ── Active incident banner ── */}
      {activeIncidents.length > 0 && (
        <div className="incident-banner">
          <span>🔴</span>
          <span>
            {activeIncidents.length} active incident
            {activeIncidents.length > 1 ? "s" : ""} — some services are down
          </span>
        </div>
      )}

      {/* ── Page header ── */}
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <button className="btn btn--primary" onClick={() => setShowModal(true)}>
          + Add service
        </button>
      </div>

      {/* ── Stats row ── */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-card__label">Total services</div>
          <div className="stat-card__value stat-card__value--blue">{total}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Online</div>
          <div className="stat-card__value stat-card__value--green">{upCount}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Incidents</div>
          <div className={`stat-card__value${downCount > 0 ? " stat-card__value--red" : ""}`}>
            {downCount}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Avg uptime</div>
          <div className={`stat-card__value${avgUptime < 90 ? " stat-card__value--red" : " stat-card__value--green"}`}>
            {avgUptime}%
          </div>
        </div>
      </div>

      {/* ── Services table ── */}
      {services.length === 0 ? (
        <div className="services-table-wrap">
          <div className="empty-state">
            <div className="empty-state__icon">📡</div>
            <div className="empty-state__title">No services yet</div>
            <div className="empty-state__desc">
              Add your first service to start monitoring uptime and response times.
            </div>
            <button className="btn btn--primary" onClick={() => setShowModal(true)}>
              + Add service
            </button>
          </div>
        </div>
      ) : (
        <div className="services-table-wrap">
          <table className="services-table">
            <thead>
              <tr>
                <th>Service</th>
                <th>Status</th>
                <th>Uptime (last 50)</th>
                <th>Last check</th>
                <th>Interval</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {services.map((svc) => (
                <tr key={svc.id} onClick={() => navigate(`/services/${svc.id}`)}>
                  <td>
                    <div className="service-name">{svc.name}</div>
                    <div className="service-url">{svc.url}</div>
                  </td>
                  <td>
                    <StatusBadge status={svc.status} />
                  </td>
                  <td>
                    <UptimeBar uptime={svc.uptime ?? 0} />
                  </td>
                  <td className="mono" style={{ color: "var(--text-secondary)", fontSize: 12 }}>
                    {svc.lastCheck
                      ? formatRelative(svc.lastCheck.created_at)
                      : "—"}
                  </td>
                  <td style={{ color: "var(--text-muted)", fontSize: 12 }}>
                    {svc.interval}s
                  </td>
                  <td>
                    <button
                      className="btn btn--danger btn--sm"
                      onClick={(e) => handleDelete(e, svc.id)}
                      disabled={deletingId === svc.id}
                    >
                      {deletingId === svc.id ? "…" : "Delete"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Add service modal ── */}
      {showModal && (
        <ServiceModal
          onClose={() => setShowModal(false)}
          onSave={handleCreate}
        />
      )}
    </>
  );
}

// Compact uptime bar — 20 segments coloured green/red/grey
function UptimeBar({ uptime }: { uptime: number }) {
  const segments = 20;
  const upSegments = Math.round((uptime / 100) * segments);

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <div className="uptime-bar">
        {Array.from({ length: segments }).map((_, i) => (
          <div
            key={i}
            className={`uptime-bar__segment${
              i < upSegments ? " uptime-bar__segment--up" : " uptime-bar__segment--down"
            }`}
          />
        ))}
      </div>
      <span style={{ fontSize: 12, color: "var(--text-muted)", fontVariantNumeric: "tabular-nums" }}>
        {uptime}%
      </span>
    </div>
  );
}
