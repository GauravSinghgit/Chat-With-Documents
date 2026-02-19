import { apiRequest } from "./client";
import type { AuthToken, RegisterPayload, User, ApiResult } from "./types";

export const authApi = {
  async register(payload: RegisterPayload): Promise<ApiResult<User>> {
    return apiRequest("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async login(email: string, password: string): Promise<ApiResult<AuthToken>> {
    // FastAPI OAuth2 form requires application/x-www-form-urlencoded
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);

    const token =
      typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/auth/login`,
      {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
      }
    );

    if (!res.ok) {
      let msg = "Login failed";
      try {
        const body = await res.json();
        msg = body.detail || msg;
      } catch {}
      return { ok: false, error: msg, status: res.status };
    }

    const data = await res.json();
    return { ok: true, data };
  },

  async me(): Promise<ApiResult<User>> {
    return apiRequest("/api/auth/me");
  },

  async logout(): Promise<void> {
    await apiRequest("/api/auth/logout", { method: "POST" });
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_user");
    }
  },
};
