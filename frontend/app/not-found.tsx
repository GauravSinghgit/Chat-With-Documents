import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Bot } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-4 text-center">
      <div className="rounded-full bg-primary/10 p-4">
        <Bot className="h-8 w-8 text-primary" />
      </div>
      <div>
        <h1 className="text-lg font-semibold">Page not found</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          The page you&apos;re looking for doesn&apos;t exist.
        </p>
      </div>
      <Button asChild>
        <Link href="/chat">Back to chat</Link>
      </Button>
    </div>
  );
}
