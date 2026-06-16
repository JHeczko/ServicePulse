import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";
import {
  getService,
  getServiceChecks,
  getServiceIncidents,
  updateService,
  deleteService,
} from "../api/client";
import type { ServiceResponse, CheckResponse, IncidentResponse } from "../types";
import StatusBadge from "../components/StatusBadge";
import ServiceModal from "../components/ServiceModal";
import ChartTooltip from "../components/ChartTooltip";

type ServiceStatus = "up" | "down" | "unknown";

function deriveStatus(checks: CheckResponse[]): ServiceStatus {
  if (!checks.length) return "unknown";
  const last = checks[0];
  return last.status_code >= 200 && last.status_code < 400 ? "up" : "down";
}

function calcUptime(checks: CheckResponse[]): number {
  if (!checks.length) return 0;
  const up = checks.filter((c) => c.status_code >= 200 && c.status_code < 400).length;
  return Math.round((up / checks.length) * 100);
}

function formatTime(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function incidentDuration(start: string, end: string | null): string {
  const ms = (end ? new Date(end).getTime() : Date.now()) - new Date(start).getTime();
  const mins = Math.floor(ms / 60_000);
  if (mins < 60) return `${mins}m`;
  return `${Math.floor(mins / 60)}h ${mins % 60}m`;
}

export default function ServiceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const serviceId = Number(id);

  const [service, setService] = useState<ServiceResponse | null>(null);
  const [checks, setChecks] = useState<CheckResponse[]>([]);
  const [incidents, setIncidents] = useState<IncidentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [showEditModal, setShowEditModal] = useState(false);

  const fetchAll = useCallback(async () => {
    try {
      const [svc, chks, incs] = await Promise.all([
        getService(serviceId),
        getServiceChecks(serviceId, 50),
        getServiceIncidents(serviceId),
      ]);
      setService(svc);
      setChecks(chks);
      setIncidents(incs);
    } catch {
      navigate("/dashboard");
    } finally {
      setLoading(false);
    }
  }, [serviceId, navigate]);

  useEffect(() => {
    fetchAll();
    const timer = setInterval(fetchAll, 30_000);
    return () => clearInterval(timer);
  }, [fetchAll]);

  async function handleUpdate(data: { name: string; url: string; interval: number }) {
    if (!service) return;
    const updated = await updateService(service.id, data);
    setService(updated);
  }

  async function handleDelete() {
    if (!confirm(`Delete "${service?.name}" and all its history?`)) return;
    await deleteService(serviceId);
    navigate("/dashboard");
  }

  if (loading) {
    return (
      <div className="loading-screen" style={{ height: "60vh" }}>
        <div className="spinner" />
      </div>
    );
  }

  if (!service) return null;

  const status = deriveStatus(checks);
  const uptime = calcUptime(checks);
  const avgResponse = checks.length
    ? Math.round(checks.reduce((acc, c) => acc + c.response_time_ms, 0) / checks.length)
    : 0;
  const lastCheck = checks[0];

  // Prepare chart data — reverse so oldest is on the left
  const chartData = [...checks].reverse().map((c) => ({
    time: formatTime(c.created_at),
    response: c.response_time_ms,
    status: c.status_code,
  }));

  const activeIncident = incidents.find((i) => !i.ended_at);

  return (
    <>
      {/* ── Back link ── */}
      <Link to="/dashboard" className="back-link">
        ← Back to Dashboard
      </Link>

      {/* ── Header ── */}
      <div className="detail-header">
        <div className="detail-header__left">
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <h1 className="detail-header__name">{service.name}</h1>
            <StatusBadge status={status} />
          </div>
          <span className="detail-header__url">{service.url}</span>
        </div>
        <div className="detail-header__actions">
          <button className="btn btn--secondary btn--sm" onClick={() => setShowEditModal(true)}>
            Edit
          </button>
          <button className="btn btn--danger btn--sm" onClick={handleDelete}>
            Delete
          </button>
        </div>
      </div>

      {/* ── Active incident notice ── */}
      {activeIncident && (
        <div className="incident-banner">
          <span>🔴</span>
          <span>
            Ongoing incident since {formatDateTime(activeIncident.started_at)} ·{" "}
            {incidentDuration(activeIncident.started_at, null)} elapsed
            {activeIncident.error_message ? ` · ${activeIncident.error_message}` : ""}
          </span>
        </div>
      )}

      {/* ── Stats row ── */}
      <div className="detail-stats-row">
        <div className="stat-card">
          <div className="stat-card__label">Uptime (last 50)</div>
          <div className={`stat-card__value${uptime < 90 ? " stat-card__value--red" : " stat-card__value--green"}`}>
            {uptime}%
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Avg response</div>
          <div className="stat-card__value stat-card__value--blue">
            {avgResponse}<span style={{ fontSize: 14, fontWeight: 500 }}>ms</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-card__label">Total incidents</div>
          <div className={`stat-card__value${incidents.length > 0 ? " stat-card__value--red" : ""}`}>
            {incidents.length}
          </div>
        </div>
      </div>

      {/* ── Charts row ── */}
      <div className="detail-grid">
        {/* Response time chart */}
        <div className="card">
          <div className="card__header">
            <span className="card__title">Response time (ms)</span>
          </div>
          {chartData.length > 0 ? (
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="responseGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4f8ef7" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#4f8ef7" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#252a38" strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="time"
                    tick={{ fill: "#4f566b", fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    tick={{ fill: "#4f566b", fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip content={<ChartTooltip unit="ms" />} />
                  <Area
                    type="monotone"
                    dataKey="response"
                    stroke="#4f8ef7"
                    strokeWidth={2}
                    fill="url(#responseGrad)"
                    dot={false}
                    activeDot={{ r: 4, fill: "#4f8ef7" }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="empty-state" style={{ padding: "40px 0" }}>
              <div style={{ color: "var(--text-muted)", fontSize: 13 }}>No data yet</div>
            </div>
          )}
        </div>

        {/* Status code chart */}
        <div className="card">
          <div className="card__header">
            <span className="card__title">HTTP status codes</span>
          </div>
          {chartData.length > 0 ? (
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                  <CartesianGrid stroke="#252a38" strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="time"
                    tick={{ fill: "#4f566b", fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    tick={{ fill: "#4f566b", fontSize: 11 }}
                    tickLine={false}
                    axisLine={false}
                    domain={[100, 600]}
                  />
                  <Tooltip content={<ChartTooltip />} />
                  <Line
                    type="stepAfter"
                    dataKey="status"
                    stroke="#22c55e"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, fill: "#22c55e" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="empty-state" style={{ padding: "40px 0" }}>
              <div style={{ color: "var(--text-muted)", fontSize: 13 }}>No data yet</div>
            </div>
          )}
        </div>
      </div>

      {/* ── Incidents + Checks row ── */}
      <div className="detail-grid">
        {/* Incident history */}
        <div className="card">
          <div className="card__header">
            <span className="card__title">Incidents</span>
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
              {incidents.length} total
            </span>
          </div>
          {incidents.length === 0 ? (
            <div style={{ color: "var(--text-muted)", fontSize: 13, padding: "12px 0" }}>
              No incidents recorded 🎉
            </div>
          ) : (
            <div className="incidents-list">
              {incidents.map((inc) => (
                <div key={inc.id} className="incident-item">
                  <div
                    className={`incident-item__dot${
                      inc.ended_at ? " incident-item__dot--resolved" : " incident-item__dot--active"
                    }`}
                  />
                  <div className="incident-item__body">
                    <div className="incident-item__message">
                      {inc.error_message || (inc.ended_at ? "Resolved" : "Ongoing")}
                    </div>
                    <div className="incident-item__time">
                      {formatDateTime(inc.started_at)}
                      {inc.ended_at && ` → ${formatDateTime(inc.ended_at)}`}
                    </div>
                  </div>
                  <div className="incident-item__duration">
                    {incidentDuration(inc.started_at, inc.ended_at)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent checks */}
        <div className="card">
          <div className="card__header">
            <span className="card__title">Recent checks</span>
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
              {checks.length} shown
            </span>
          </div>
          {checks.length === 0 ? (
            <div style={{ color: "var(--text-muted)", fontSize: 13, padding: "12px 0" }}>
              No checks yet — worker will pick this up shortly.
            </div>
          ) : (
            <div style={{ overflowY: "auto", maxHeight: 260 }}>
              <table className="checks-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Status</th>
                    <th>Response</th>
                  </tr>
                </thead>
                <tbody>
                  {checks.map((c) => {
                    const isOk = c.status_code >= 200 && c.status_code < 400;
                    return (
                      <tr key={c.id}>
                        <td>{formatTime(c.created_at)}</td>
                        <td className={isOk ? "status-code--ok" : "status-code--err"}>
                          {c.status_code}
                        </td>
                        <td>{c.response_time_ms}ms</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* ── Edit modal ── */}
      {showEditModal && (
        <ServiceModal
          onClose={() => setShowEditModal(false)}
          onSave={handleUpdate}
          initial={service}
        />
      )}
    </>
  );
}
