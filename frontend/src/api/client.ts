import type {
  Token,
  User,
  ServiceResponse,
  ServiceCreate,
  ServiceUpdate,
  CheckResponse,
  IncidentResponse,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:13000";

// ─── Token storage ────────────────────────────────────────────────────────────

export function getToken(): string | null {
  return localStorage.getItem("sp_token");
}

export function setToken(token: string): void {
  localStorage.setItem("sp_token", token);
}

export function clearToken(): void {
  localStorage.removeItem("sp_token");
}

// ─── Base fetch helper ────────────────────────────────────────────────────────

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(
      typeof error.detail === "string"
        ? error.detail
        : JSON.stringify(error.detail)
    );
  }

  // 204 No Content
  if (res.status === 204) return undefined as unknown as T;

  return res.json() as Promise<T>;
}

// ─── Auth endpoints ───────────────────────────────────────────────────────────

export async function register(
  username: string,
  password: string
): Promise<User> {
  return request<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function login(
  username: string,
  password: string
): Promise<Token> {
  // FastAPI OAuth2 expects application/x-www-form-urlencoded
  const body = new URLSearchParams({ username, password, grant_type: "password" });

  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(
      typeof error.detail === "string" ? error.detail : "Login failed"
    );
  }

  return res.json() as Promise<Token>;
}

// ─── Services endpoints ───────────────────────────────────────────────────────

export async function getServices(): Promise<ServiceResponse[]> {
  return request<ServiceResponse[]>("/services/");
}

export async function getService(id: number): Promise<ServiceResponse> {
  return request<ServiceResponse>(`/services/${id}`);
}

export async function createService(data: ServiceCreate): Promise<ServiceResponse> {
  return request<ServiceResponse>("/services/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateService(
  id: number,
  data: ServiceUpdate
): Promise<ServiceResponse> {
  return request<ServiceResponse>(`/services/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deleteService(id: number): Promise<void> {
  return request<void>(`/services/${id}`, { method: "DELETE" });
}

// ─── Checks endpoints ─────────────────────────────────────────────────────────

export async function getServiceChecks(
  serviceId: number,
  limit = 50
): Promise<CheckResponse[]> {
  return request<CheckResponse[]>(
    `/services/${serviceId}/checks?limit=${limit}`
  );
}

// ─── Incidents endpoints ──────────────────────────────────────────────────────

export async function getServiceIncidents(
  serviceId: number
): Promise<IncidentResponse[]> {
  return request<IncidentResponse[]>(`/services/${serviceId}/incidents`);
}

export async function getActiveIncidents(): Promise<IncidentResponse[]> {
  return request<IncidentResponse[]>("/services/incidents/active");
}
