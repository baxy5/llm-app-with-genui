import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET() {
  try {
    const res = await fetch(`${BACKEND_URL}/health`);

    if (!res) return NextResponse.json({ online: false });

    const data = await res.json();
    return NextResponse.json({ online: data.status === "ok" });
  } catch {
    return NextResponse.json({ online: false });
  }
}
