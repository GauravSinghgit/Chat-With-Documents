import type { DocumentListResponse, Document, ApiResult } from "./types";

export const documentsApi = {
  async upload(
    files: File[],
    generateSummary = true
  ): Promise<ApiResult<{ ingested: number; results: unknown[] }>> {
    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));

    const res = await fetch(`/api/documents/ingest?generate_summary=${generateSummary}`, {
      method: "POST",
      credentials: "include",
      body: formData,
    });

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
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (fileType) params.append("file_type", fileType);

    const res = await fetch(`/api/documents?${params}`, {
      credentials: "include",
      headers: { "Content-Type": "application/json" },
    });

    if (!res.ok) {
      return { ok: false, error: `HTTP ${res.status}`, status: res.status };
    }
    const data = await res.json();
    return { ok: true, data };
  },

  async get(id: number): Promise<ApiResult<Document>> {
    const res = await fetch(`/api/documents/${id}`, {
      credentials: "include",
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) return { ok: false, error: `HTTP ${res.status}`, status: res.status };
    const data = await res.json();
    return { ok: true, data };
  },

  async delete(id: number): Promise<ApiResult<null>> {
    const res = await fetch(`/api/documents/${id}`, {
      method: "DELETE",
      credentials: "include",
    });
    if (!res.ok && res.status !== 204) {
      return { ok: false, error: `HTTP ${res.status}`, status: res.status };
    }
    return { ok: true, data: null };
  },

  async reindex(
    id: number
  ): Promise<ApiResult<{ document_id: number; chunks: number; status: string }>> {
    const res = await fetch(`/api/documents/${id}/reindex`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) return { ok: false, error: `HTTP ${res.status}`, status: res.status };
    const data = await res.json();
    return { ok: true, data };
  },
};
