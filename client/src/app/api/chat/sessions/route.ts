import { IChatSessionsResponse } from "@/schemas/api-responses";
import { NextResponse } from "next/server";

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
      const emptyData: IChatSessionsResponse[] = [];
      return NextResponse.json({ emptyData });
    }

    return NextResponse.json({ data });
  } catch (err) {
    console.error("Error in sessions API:", err);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function DELETE(request: Request) {
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

    const { searchParams } = new URL(request.url);
    const sessionId = searchParams.get("session_id");

    if (!sessionId) {
      return NextResponse.json(
        { error: "Missing session_id parameter" },
        { status: 400 }
      );
    }

    const response = await fetch(
      `${backendUrl}/chat_sessions/delete_session?session_id=${sessionId}`,
      {
        method: "DELETE",
      }
    );

    if (!response.ok) {
      console.error("Failed to delete chat session:", response.statusText);
      return NextResponse.json(
        { error: "Failed to delete chat session." },
        { status: response.status }
      );
    }

    return NextResponse.json(
      {
        message: "Chat session deleted successfully.",
        sessionId: sessionId,
      },
      { status: 200 }
    );
  } catch (err) {
    console.error("Error in sessions DELETE API:", err);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
