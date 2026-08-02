// Auth
export interface LoginRequest {
  username: string; // actually email
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface RegisterResponse {
  username: string;
}

// User
export interface User {
  username: string;
  email: string;
  filename: string | null;
}

// Projects
export interface Project {
  project_id: number;
  name: string;
  description: string | null;
}

export interface ProjectCreate {
  name: string;
  description?: string;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
}

// API Keys
export interface ApiKey {
  api_key_id: number;
  name: string;
  api_key_created_at: string;
}

export interface ApiKeyCreateRequest {
  name: string;
}

export interface ApiKeyCreateResponse {
  api_key: string;
}

// Dashboard
export interface DashboardOverview {
  projects: number;
  api_keys: number;
  requests_today: number;
  tokens_today: number;
  avg_latency: number;
  cache_hit_rate: number;
  success_rate: number;
}

export interface RequestHistoryItem {
  request_time: string;
  model: string;
  provider: string;
  latency: number;
  tokens: number;
  status: string;
}

export interface ModelUsage {
  model: string;
  requests: number;
  token: number;
}

export interface TokenTrend {
  day: string;
  tokens: number;
}

export interface RequestTrend {
  day: string;
  requests: number;
}

// Chat
export interface ChatRequest {
  prompt: string;
  system_prompt?: string;
  model?: string;
  model_temp?: number;
  max_tokens?: number;
}

export interface ChatResponse {
  response: string;
}

// Health
export interface HealthResponse {
  status: string;
  version: string;
  uptime_seconds: number;
  timestamp: string;
  services: Record<string, string>;
}
