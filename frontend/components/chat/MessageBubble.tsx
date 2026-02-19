"use client";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Message } from "@/lib/api/types";
import { Bot, User } from "lucide-react";

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
}

export function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-3 animate-fade-in", isUser ? "flex-row-reverse" : "flex-row")}>
      {/* Avatar */}
      <Avatar className="h-8 w-8 shrink-0 mt-1">
        <AvatarFallback className={cn(
          "text-xs",
          isUser ? "bg-primary text-primary-foreground" : "bg-muted"
        )}>
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>

      {/* Bubble */}
      <div className={cn("flex flex-col gap-1 max-w-[75%]", isUser && "items-end")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
            isUser
              ? "bg-primary text-primary-foreground rounded-tr-sm"
              : "bg-muted text-foreground rounded-tl-sm"
          )}
        >
          {message.content ? (
            <div
              className="message-content whitespace-pre-wrap break-words"
              dangerouslySetInnerHTML={{
                __html: renderMarkdown(message.content),
              }}
            />
          ) : (
            isStreaming && (
              <span className="flex items-center gap-1 text-muted-foreground">
                <span className="h-1.5 w-1.5 rounded-full bg-current animate-bounce [animation-delay:-0.3s]" />
                <span className="h-1.5 w-1.5 rounded-full bg-current animate-bounce [animation-delay:-0.15s]" />
                <span className="h-1.5 w-1.5 rounded-full bg-current animate-bounce" />
              </span>
            )
          )}
          {isStreaming && message.content && (
            <span className="streaming-cursor" />
          )}
        </div>

        <span className="text-[11px] text-muted-foreground px-1">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  );
}

function formatTime(ts: string): string {
  try {
    return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

/** Minimal inline markdown renderer */
function renderMarkdown(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/```([\s\S]*?)```/g, "<pre><code>$1</code></pre>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/\n/g, "<br/>");
}
