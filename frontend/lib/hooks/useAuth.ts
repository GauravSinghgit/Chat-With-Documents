"use client";

import { useState, useEffect, useCallback } from "react";
import { authApi } from "@/lib/api/auth";
import type { User } from "@/lib/api/types";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("auth_user");
    const token = localStorage.getItem("auth_token");
    if (stored && token) {
      try {
        setUser(JSON.parse(stored));
      } catch {}
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const result = await authApi.login(email, password);
    if (!result.ok) return { ok: false as const, error: result.error };
    localStorage.setItem("auth_token", result.data.access_token);
    localStorage.setItem("auth_user", JSON.stringify(result.data.user));
    setUser(result.data.user);
    return { ok: true as const };
  }, []);

  const register = useCallback(async (email: string, password: string, full_name?: string) => {
    const result = await authApi.register({ email, password, full_name });
    if (!result.ok) return { ok: false as const, error: result.error };
    // Auto-login after register
    return login(email, password);
  }, [login]);

  const logout = useCallback(async () => {
    await authApi.logout();
    setUser(null);
  }, []);

  const isAuthenticated = !!user;

  return { user, loading, isAuthenticated, login, register, logout };
}
