import { ChatInterface } from "@/components/chat/ChatInterface";

interface Props {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ doc_name?: string; doc_id?: string }>;
}

export default async function ConversationPage({ params, searchParams }: Props) {
  const { id } = await params;
  const sp = await searchParams;
  return (
    <ChatInterface
      conversationId={id}
      docName={sp.doc_name ? decodeURIComponent(sp.doc_name) : undefined}
      docId={sp.doc_id ? Number(sp.doc_id) : undefined}
    />
  );
}
