"use client";

import { useEffect, useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { useStreamChat } from "@/lib/hooks/useStreamChat";
import { chatApi } from "@/lib/api/chat";
import { Bot, FileText, X } from "lucide-react";

interface FocusDoc {
  id: number;
  name: string;
}

interface ChatInterfaceProps {
  conversationId: string;
  docName?: string;
  docId?: number;
}

export function ChatInterface({ conversationId, docName, docId }: ChatInterfaceProps) {
  const { messages, isStreaming, error, sendMessage, cancelStream, loadMessages, messagesEndRef } =
    useStreamChat(conversationId);

  // focusDoc can come from URL params OR be picked inline in chat
  const [focusDoc, setFocusDoc] = useState<FocusDoc | null>(
    docName && docId ? { id: docId, name: docName } : null
  );

  // Sync when URL params change (e.g. navigating from documents page)
  useEffect(() => {
    setFocusDoc(docName && docId ? { id: docId, name: docName } : null);
  }, [docName, docId]);

  // Load existing messages on conversation switch
  useEffect(() => {
    let cancelled = false;
    async function load() {
      const result = await chatApi.getMessages(conversationId);
      if (!cancelled && result.ok) loadMessages(result.data);
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [conversationId, loadMessages]);

  return (
    <div className="flex h-full flex-col">
      {/* Focused doc banner */}
      {focusDoc && (
        <div className="flex shrink-0 items-center gap-2 border-b bg-primary/5 px-4 py-2 text-xs text-primary">
          <FileText className="h-3.5 w-3.5 shrink-0" />
          <span className="font-medium">Focused on:</span>
          <span className="flex-1 truncate">{focusDoc.name}</span>
          <button
            onClick={() => setFocusDoc(null)}
            className="ml-1 text-muted-foreground transition-colors hover:text-foreground"
            aria-label="Clear document focus"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* Messages */}
      <ScrollArea className="flex-1">
        <div className="mx-auto max-w-3xl space-y-4 px-4 py-6">
          {messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center gap-3 py-20 text-center">
              <div className="rounded-full bg-primary/10 p-4">
                {focusDoc ? (
                  <FileText className="h-8 w-8 text-primary" />
                ) : (
                  <Bot className="h-8 w-8 text-primary" />
                )}
              </div>
              {focusDoc ? (
                <>
                  <h2 className="text-lg font-semibold">Ask about &quot;{focusDoc.name}&quot;</h2>
                  <p className="max-w-sm text-sm text-muted-foreground">
                    Ask any question — I&apos;ll search this document and give you an accurate
                    answer.
                  </p>
                </>
              ) : (
                <>
                  <h2 className="text-lg font-semibold">How can I help you today?</h2>
                  <p className="max-w-sm text-sm text-muted-foreground">
                    Ask me anything. You can also pick a document below to ask focused questions
                    about it.
                  </p>
                </>
              )}
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
            <div className="rounded-md bg-destructive/10 px-4 py-2 text-center text-sm text-destructive">
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
        placeholder={focusDoc ? `Ask about "${focusDoc.name}"…` : undefined}
        focusDoc={focusDoc}
        onDocSelect={setFocusDoc}
      />
    </div>
  );
}
