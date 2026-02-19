"use client";

import { useState, useRef, KeyboardEvent } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { Send, Square, Globe, FileSearch, Bot } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string, opts: { use_rag: boolean; use_tools: boolean; use_agent: boolean }) => void;
  isStreaming: boolean;
  onCancel: () => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, isStreaming, onCancel, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");
  const [useRag, setUseRag] = useState(true);
  const [useTools, setUseTools] = useState(true);
  const [useAgent, setUseAgent] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!value.trim() || isStreaming) return;
    onSend(value.trim(), { use_rag: useRag, use_tools: useTools, use_agent: useAgent });
    setValue("");
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t bg-background/95 backdrop-blur p-4">
      {/* Options row */}
      <div className="flex items-center gap-2 mb-2">
        <ToggleChip
          icon={<FileSearch className="h-3 w-3" />}
          label="RAG"
          active={useRag}
          onClick={() => setUseRag((v) => !v)}
          title="Search uploaded documents"
        />
        <ToggleChip
          icon={<Globe className="h-3 w-3" />}
          label="Web"
          active={useTools}
          onClick={() => setUseTools((v) => !v)}
          title="Use tools (web search, history)"
        />
        <ToggleChip
          icon={<Bot className="h-3 w-3" />}
          label="Agent"
          active={useAgent}
          onClick={() => setUseAgent((v) => !v)}
          title="Enable ReAct agent loop"
        />
      </div>

      {/* Input row */}
      <div className="flex gap-2 items-end">
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message… (Enter to send, Shift+Enter for newline)"
          className="flex-1 min-h-[44px] max-h-[200px] resize-none"
          disabled={disabled || isStreaming}
          rows={1}
        />
        {isStreaming ? (
          <Button variant="outline" size="icon" onClick={onCancel} title="Stop generation">
            <Square className="h-4 w-4 fill-current" />
          </Button>
        ) : (
          <Button
            size="icon"
            onClick={handleSend}
            disabled={!value.trim() || disabled}
            title="Send (Enter)"
          >
            <Send className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}

function ToggleChip({
  icon,
  label,
  active,
  onClick,
  title,
}: {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
  title: string;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={cn(
        "flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium transition-colors border",
        active
          ? "bg-primary/10 border-primary/30 text-primary"
          : "bg-muted border-transparent text-muted-foreground hover:text-foreground"
      )}
    >
      {icon}
      {label}
    </button>
  );
}
