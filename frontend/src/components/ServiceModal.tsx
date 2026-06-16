import { useState, useEffect } from "react";
import type { ServiceResponse } from "../types";

interface Props {
  onClose: () => void;
  onSave: (data: { name: string; url: string; interval: number }) => Promise<void>;
  initial?: ServiceResponse | null;
}

export default function ServiceModal({ onClose, onSave, initial }: Props) {
  const [name, setName] = useState(initial?.name ?? "");
  const [url, setUrl] = useState(initial?.url ?? "");
  const [interval, setInterval] = useState(String(initial?.interval ?? 60));
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  // Close on Escape key
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  function validate(): string | null {
    if (!name.trim()) return "Name is required.";
    if (!url.trim()) return "URL is required.";
    try {
      new URL(url);
    } catch {
      return "URL must be a valid address (e.g. https://example.com).";
    }
    const n = Number(interval);
    if (!Number.isInteger(n) || n < 10 || n > 3600) {
      return "Interval must be between 10 and 3600 seconds.";
    }
    return null;
  }

  async function handleSubmit() {
    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }
    setError("");
    setSaving(true);
    try {
      await onSave({ name: name.trim(), url: url.trim(), interval: Number(interval) });
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal__header">
          <h2 className="modal__title">
            {initial ? "Edit service" : "Add service"}
          </h2>
          <button className="modal__close" onClick={onClose}>✕</button>
        </div>

        <div className="modal__form">
          {error && <div className="auth-form__alert">{error}</div>}

          <div className="form-group">
            <label className="form-label">Name</label>
            <input
              className="form-input"
              placeholder="My API"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label">URL</label>
            <input
              className="form-input"
              placeholder="https://api.example.com/health"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Check interval (seconds)</label>
            <input
              className="form-input"
              type="number"
              min={10}
              max={3600}
              placeholder="60"
              value={interval}
              onChange={(e) => setInterval(e.target.value)}
            />
            <span className="form-hint">Min 10s · Max 3600s</span>
          </div>
        </div>

        <div className="modal__footer">
          <button className="btn btn--secondary" onClick={onClose}>
            Cancel
          </button>
          <button className="btn btn--primary" onClick={handleSubmit} disabled={saving}>
            {saving ? "Saving…" : initial ? "Save changes" : "Add service"}
          </button>
        </div>
      </div>
    </div>
  );
}
