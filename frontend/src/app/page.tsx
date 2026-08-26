"use client";

import React, { useMemo } from "react";
import { useAgentStore } from "@/stores/useAgentStore";
import { useStockPrice } from "@/hooks/useStockPrice";
import { generateCandleSeries } from "@/lib/mockData";
import { formatKRW, formatPercent } from "@/lib/formatters";

// Common UI
import { Header } from "@/components/common/Header";
import { SearchBar } from "@/components/common/SearchBar";
import { SystemStatus } from "@/components/common/SystemStatus";

// DAG & Chart
import { DagTracker } from "@/components/dag/DagTracker";
import { StockChart } from "@/components/chart/StockChart";

// Insight Cards
import { TechnicalCard } from "@/components/insights/TechnicalCard";
import { FundamentalCard } from "@/components/insights/FundamentalCard";
import { DartDisclosureCard } from "@/components/insights/DartDisclosureCard";
import { MacroSectorCard } from "@/components/insights/MacroSectorCard";
import { BullBearDebateCard } from "@/components/insights/BullBearDebateCard";
import { RiskGatekeeperCard } from "@/components/insights/RiskGatekeeperCard";
import { DataProcessingCard } from "@/components/insights/DataProcessingCard";
import { WebSearchCard } from "@/components/insights/WebSearchCard";

// Report & Monitoring
import { ReportViewer } from "@/components/report/ReportViewer";
import { GrafanaEmbed } from "@/components/monitoring/GrafanaEmbed";
import { ArrowUpRight, CheckCircle2, Shield, Sparkles, TrendingUp, Zap } from "lucide-react";

