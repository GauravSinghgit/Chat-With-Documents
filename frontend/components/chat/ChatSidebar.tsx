"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { chatApi } from "@/lib/api/chat";
import { cn, truncate, formatDate } from "@/lib/utils";
import type { Conversation } from "@/lib/api/types";
import {
  MessageSquarePlus,
  Trash2,
  MoreHorizontal,
  FileText,
  LogOut,
  Moon,
  Sun,
  Bot,
  BarChart3,
} from "lucide-react";
import { useTheme } from "next-themes";
import { toast } from "sonner";

interface ChatSidebarProps {
  activeConversationId?: string;
  onLogout: () => void;
  userName?: string;
  isAdmin?: boolean;
}

export function ChatSidebar({
  activeConversationId,
  onLogout,
  userName,
  isAdmin,
}: ChatSidebarProps) {
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchConversations = useCallback(async () => {
    const result = await chatApi.listConversations();
    if (result.ok) setConversations(result.data);
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations, activeConversationId]);

  const handleNew = () => {
    router.push(`/chat/${crypto.randomUUID()}`);
  };

  const handleDelete = async (id: string) => {
    const result = await chatApi.deleteConversation(id);
    if (result.ok) {
      setConversations((prev) => prev.filter((c) => c.id !== id));
      toast.success("Conversation deleted");
      if (activeConversationId === id) router.push("/chat");
    } else {
      toast.error("Failed to delete conversation");
    }
  };

  return (
    <aside className="flex h-full w-64 flex-col border-r bg-muted/30">
      {/* Header */}
      <div className="flex items-center gap-2 p-4 font-semibold">
        <Bot className="h-5 w-5 text-primary" />
        <span className="text-sm">AI Assistant</span>
      </div>

      <Separator />

      {/* New Chat */}
      <div className="p-3">
        <Button onClick={handleNew} className="w-full gap-2" variant="outline" size="sm">
          <MessageSquarePlus className="h-4 w-4" />
          New Chat
        </Button>
      </div>

      {/* Conversations */}
      <ScrollArea className="flex-1 px-2">
        {loading ? (
          <div className="space-y-2 px-1 py-2">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-9 w-full rounded-md" />
            ))}
          </div>
        ) : conversations.length === 0 ? (
          <p className="px-3 py-6 text-center text-xs text-muted-foreground">
            No conversations yet.
            <br />
            Start a new chat!
          </p>
        ) : (
          <div className="space-y-0.5 py-2">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                className={cn(
                  "group flex items-center justify-between rounded-md px-3 py-2 text-sm transition-colors",
                  activeConversationId === conv.id
                    ? "bg-accent text-accent-foreground"
                    : "cursor-pointer hover:bg-accent/50"
                )}
                onClick={() => router.push(`/chat/${conv.id}`)}
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium leading-tight">
                    {truncate(conv.title || "New Chat", 28)}
                  </p>
                  <p className="mt-0.5 text-[11px] text-muted-foreground">
                    {formatDate(conv.updated_at)} · {conv.message_count} msgs
                  </p>
                </div>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 shrink-0 opacity-0 group-hover:opacity-100"
                    >
                      <MoreHorizontal className="h-3.5 w-3.5" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                      className="text-destructive"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(conv.id);
                      }}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            ))}
          </div>
        )}
      </ScrollArea>

      <Separator />

      {/* Footer */}
      <div className="space-y-1 p-3">
        <Link href="/documents">
          <Button variant="ghost" size="sm" className="w-full justify-start gap-2">
            <FileText className="h-4 w-4" />
            Documents
          </Button>
        </Link>
        {isAdmin && (
          <Link href="/admin">
            <Button variant="ghost" size="sm" className="w-full justify-start gap-2">
              <BarChart3 className="h-4 w-4" />
              Admin
            </Button>
          </Link>
        )}
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start gap-2"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        >
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          {theme === "dark" ? "Light Mode" : "Dark Mode"}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start gap-2 text-muted-foreground"
          onClick={onLogout}
        >
          <LogOut className="h-4 w-4" />
          {userName ? `Sign out (${userName.split("@")[0]})` : "Sign out"}
        </Button>
      </div>
    </aside>
  );
}
