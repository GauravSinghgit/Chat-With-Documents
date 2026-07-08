import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/providers/ThemeProvider";
import { Toaster } from "sonner";

const inter = Inter({ subsets: ["latin"] });

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "AI Assistant Platform",
    template: "%s | AI Assistant Platform",
  },
  description:
    "An AI chat assistant with RAG over your documents, a LangGraph agent with tool use, and streaming responses.",
  openGraph: {
    title: "AI Assistant Platform",
    description:
      "An AI chat assistant with RAG over your documents, a LangGraph agent with tool use, and streaming responses.",
    siteName: "AI Assistant Platform",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "AI Assistant Platform",
    description:
      "An AI chat assistant with RAG over your documents, a LangGraph agent with tool use, and streaming responses.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
          <Toaster richColors position="top-right" />
        </ThemeProvider>
      </body>
    </html>
  );
}
