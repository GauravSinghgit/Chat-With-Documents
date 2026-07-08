"use client";

import { useState } from "react";
import { Bot, Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { ChatSidebar } from "./ChatSidebar";

interface AppShellProps {
  children: React.ReactNode;
  onLogout: () => void;
  userName?: string;
  isAdmin?: boolean;
  activeConversationId?: string;
}

/** Shared responsive shell used by the chat/documents/admin layouts: a
 * fixed sidebar on desktop, collapsed behind a Sheet + hamburger on mobile. */
export function AppShell({ children, ...sidebarProps }: AppShellProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">
      <div className="hidden md:flex">
        <ChatSidebar {...sidebarProps} />
      </div>

      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="flex items-center gap-2 border-b p-3 md:hidden">
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" aria-label="Open menu">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-64 p-0" onClick={() => setOpen(false)}>
              <SheetTitle className="sr-only">Navigation</SheetTitle>
              <ChatSidebar {...sidebarProps} />
            </SheetContent>
          </Sheet>
          <Bot className="h-5 w-5 text-primary" />
          <span className="text-sm font-semibold">AI Assistant</span>
        </div>
        <main className="flex-1 overflow-hidden">{children}</main>
      </div>
    </div>
  );
}
