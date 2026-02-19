import { apiRequest } from "./client";
import type { ChatRequest, ChatResponse, Conversation, Message, ApiResult } from "./types";

export const chatApi = {
  async send(payload: ChatRequest): Promise<ApiResult<ChatResponse>> {
    return apiRequest("/api/chat", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async listConversations(): Promise<ApiResult<Conversation[]>> {
    return apiRequest("/api/conversations");
  },

  async getMessages(conversationId: string): Promise<ApiResult<Message[]>> {
    return apiRequest(`/api/conversations/${conversationId}/messages`);
  },

  async updateTitle(conversationId: string, title: string): Promise<ApiResult<{ id: string; title: string }>> {
    return apiRequest(`/api/conversations/${conversationId}/title?title=${encodeURIComponent(title)}`, {
      method: "PATCH",
    });
  },

  async deleteConversation(conversationId: string): Promise<ApiResult<null>> {
    return apiRequest(`/api/conversations/${conversationId}`, {
      method: "DELETE",
    });
  },
};
