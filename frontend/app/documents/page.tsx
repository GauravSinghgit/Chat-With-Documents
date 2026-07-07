"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { documentsApi } from "@/lib/api/documents";
import type { Document } from "@/lib/api/types";
import { toast } from "sonner";
import {
  Upload,
  Trash2,
  MoreHorizontal,
  FileText,
  FileType2,
  RefreshCw,
  Loader2,
  CheckCircle,
  Clock,
  AlertCircle,
  MessageSquare,
} from "lucide-react";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<
    string,
    {
      variant: "default" | "secondary" | "destructive" | "outline";
      icon: React.ReactNode;
      label: string;
    }
  > = {
    indexed: { variant: "default", icon: <CheckCircle className="h-3 w-3" />, label: "Indexed" },
    processing: { variant: "secondary", icon: <Clock className="h-3 w-3" />, label: "Processing" },
    failed: { variant: "destructive", icon: <AlertCircle className="h-3 w-3" />, label: "Failed" },
  };
  const s = map[status] ?? map.indexed;
  return (
    <Badge variant={s.variant} className="gap-1 text-xs">
      {s.icon}
      {s.label}
    </Badge>
  );
}

export default function DocumentsPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [reindexingId, setReindexingId] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocs = useCallback(async () => {
    setLoading(true);
    const result = await documentsApi.list();
    if (result.ok) {
      setDocuments(result.data.documents);
      setTotal(result.data.total);
    } else {
      toast.error(`Failed to load documents: ${result.error}`);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchDocs();
  }, [fetchDocs]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;

    setUploading(true);
    const result = await documentsApi.upload(files, true);
    setUploading(false);

    if (result.ok) {
      toast.success(`Uploaded ${result.data.ingested} file(s) successfully`);
      fetchDocs();
    } else {
      toast.error(result.error || "Upload failed");
    }
    // Reset file input
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleDelete = async (doc: Document) => {
    const result = await documentsApi.delete(doc.id);
    if (result.ok) {
      setDocuments((prev) => prev.filter((d) => d.id !== doc.id));
      setTotal((t) => t - 1);
      toast.success(`Deleted "${doc.original_filename}"`);
    } else {
      toast.error("Failed to delete document");
    }
  };

  const handleStartChat = (doc: Document) => {
    const chatId = crypto.randomUUID();
    const params = new URLSearchParams({
      doc_id: String(doc.id),
      doc_name: doc.original_filename,
    });
    router.push(`/chat/${chatId}?${params.toString()}`);
  };

  const handleReindex = async (doc: Document) => {
    setReindexingId(doc.id);
    const result = await documentsApi.reindex(doc.id);
    setReindexingId(null);
    if (result.ok) {
      toast.success(`Re-indexed "${doc.original_filename}" — ${result.data.chunks} chunks`);
      fetchDocs();
    } else {
      toast.error("Re-indexing failed");
    }
  };

  return (
    <div className="flex h-screen flex-col">
      {/* Header */}
      <header className="flex items-center gap-4 border-b bg-background px-6 py-4">
        <div>
          <h1 className="text-lg font-semibold">Knowledge Base</h1>
          <p className="text-xs text-muted-foreground">
            {total} document{total !== 1 ? "s" : ""} indexed
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchDocs} className="gap-2">
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </Button>
          <Button
            size="sm"
            className="gap-2"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
          >
            {uploading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Upload className="h-4 w-4" />
            )}
            Upload Files
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.txt,.md"
            className="hidden"
            onChange={handleUpload}
          />
        </div>
      </header>

      {/* Upload hint */}
      <div
        className="mx-6 mt-4 cursor-pointer rounded-lg border-2 border-dashed border-border bg-muted/30 px-6 py-8 text-center transition-colors hover:bg-muted/50"
        onClick={() => fileInputRef.current?.click()}
      >
        <Upload className="mx-auto mb-2 h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium">Drop files here or click to upload</p>
        <p className="mt-1 text-xs text-muted-foreground">
          Supports PDF, TXT, MD — max 10 MB per file
        </p>
      </div>

      <Separator className="mt-4" />

      {/* Document list */}
      <div className="flex-1 overflow-auto px-6 py-4">
        {loading ? (
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-20 w-full rounded-lg" />
            ))}
          </div>
        ) : documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
            <FileText className="h-12 w-12 text-muted-foreground/50" />
            <h2 className="font-semibold">No documents yet</h2>
            <p className="text-sm text-muted-foreground">
              Upload PDF or TXT files to enable intelligent document search.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {documents.map((doc) => (
              <Card key={doc.id} className="transition-shadow hover:shadow-sm">
                <CardContent className="p-4">
                  <div className="flex items-start gap-4">
                    <div className="shrink-0 rounded-md bg-primary/10 p-2">
                      {doc.file_type === "pdf" ? (
                        <FileType2 className="h-5 w-5 text-primary" />
                      ) : (
                        <FileText className="h-5 w-5 text-primary" />
                      )}
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="truncate text-sm font-medium">{doc.original_filename}</h3>
                        <StatusBadge status={doc.status} />
                        <Badge variant="outline" className="text-xs">
                          {doc.file_type.toUpperCase()}
                        </Badge>
                      </div>

                      {doc.summary && (
                        <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                          {doc.summary}
                        </p>
                      )}

                      <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
                        <span>{doc.chunk_count} chunks</span>
                        {doc.page_count > 1 && <span>{doc.page_count} pages</span>}
                        <span>{formatBytes(doc.file_size)}</span>
                        <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>

                    <div className="flex shrink-0 items-center gap-1">
                      {doc.status === "indexed" && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-8 gap-1.5 text-xs"
                          onClick={() => handleStartChat(doc)}
                        >
                          <MessageSquare className="h-3.5 w-3.5" />
                          Chat
                        </Button>
                      )}
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={() => handleReindex(doc)}
                            disabled={reindexingId === doc.id}
                          >
                            {reindexingId === doc.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <RefreshCw className="h-4 w-4" />
                            )}
                            Re-index
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-destructive"
                            onClick={() => handleDelete(doc)}
                          >
                            <Trash2 className="h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
