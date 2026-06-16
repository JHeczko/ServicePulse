import { useState } from "react";
import { useAuth } from "../hooks/useAuth";

type Tab = "login" | "register";

export default function AuthPage() {
  const { loginUser, registerUser } = useAuth();

  const [tab, setTab] = useState<Tab>("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit() {
    if (!username.trim() || !password.trim()) {
      setError("Username and password are required.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      if (tab === "login") {
        await loginUser(username.trim(), password);
      } else {
        await registerUser(username.trim(), password);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") handleSubmit();
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        {/* Logo */}
        <div className="auth-card__logo">
          <div className="auth-card__logo-icon">⚡</div>
          <span className="auth-card__logo-text">ServicePulse</span>
        </div>

        {/* Heading */}
        <h1 className="auth-card__title">
          {tab === "login" ? "Welcome back" : "Create account"}
        </h1>
        <p className="auth-card__subtitle">
          {tab === "login"
            ? "Sign in to monitor your services."
            : "Start monitoring your infrastructure in seconds."}
        </p>

        {/* Tabs */}
        <div className="auth-card__tabs">
          <button
            className={`auth-card__tab${tab === "login" ? " active" : ""}`}
            onClick={() => { setTab("login"); setError(""); }}
          >
            Sign in
          </button>
          <button
            className={`auth-card__tab${tab === "register" ? " active" : ""}`}
            onClick={() => { setTab("register"); setError(""); }}
          >
            Create account
          </button>
        </div>

        {/* Form */}
        <div className="auth-form">
          {error && <div className="auth-form__alert">{error}</div>}

          <div className="form-group">
            <label className="form-label">Username</label>
            <input
              className="form-input"
              type="text"
              placeholder="your-username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onKeyDown={handleKeyDown}
              autoFocus
              autoComplete="username"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              className="form-input"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={handleKeyDown}
              autoComplete={tab === "login" ? "current-password" : "new-password"}
            />
          </div>

          <button
            className="btn btn--primary"
            style={{ width: "100%", justifyContent: "center", padding: "10px" }}
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading
              ? "Please wait…"
              : tab === "login"
              ? "Sign in"
              : "Create account"}
          </button>
        </div>
      </div>
    </div>
  );
}
