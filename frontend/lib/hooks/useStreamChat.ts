"use client";

import { useState, useRef, useCallback } from "react";
import { streamRequest } from "@/lib/api/client";
import type { Message } from "@/lib/api/types";

export function useStreamChat(conversationId: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const nextId = useRef(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 50);
  }, []);

  const sendMessage = useCallback(
    async (
      content: string,
      opts: { use_rag?: boolean; use_tools?: boolean; use_agent?: boolean } = {}
    ) => {
      if (!content.trim() || isStreaming) return;

      setError(null);
      setIsStreaming(true);

      const userMsg: Message = {
        id: nextId.current++,
        role: "user",
        content,
        timestamp: new Date().toISOString(),
      };
      const assistantPlaceholder: Message = {
        id: nextId.current++,
        role: "assistant",
        content: "",
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMsg, assistantPlaceholder]);
      scrollToBottom();

      abortRef.current = new AbortController();

      await streamRequest(
        "/api/chat/stream",
        {
          conversation_id: conversationId,
          message: content,
          use_rag: opts.use_rag ?? true,
          use_tools: opts.use_tools ?? true,
          use_agent: opts.use_agent ?? false,
        },
        // onToken
        (token) => {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last.role === "assistant") {
              updated[updated.length - 1] = { ...last, content: last.content + token };
            }
            return updated;
          });
          scrollToBottom();
        },
        // onDone
        () => {
          setIsStreaming(false);
          scrollToBottom();
        },
        // onError
        (msg) => {
          setError(msg);
          setIsStreaming(false);
          // Remove empty assistant placeholder on error
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last?.role === "assistant" && !last.content) {
              return prev.slice(0, -1);
            }
            return prev;
          });
        },
        abortRef.current.signal
      );
    },
    [conversationId, isStreaming, scrollToBottom]
  );

  const cancelStream = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
  }, []);

  const loadMessages = useCallback((msgs: Message[]) => {
    setMessages(msgs);
  }, []);

  return {
    messages,
    isStreaming,
    error,
    sendMessage,
    cancelStream,
    loadMessages,
    messagesEndRef,
  };
}
