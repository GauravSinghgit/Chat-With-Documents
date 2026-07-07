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
    // FastAPI OAuth2 form requires application/x-www-form-urlencoded. The
    // response also sets an httpOnly cookie server-side — that's what
    // actually authenticates subsequent requests; the body is only used
    // here to populate the in-memory user object.
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);

    return apiRequest("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    });
  },

  async me(): Promise<ApiResult<User>> {
    return apiRequest("/api/auth/me");
  },

  async logout(): Promise<void> {
    await apiRequest("/api/auth/logout", { method: "POST" });
  },
};
