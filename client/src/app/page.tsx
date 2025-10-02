import ChatContainer from "@/components/chat/chat-container";
import { getLatestSessionId } from "@/lib/data";

export default async function Home() {
  const sessionId = await getLatestSessionId();

  return (
    <>
      <ChatContainer mess={[]} slug={sessionId.toString()} />
    </>
  );
}
