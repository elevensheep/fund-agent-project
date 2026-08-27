import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:28000";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const ticker = searchParams.get("ticker") || "005930";
  const timeframe = searchParams.get("timeframe") || "1D";
  const count = searchParams.get("count") || "60";

  try {
    const res = await fetch(
      `${BACKEND_URL}/api/v1/stock/candles?ticker=${ticker}&timeframe=${timeframe}&count=${count}`,
      {
        headers: { "Content-Type": "application/json" },
        cache: "no-store",
      }
    );

    if (!res.ok) {
      return NextResponse.json({ error: `Backend returned ${res.status}` }, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error: any) {
    return NextResponse.json({ error: error.message || "Failed to fetch stock candles" }, { status: 500 });
  }
}
