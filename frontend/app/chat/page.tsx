"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { MessageSquarePlus, FileText, Bot } from "lucide-react";

export default function ChatHomePage() {
  const router = useRouter();

  return (
    <div className="flex h-full flex-col items-center justify-center gap-6 p-8 text-center">
      <div className="rounded-full bg-primary/10 p-5">
        <Bot className="h-10 w-10 text-primary" />
      </div>
      <div>
        <h1 className="mb-2 text-2xl font-bold">AI Assistant Platform</h1>
        <p className="max-w-md text-muted-foreground">
          Start a new conversation, or upload documents to enable intelligent document search with
          RAG.
        </p>
      </div>
      <div className="flex gap-3">
        <Button onClick={() => router.push(`/chat/${crypto.randomUUID()}`)} className="gap-2">
          <MessageSquarePlus className="h-4 w-4" />
          New Chat
        </Button>
        <Button variant="outline" onClick={() => router.push("/documents")} className="gap-2">
          <FileText className="h-4 w-4" />
          Manage Documents
        </Button>
      </div>
    </div>
  );
}
