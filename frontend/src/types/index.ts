export interface User {
  id: number;
  username: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface ServiceResponse {
  id: number;
  name: string;
  url: string;
  interval: number;
  user_id: number;
}

export interface ServiceCreate {
  name: string;
  url: string;
  interval: number;
}

export interface ServiceUpdate {
  name: string;
  url: string;
  interval: number;
}

export interface CheckResponse {
  id: number;
  status_code: number;
  response_time_ms: number;
  created_at: string;
  user_id: number;
  service_id: number;
}

export interface IncidentResponse {
  id: number;
  started_at: string;
  ended_at: string | null;
  error_message: string;
  user_id: number;
  service_id: number;
}

export type ServiceStatus = "up" | "down" | "unknown";

export interface ServiceWithStatus extends ServiceResponse {
  status: ServiceStatus;
  lastCheck?: CheckResponse;
  uptime?: number; // percentage 0-100
}
