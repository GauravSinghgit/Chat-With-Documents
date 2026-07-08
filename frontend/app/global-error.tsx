"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <html lang="en">
      <body className="flex min-h-screen flex-col items-center justify-center gap-4 p-4 text-center">
        <h1 className="text-lg font-semibold">Application error</h1>
        <p className="text-sm text-muted-foreground">
          A critical error occurred. Please reload the page.
        </p>
        <button
          onClick={reset}
          className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-accent"
        >
          Try again
        </button>
      </body>
    </html>
  );
}
