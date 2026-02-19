import type { DocumentListResponse, Document, ApiResult } from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("auth_token");
}

export const documentsApi = {
  async upload(
    files: File[],
    generateSummary = true
  ): Promise<ApiResult<{ ingested: number; results: unknown[] }>> {
    const token = getToken();
    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));

    const res = await fetch(
      `${BASE_URL}/api/documents/ingest?generate_summary=${generateSummary}`,
      {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      }
    );

    if (!res.ok) {
      let msg = `HTTP ${res.status}`;
      try {
        const b = await res.json();
        msg = b.detail || msg;
      } catch {}
      return { ok: false, error: msg, status: res.status };
    }
    const data = await res.json();
    return { ok: true, data };
  },

  async list(page = 1, pageSize = 20, fileType?: string): Promise<ApiResult<DocumentListResponse>> {
    const token = getToken();
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (fileType) params.append("file_type", fileType);

    const res = await fetch(`${BASE_URL}/api/documents?${params}`, {
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });

    if (!res.ok) {
      return { ok: false, error: `HTTP ${res.status}`, status: res.status };
    }
    const data = await res.json();
    return { ok: true, data };
  },

  async get(id: number): Promise<ApiResult<Document>> {
    const token = getToken();
    const res = await fetch(`${BASE_URL}/api/documents/${id}`, {
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
    if (!res.ok) return { ok: false, error: `HTTP ${res.status}`, status: res.status };
    const data = await res.json();
    return { ok: true, data };
  },

  async delete(id: number): Promise<ApiResult<null>> {
    const token = getToken();
    const res = await fetch(`${BASE_URL}/api/documents/${id}`, {
      method: "DELETE",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok && res.status !== 204) {
      return { ok: false, error: `HTTP ${res.status}`, status: res.status };
    }
    return { ok: true, data: null };
  },

  async reindex(id: number): Promise<ApiResult<{ document_id: number; chunks: number; status: string }>> {
    const token = getToken();
    const res = await fetch(`${BASE_URL}/api/documents/${id}/reindex`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
    if (!res.ok) return { ok: false, error: `HTTP ${res.status}`, status: res.status };
    const data = await res.json();
    return { ok: true, data };
  },
};
