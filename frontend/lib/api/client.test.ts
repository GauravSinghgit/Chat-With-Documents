import { afterEach, describe, expect, it, vi } from "vitest";
import { apiRequest } from "./client";

describe("apiRequest", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends credentials: include so the httpOnly auth cookie is attached", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ hello: "world" }), { status: 200 })
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiRequest("/api/whoami");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/whoami",
      expect.objectContaining({ credentials: "include" })
    );
    expect(result).toEqual({ ok: true, data: { hello: "world" } });
  });

  it("returns ok:false with the server's detail message on non-2xx", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Not authenticated" }), { status: 401 })
      )
    );

    const result = await apiRequest("/api/auth/me");

    expect(result).toEqual({ ok: false, error: "Not authenticated", status: 401 });
  });

  it("returns ok:false on a network failure without throwing", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch"))
    );

    const result = await apiRequest("/api/anything");

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.status).toBe(0);
    }
  });

  it("treats 204 No Content as a successful empty response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 204 })));

    const result = await apiRequest("/api/documents/1");

    expect(result).toEqual({ ok: true, data: null });
  });
});
