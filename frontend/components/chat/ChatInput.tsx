"use client";

import { useState, useRef, KeyboardEvent, useEffect } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import {
  Send,
  Square,
  Globe,
  FileSearch,
  Bot,
  FileText,
  Upload,
  X,
  ChevronDown,
} from "lucide-react";
import { documentsApi } from "@/lib/api/documents";
import type { Document } from "@/lib/api/types";

interface FocusDoc {
  id: number;
  name: string;
}

interface ChatInputProps {
  onSend: (
    message: string,
    opts: { use_rag: boolean; use_tools: boolean; use_agent: boolean }
  ) => void;
  isStreaming: boolean;
  onCancel: () => void;
  disabled?: boolean;
  placeholder?: string;
  focusDoc: FocusDoc | null;
  onDocSelect: (doc: FocusDoc | null) => void;
}

export function ChatInput({
  onSend,
  isStreaming,
  onCancel,
  disabled,
  placeholder,
  focusDoc,
  onDocSelect,
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const [useRag, setUseRag] = useState(true);
  const [useTools, setUseTools] = useState(true);
  const [useAgent, setUseAgent] = useState(false);
  const [docs, setDocs] = useState<Document[]>([]);
  const [docsLoaded, setDocsLoaded] = useState(false);
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

  const loadDocs = async () => {
    if (docsLoaded) return;
    const result = await documentsApi.list();
    if (result.ok) {
      setDocs(result.data.documents.filter((d) => d.status === "indexed"));
    }
    setDocsLoaded(true);
  };

  return (
    <div className="border-t bg-background/95 p-4 backdrop-blur">
      {/* Options row */}
      <div className="mb-2 flex flex-wrap items-center gap-2">
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

        {/* Doc Picker */}
        <DropdownMenu onOpenChange={(open) => open && loadDocs()}>
          <DropdownMenuTrigger asChild>
            <button
              title="Focus on a specific document"
              aria-label="Focus on a specific document"
              className={cn(
                "flex max-w-[180px] items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors",
                focusDoc
                  ? "border-primary/30 bg-primary/10 text-primary"
                  : "border-transparent bg-muted text-muted-foreground hover:text-foreground"
              )}
            >
              <FileText className="h-3 w-3 shrink-0" />
              <span className="truncate">{focusDoc ? focusDoc.name : "Select Doc"}</span>
              <ChevronDown className="h-3 w-3 shrink-0 opacity-60" />
            </button>
          </DropdownMenuTrigger>

          <DropdownMenuContent align="start" className="w-64">
            <DropdownMenuLabel className="text-xs font-normal text-muted-foreground">
              Focus chat on a document
            </DropdownMenuLabel>
            <DropdownMenuSeparator />

            {!docsLoaded ? (
              <div className="px-3 py-4 text-center text-xs text-muted-foreground">Loading…</div>
            ) : docs.length === 0 ? (
              <div className="flex flex-col items-center gap-2 px-3 py-4 text-center">
                <Upload className="h-6 w-6 text-muted-foreground/50" />
                <p className="text-xs text-muted-foreground">No documents uploaded yet.</p>
                <Link
                  href="/documents"
                  className="text-xs font-medium text-primary hover:underline"
                >
                  Upload documents →
                </Link>
              </div>
            ) : (
              <>
                {docs.map((doc) => (
                  <DropdownMenuItem
                    key={doc.id}
                    onClick={() => onDocSelect({ id: doc.id, name: doc.original_filename })}
                    className={cn(
                      "cursor-pointer gap-2",
                      focusDoc?.id === doc.id && "bg-primary/5 text-primary"
                    )}
                  >
                    <FileText className="h-3.5 w-3.5 shrink-0" />
                    <span className="truncate text-xs">{doc.original_filename}</span>
                  </DropdownMenuItem>
                ))}

                <DropdownMenuSeparator />

                {focusDoc && (
                  <DropdownMenuItem
                    onClick={() => onDocSelect(null)}
                    className="gap-2 text-muted-foreground"
                  >
                    <X className="h-3.5 w-3.5" />
                    <span className="text-xs">Clear selection</span>
                  </DropdownMenuItem>
                )}

                <DropdownMenuItem asChild>
                  <Link href="/documents" className="cursor-pointer gap-2">
                    <Upload className="h-3.5 w-3.5" />
                    <span className="text-xs">Manage documents</span>
                  </Link>
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Input row */}
      <div className="flex items-end gap-2">
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder ?? "Type a message… (Enter to send, Shift+Enter for newline)"}
          className="max-h-[200px] min-h-[44px] flex-1 resize-none"
          disabled={disabled || isStreaming}
          rows={1}
        />
        {isStreaming ? (
          <Button
            variant="outline"
            size="icon"
            onClick={onCancel}
            title="Stop generation"
            aria-label="Stop generation"
          >
            <Square className="h-4 w-4 fill-current" />
          </Button>
        ) : (
          <Button
            size="icon"
            onClick={handleSend}
            disabled={!value.trim() || disabled}
            title="Send (Enter)"
            aria-label="Send message"
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
        "flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors",
        active
          ? "border-primary/30 bg-primary/10 text-primary"
          : "border-transparent bg-muted text-muted-foreground hover:text-foreground"
      )}
    >
      {icon}
      {label}
    </button>
  );
}
