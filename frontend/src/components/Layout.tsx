import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function Layout() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  // Read username from JWT payload (simple decode, no verification)
  function getUsername(): string {
    const token = localStorage.getItem("sp_token");
    if (!token) return "User";
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      return payload.sub ?? "User";
    } catch {
      return "User";
    }
  }

  const username = getUsername();

  function handleLogout() {
    logout();
    navigate("/auth");
  }

  return (
    <div className="layout">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar__logo">
          <div className="sidebar__logo-icon">⚡</div>
          <span className="sidebar__logo-text">ServicePulse</span>
        </div>

        <nav className="sidebar__nav">
          <div className="sidebar__nav-label">Monitor</div>
          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              `sidebar__nav-link${isActive ? " active" : ""}`
            }
          >
            <span className="nav-icon">▦</span>
            Dashboard
          </NavLink>
        </nav>

        <div className="sidebar__footer">
          <div className="sidebar__user">
            <div className="sidebar__avatar">
              {username.charAt(0).toUpperCase()}
            </div>
            <span className="sidebar__username">{username}</span>
          </div>
          <button className="sidebar__nav-link btn--ghost" onClick={handleLogout}>
            <span className="nav-icon">→</span>
            Sign out
          </button>
        </div>
      </aside>

      {/* ── Main area ── */}
      <div className="main">
        <div className="content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