export default function DashboardPage() {
  const {
    ticker,
    stockName,
    plan,
    currentStepId,
    completedAgents,
    stepResults,
    finalReport,
    isAnalyzing,
    activeTab,
  } = useAgentStore();

  const quote = useStockPrice(ticker);

  // Generate Candlestick and SMA dataset based on current stock price
  const { candles, sma20, sma60 } = useMemo(() => {
    return generateCandleSeries(quote.price, 60);
  }, [quote.price]);

  const isUp = quote.change >= 0;

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <SystemStatus />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Top Search & Stock Overview Banner */}
        <section className="flex flex-col gap-4">
          <SearchBar />

          {/* Active Stock Summary Bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-700 flex items-center justify-center font-bold text-lg text-white shadow-md shadow-blue-500/20">
                {stockName.slice(0, 1)}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-bold text-slate-100">{stockName}</h2>
                  <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                    {ticker} • {quote.market}
                  </span>
                </div>
                <div className="flex items-baseline gap-2 mt-0.5">
                  <span className="text-2xl font-black font-mono tracking-tight text-white">
                    {formatKRW(quote.price)}
                  </span>
                  <span
                    className={`text-sm font-mono font-bold flex items-center gap-0.5 ${
                      isUp ? "text-rose-400" : "text-blue-400"
                    }`}
                  >
                    {isUp ? "▲" : "▼"} {formatKRW(Math.abs(quote.change))} (
                    {formatPercent(quote.changePercent, { includeSign: true })})
                  </span>
                </div>
              </div>
            </div>

            {/* Micro Stats */}
            <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
              <div className="hidden sm:block">
                <span className="text-slate-500 block text-[10px]">당일 고가</span>
                <span className="text-rose-400 font-bold">{formatKRW(quote.high)}</span>
              </div>
              <div className="hidden sm:block">
                <span className="text-slate-500 block text-[10px]">당일 저가</span>
                <span className="text-blue-400 font-bold">{formatKRW(quote.low)}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">누적 거래량</span>
                <span className="text-slate-200 font-bold">
                  {quote.volume.toLocaleString("ko-KR")}주
                </span>
              </div>
              <div className="hidden md:block">
                <span className="text-slate-500 block text-[10px]">시세 갱신</span>
                <span className="text-slate-400">{quote.updatedAt}</span>
              </div>
            </div>
          </div>
        </section>

        {/* Plan-and-Execute DAG Pipeline Tracker */}
        <section>
          <DagTracker
            plan={plan}
            currentStep={currentStepId}
            completedAgents={completedAgents}
            isAnalyzing={isAnalyzing}
          />
        </section>

        {/* Tab 1: Comprehensive Dashboard View */}
        {activeTab === "dashboard" && (
          <div className="space-y-6">
            {/* Top Grid: TradingView Chart + Real-time Data Processing */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <StockChart
                  data={candles}
                  sma20={sma20}
                  sma60={sma60}
                  ticker={ticker}
                  stockName={stockName}
                />
              </div>
              <div className="space-y-6">
                <DataProcessingCard data={stepResults.data_processing_agent} />
                <WebSearchCard data={stepResults.web_search_agent} />
              </div>
            </div>

            {/* 4-Domain Parallel Deep Analysis Cards */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4 text-blue-400" />
                <h3 className="text-sm font-bold text-slate-200">
                  2단계: 4대 영역 심층 병렬 분석 (Deep Domain Analysis)
                </h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FundamentalCard data={stepResults.fundamental_agent} />
                <TechnicalCard data={stepResults.technical_agent} />
                <DartDisclosureCard data={stepResults.dart_disclosure_agent} />
                <MacroSectorCard data={stepResults.macro_sector_agent} />
              </div>
            </div>

            {/* 3rd & 4th Steps: Bull vs Bear Debate + 100% Rule-Based Risk Gatekeeper */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Shield className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-bold text-slate-200">
                  3~4단계: 대립 토론 판정 & 100% Rule-Based 리스크 심의
                </h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <BullBearDebateCard data={stepResults.bull_bear_debate_agent} />
                <RiskGatekeeperCard data={stepResults.risk_management_agent} />
              </div>
            </div>

            {/* Final Report Section */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle2 className="w-4 h-4 text-blue-400" />
                <h3 className="text-sm font-bold text-slate-200">
                  최종 오케스트레이터 종합 투자 의견서
                </h3>
              </div>
              <ReportViewer
                reportMarkdown={finalReport}
                ticker={ticker}
                stockName={stockName}
                isAnalyzing={isAnalyzing}
              />
            </div>
          </div>
        )}

        {/* Tab 2: DAG Pipeline Focus View */}
        {activeTab === "dag" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <DataProcessingCard data={stepResults.data_processing_agent} />
              <WebSearchCard data={stepResults.web_search_agent} />
              <FundamentalCard data={stepResults.fundamental_agent} />
              <TechnicalCard data={stepResults.technical_agent} />
              <DartDisclosureCard data={stepResults.dart_disclosure_agent} />
              <MacroSectorCard data={stepResults.macro_sector_agent} />
              <BullBearDebateCard data={stepResults.bull_bear_debate_agent} />
              <RiskGatekeeperCard data={stepResults.risk_management_agent} />
            </div>
          </div>
        )}

        {/* Tab 3: Final Report Focus View */}
        {activeTab === "report" && (
          <div className="space-y-6">
            <ReportViewer
              reportMarkdown={finalReport}
              ticker={ticker}
              stockName={stockName}
              isAnalyzing={isAnalyzing}
            />
          </div>
        )}

        {/* Tab 4: Observability & Monitoring View */}
        {activeTab === "monitoring" && (
          <div className="space-y-6">
            <GrafanaEmbed />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-slate-800/60 bg-slate-950/80 py-6 mt-12 text-center text-xs text-slate-500">
        <p>
          Financial Multi-Agent Ecosystem • FastMCP SSE & Google ADK A2A JSON-RPC 2.0 Protocol
        </p>
        <p className="mt-1 text-[11px] text-slate-600">
          모든 투자 판단의 책임은 본인에게 있으며, 본 시스템은 AI 다중 에이전트 기반 의사결정 보조 솔루션입니다.
        </p>
      </footer>
    </div>
  );
}
