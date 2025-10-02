import { IChatSessionsResponse } from "@/schemas/api-responses";
import { NextResponse } from "next/server";

// TYPE
export async function GET() {
  try {
    const backendUrl = process.env.BACKEND_URL;

    if (!backendUrl) {
      return NextResponse.json(
        {
          error: "Backend URL not configured.",
        },
        {
          status: 500,
        }
      );
    }

    const response = await fetch(`${backendUrl}/chat_sessions/sessions`);

    if (!response.ok) {
      console.error("Failed to fetch chat sessions:", response.statusText);
      return NextResponse.json(
        { error: "Failed to fetch chat sessions." },
        { status: response.status }
      );
    }

    const data: IChatSessionsResponse[] = await response.json();

    if (data.length === 0) {
      return NextResponse.json(
        { error: "No chat sessions found." },
        { status: 404 }
      );
    }

    const latestSession = data.reduce((a, b) =>
      new Date(a.created_at) > new Date(b.created_at) ? a : b
    );

    const sessionId = latestSession.session_id + 1;

    return NextResponse.json({ sessionId });
  } catch (err) {
    console.error("Error in latest-session-id API:", err);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
