import { NextRequest, NextResponse } from "next/server";

const ORCHESTRATOR_URL =
  process.env.INTERNAL_ORCHESTRATOR_URL ||
  process.env.NEXT_PUBLIC_ORCHESTRATOR_URL ||
  "http://agent_orchestrator_app:28000";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get("query") || "";
  const limit = searchParams.get("limit") || "10";

  if (!query.trim()) {
    return NextResponse.json([]);
  }

  try {
    const res = await fetch(
      `${ORCHESTRATOR_URL}/api/v1/stock/search?query=${encodeURIComponent(query)}&limit=${limit}`,
      {
        headers: { "Content-Type": "application/json" },
        cache: "no-store",
      }
    );

    if (!res.ok) {
      return NextResponse.json([], { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("BFF /api/stock/search error:", error);
    return NextResponse.json([], { status: 500 });
  }
}
