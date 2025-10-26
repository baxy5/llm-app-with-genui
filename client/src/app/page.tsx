import ChatContainer from "@/components/chat/chat-container";
import { getLatestSessionId, isServerOnline } from "@/lib/data";

export default async function Home() {
  const isOnline = await isServerOnline();

  if (!isOnline) {
    throw new Error("Server is unavailable.");
  }

  const sessionId = await getLatestSessionId();

  return (
    <>
      <ChatContainer mess={[]} slug={sessionId?.toString()} />
    </>
  );
}
