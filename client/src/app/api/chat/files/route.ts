import { NextResponse } from "next/server";

export async function GET(request: Request) {
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
        { error: "Missing sessionId parameter" },
        { status: 400 }
      );
    }

    const response = await fetch(
      `${backendUrl}/chat_sessions/files?session_id=${sessionId}`
    );

    if (!response.ok) {
      console.error("Failed to fetch files:", response.statusText);
      return NextResponse.json(
        { error: "Failed to fetch files." },
        { status: response.status }
      );
    }

    const data: string[] = await response.json();

    return NextResponse.json({ data });
  } catch (err) {
    console.error("Error in files API:", err);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
