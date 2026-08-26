import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Financial Multi-Agent Ecosystem | 고성능 분산 금융 분석 대시보드",
  description:
    "Next.js 14, TradingView Lightweight Charts, A2A JSON-RPC 2.0, MCP FastMCP SSE 기반 분산 8대 금융 전문 서브 에이전트 오케스트레이션 플랫폼",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" className="dark">
      <body className="antialiased min-h-screen bg-[#050811] text-slate-100 flex flex-col selection:bg-blue-600 selection:text-white">
        {children}
      </body>
    </html>
  );
}
