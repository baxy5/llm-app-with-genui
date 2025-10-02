import { IChatMessagesResponse } from "@/schemas/api-responses";
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
    const slug = searchParams.get("slug");

    if (!slug) {
      return NextResponse.json(
        { error: "Missing slug parameter" },
        { status: 400 }
      );
    }

    const response = await fetch(
      `${backendUrl}/chat_sessions/messages?session_id=${slug}`
    );

    if (!response.ok) {
      console.error("Failed to fetch messages:", response.statusText);
      return NextResponse.json(
        { error: "Failed to fetch messages." },
        { status: response.status }
      );
    }

    const data: IChatMessagesResponse[] = await response.json();

    if (data.length === 0) {
      return NextResponse.json(
        { error: "No messages found." },
        { status: 404 }
      );
    }

    return NextResponse.json({ data });
  } catch (err) {
    console.error("Error in messages API:", err);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
