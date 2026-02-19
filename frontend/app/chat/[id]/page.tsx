import { ChatInterface } from "@/components/chat/ChatInterface";

interface Props {
  params: Promise<{ id: string }>;
}

export default async function ConversationPage({ params }: Props) {
  const { id } = await params;
  return <ChatInterface conversationId={id} />;
}
