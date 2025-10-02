import ChatContainer from "@/components/chat/chat-container";
import { getMessages } from "@/lib/data";
import { IChatMessagesResponse } from "@/schemas/api-responses";

const ChatSessionPage = async ({
  params,
}: {
  params: Promise<{ slug: string }>;
}) => {
  const { slug } = await params;

  const messages: IChatMessagesResponse[] = await getMessages(slug);

  return (
    <>
      <ChatContainer mess={messages || []} slug={slug} />
    </>
  );
};

export default ChatSessionPage;
