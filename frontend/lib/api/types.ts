// ─── Auth ─────────────────────────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name?: string;
}

// ─── Chat ─────────────────────────────────────────────────────────────────────
export interface ChatRequest {
  conversation_id: string;
  message: string;
  use_rag?: boolean;
  use_tools?: boolean;
  use_agent?: boolean;
}

export interface ChatResponse {
  conversation_id: string;
  message: string;
  sources?: Array<{ content: string; score: number }>;
  tool_calls?: string[];
  agent_thoughts?: string[];
}

export type StreamEvent =
  | { type: "token"; token: string }
  | { type: "done"; conversation_id: string; sources: Array<{ content: string; score: number }>; tool_calls: string[] }
  | { type: "error"; message: string };

// ─── Conversations ────────────────────────────────────────────────────────────
export interface Conversation {
  id: string;
  title?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

// ─── Documents ────────────────────────────────────────────────────────────────
export interface Document {
  id: number;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  chunk_count: number;
  page_count: number;
  status: "processing" | "indexed" | "failed";
  summary?: string;
  created_at: string;
}

export interface DocumentListResponse {
  total: number;
  documents: Document[];
}

// ─── Admin / Usage Analytics ──────────────────────────────────────────────────
export interface UsageTotals {
  total_requests: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  avg_latency_ms: number;
}

export interface UsageByUser {
  user_id: string | null;
  email: string | null;
  requests: number;
  total_tokens: number;
}

export interface UsageByDay {
  date: string;
  requests: number;
  total_tokens: number;
}

export interface AdminStats {
  totals: UsageTotals;
  by_user: UsageByUser[];
  by_day: UsageByDay[];
}

// ─── Generic ─────────────────────────────────────────────────────────────────
export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string; status: number };
