import type { ApiResult } from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("auth_token");
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResult<T>> {
  const token = getToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const res = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!res.ok) {
      let errorMsg = `HTTP ${res.status}`;
      try {
        const body = await res.json();
        errorMsg = body.detail || body.message || errorMsg;
      } catch {}
      return { ok: false, error: errorMsg, status: res.status };
    }

    // 204 No Content
    if (res.status === 204) {
      return { ok: true, data: null as unknown as T };
    }

    const data = await res.json();
    return { ok: true, data };
  } catch (err) {
    return {
      ok: false,
      error: err instanceof Error ? err.message : "Network error",
      status: 0,
    };
  }
}

export async function streamRequest(
  endpoint: string,
  body: unknown,
  onToken: (token: string) => void,
  onDone: (data: { conversation_id: string; sources: unknown[]; tool_calls: string[] }) => void,
  onError: (msg: string) => void,
  signal?: AbortSignal
) {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  try {
    const res = await fetch(`${BASE_URL}${endpoint}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      signal,
    });

    if (!res.ok || !res.body) {
      let msg = `HTTP ${res.status}`;
      try {
        const b = await res.json();
        msg = b.detail || msg;
      } catch {}
      onError(msg);
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        try {
          const event = JSON.parse(line.slice(6));
          if (event.type === "token") onToken(event.token);
          else if (event.type === "done") onDone(event);
          else if (event.type === "error") onError(event.message);
        } catch {}
      }
    }
  } catch (err) {
    if (err instanceof Error && err.name === "AbortError") return;
    onError(err instanceof Error ? err.message : "Stream error");
  }
}
