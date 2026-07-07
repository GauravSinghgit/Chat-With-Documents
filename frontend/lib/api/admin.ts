import { apiRequest } from "./client";
import type { AdminStats, ApiResult } from "./types";

export const adminApi = {
  async getStats(days = 30): Promise<ApiResult<AdminStats>> {
    return apiRequest(`/api/admin/stats?days=${days}`);
  },
};
