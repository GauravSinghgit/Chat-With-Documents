"use client";

import { useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { Skeleton } from "@/components/ui/skeleton";
import { useStreamChat } from "@/lib/hooks/useStreamChat";
import { chatApi } from "@/lib/api/chat";
import { Bot } from "lucide-react";

interface ChatInterfaceProps {
  conversationId: string;
}

export function ChatInterface({ conversationId }: ChatInterfaceProps) {
  const { messages, isStreaming, error, sendMessage, cancelStream, loadMessages, messagesEndRef } =
    useStreamChat(conversationId);

  // Load existing messages when switching conversations
  useEffect(() => {
    let cancelled = false;
    async function load() {
      const result = await chatApi.getMessages(conversationId);
      if (!cancelled && result.ok) {
        loadMessages(result.data);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [conversationId, loadMessages]);

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <ScrollArea className="flex-1">
        <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full py-20 text-center gap-3">
              <div className="rounded-full bg-primary/10 p-4">
                <Bot className="h-8 w-8 text-primary" />
              </div>
              <h2 className="text-lg font-semibold">How can I help you today?</h2>
              <p className="text-sm text-muted-foreground max-w-sm">
                Ask me anything. I can search your documents, browse the web, and remember our conversation.
              </p>
            </div>
          )}

          {messages.map((msg, i) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              isStreaming={isStreaming && i === messages.length - 1 && msg.role === "assistant"}
            />
          ))}

          {error && (
            <div className="text-center text-sm text-destructive bg-destructive/10 rounded-md py-2 px-4">
              {error}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input */}
      <ChatInput
        onSend={sendMessage}
        isStreaming={isStreaming}
        onCancel={cancelStream}
      />
    </div>
  );
}
