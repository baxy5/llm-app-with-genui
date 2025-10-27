export async function getMessages(slug: string) {
  const res = await fetch(
    `http://localhost:3000/api/chat/messages?slug=${slug}`
  );
  const data = await res.json();

  return data.data || [];
}

export async function getChatSessions() {
  const res = await fetch(`http://localhost:3000/api/chat/sessions`, {
    method: "GET",
  });

  const data = await res.json();

  return data.data || [];
}

export async function getFiles(sessionId: string) {
  const res = await fetch(
    `http://localhost:3000/api/chat/files?session_id=${sessionId}`,
    {
      method: "GET",
    }
  );

  const data = await res.json();

  return data.data || [];
}

export async function getLatestSessionId() {
  const res = await fetch("http://localhost:3000/api/chat/latest-session-id");
  const data = await res.json();

  return data.sessionId;
}

export async function deleteChatSessionById(session_id: string) {
  const res = await fetch(
    `http://localhost:3000/api/chat/sessions?session_id=${session_id}`,
    {
      method: "DELETE",
    }
  );

  const data = await res.json();

  return data;
}

export async function isServerOnline() {
  const data = await fetch("http://localhost:3000/api/health");

  const res = await data.json();

  return res.online;
}
