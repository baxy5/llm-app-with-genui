import ChatContainer from "@/components/chat/chat-container";
import Layout from "@/components/layout";
import { getMessages } from "@/lib/data";
import { IChatMessagesResponse } from "@/schemas/api-responses";
import { notFound } from "next/navigation";

const ChatSessionPage = async ({
  params,
}: {
  params: Promise<{ slug: string }>;
}) => {
  const { slug } = await params;

  const messages: IChatMessagesResponse[] = await getMessages(slug);

  if (!messages || messages.length === 0) {
    notFound();
  }

  return (
    <>
      <Layout>
        <ChatContainer mess={messages || []} slug={slug} />
      </Layout>
    </>
  );
};

export default ChatSessionPage;
