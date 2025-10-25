import ChatContainer from "@/components/chat/chat-container";
import { getLatestSessionId, isServerOnline } from "@/lib/data";

export default async function Home() {
  const isOnline = await isServerOnline();

  if (!isOnline) {
    return (
      <div>
        <h2>Server offline</h2>
        <p>The backend is currently unavailable. Please try again later.</p>
      </div>
    );
  }

  const sessionId = await getLatestSessionId();

  return (
    <>
      <ChatContainer mess={[]} slug={sessionId?.toString()} />
    </>
  );
}
