"use client";

import { useState, useEffect, useCallback } from "react";
import { authApi } from "@/lib/api/auth";
import type { User } from "@/lib/api/types";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // The access token lives in an httpOnly cookie (not readable from JS),
    // so auth state is derived by asking the backend who the cookie
    // belongs to, rather than reading anything out of local storage.
    authApi.me().then((result) => {
      setUser(result.ok ? result.data : null);
      setLoading(false);
    });
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const result = await authApi.login(email, password);
    if (!result.ok) return { ok: false as const, error: result.error };
    setUser(result.data.user);
    return { ok: true as const };
  }, []);

  const register = useCallback(
    async (email: string, password: string, full_name?: string) => {
      const result = await authApi.register({ email, password, full_name });
      if (!result.ok) return { ok: false as const, error: result.error };
      // Auto-login after register
      return login(email, password);
    },
    [login]
  );

  const logout = useCallback(async () => {
    await authApi.logout();
    setUser(null);
  }, []);

  const isAuthenticated = !!user;

  return { user, loading, isAuthenticated, login, register, logout };
}
