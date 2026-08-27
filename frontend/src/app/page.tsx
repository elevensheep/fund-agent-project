"use client";

import React, { useMemo } from "react";
import { useAgentStore } from "@/stores/useAgentStore";
import { useStockPrice } from "@/hooks/useStockPrice";
import { formatKRW, formatPercent } from "@/lib/formatters";

// Common UI
import { Header } from "@/components/common/Header";
import { SearchBar } from "@/components/common/SearchBar";
import { SystemStatus } from "@/components/common/SystemStatus";
import { WatchlistBar } from "@/components/watchlist/WatchlistBar";

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

// Report, Recommendation & Monitoring
import { RecommendationView } from "@/components/recommendation/RecommendationView";
import { ReportViewer } from "@/components/report/ReportViewer";
import { GrafanaEmbed } from "@/components/monitoring/GrafanaEmbed";
import { useAgentStream } from "@/hooks/useAgentStream";
import { useStockCandles } from "@/hooks/useStockCandles";
import { ArrowUpRight, CheckCircle2, Database, Flame, Layers, Radio, Scale, Search, Shield, Sparkles, TrendingUp, Zap } from "lucide-react";

export default function DashboardPage() {
  const {
    ticker,
    stockName,
    query,
    plan,
    currentStepId,
    completedAgents,
    stepResults,
    recommendation,
    finalReport,
    isAnalyzing,
    activeTab,
    setActiveTab,
  } = useAgentStore();

  const { startAnalysis } = useAgentStream();
  const { quote } = useStockPrice(ticker);
  const {
    candles,
    sma20,
    sma60,
    timeframe,
    setTimeframe,
    isLoading: isCandlesLoading,
    isEmpty: isCandlesEmpty,
  } = useStockCandles(ticker);

  const isUp = (quote?.change ?? 0) >= 0;

  const triggerThemeRecommendation = (themePrompt: string) => {
    setActiveTab("recommendation");
    startAnalysis(themePrompt);
  };

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <SystemStatus />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Real-time Dynamic Stream Watchlist Bar */}
        <section>
          <WatchlistBar />
        </section>

        {/* Top Search & Preset Recommendation Chips */}
        <section className="flex flex-col gap-3">
          <SearchBar />

          {/* Quick Preset Theme Recommendation Chips */}
          <div className="flex items-center gap-2 overflow-x-auto scrollbar-none py-1">
            <span className="text-[11px] font-bold text-slate-400 flex items-center gap-1 flex-shrink-0">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              AI 테마 추천:
            </span>
            <button
              type="button"
              onClick={() => triggerThemeRecommendation("AI 반도체 및 HBM 주도 유망주 추천해줘")}
              className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-950/40 hover:bg-blue-900/60 border border-blue-800/60 text-blue-300 transition flex items-center gap-1.5 flex-shrink-0"
            >
              <Flame className="w-3 h-3 text-orange-400" />
              <span>🔥 AI 반도체 Top Picks</span>
            </button>
            <button
              type="button"
              onClick={() => triggerThemeRecommendation("저PBR 밸류업 및 고배당 우량주 추천해줘")}
              className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950/40 hover:bg-emerald-900/60 border border-emerald-800/60 text-emerald-300 transition flex items-center gap-1.5 flex-shrink-0"
            >
              <span>💎 저PBR 밸류업 추천</span>
            </button>
            <button
              type="button"
              onClick={() => triggerThemeRecommendation("외인 기관 쌍끌이 수급 모멘텀 급등주 추천해줘")}
              className="px-3 py-1 rounded-full text-xs font-semibold bg-purple-950/40 hover:bg-purple-900/60 border border-purple-800/60 text-purple-300 transition flex items-center gap-1.5 flex-shrink-0"
            >
              <TrendingUp className="w-3 h-3 text-purple-400" />
              <span>🚀 외인·기관 쌍끌이 Top Picks</span>
            </button>
          </div>

          {/* Active Stock Summary Bar — shown only when a stock is selected */}
          {ticker ? (
            <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-700 flex items-center justify-center font-bold text-lg text-white shadow-md shadow-blue-500/20">
                  {stockName.slice(0, 1)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold text-slate-100">{stockName}</h2>
                    <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {ticker} • {quote?.market || "KOSPI"}
                    </span>
                  </div>
                  <div className="flex items-baseline gap-2 mt-0.5">
                    <span className="text-2xl font-black font-mono tracking-tight text-white">
                      {quote ? formatKRW(quote.price) : "시세 조회 중..."}
                    </span>
                    {quote && (
                      <span
                        className={`text-sm font-mono font-bold flex items-center gap-0.5 ${
                          isUp ? "text-rose-400" : "text-blue-400"
                        }`}
                      >
                        {isUp ? "▲" : "▼"} {formatKRW(Math.abs(quote.change))} (
                        {formatPercent(quote.changePercent, { includeSign: true })})
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Micro Stats */}
              <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
                <div className="hidden sm:block">
                  <span className="text-slate-500 block text-[10px]">당일 고가</span>
                  <span className="text-rose-400 font-bold">{quote ? formatKRW(quote.high) : "-"}</span>
                </div>
                <div className="hidden sm:block">
                  <span className="text-slate-500 block text-[10px]">당일 저가</span>
                  <span className="text-blue-400 font-bold">{quote ? formatKRW(quote.low) : "-"}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px]">누적 거래량</span>
                  <span className="text-slate-200 font-bold">
                    {quote ? `${quote.volume.toLocaleString("ko-KR")}주` : "-"}
                  </span>
                </div>
                <div className="hidden md:block">
                  <span className="text-slate-500 block text-[10px]">시세 갱신</span>
                  <span className="text-slate-400">{quote?.updatedAt || "실시간"}</span>
                </div>
              </div>
            </div>
          ) : !recommendation && (
            /* Empty State — invite user to search */
            <div className="flex flex-col items-center justify-center py-16 px-6 rounded-2xl bg-slate-900/40 border border-slate-800/60 border-dashed">
              <div className="w-16 h-16 rounded-full bg-slate-800/80 flex items-center justify-center mb-4">
                <Search className="w-7 h-7 text-slate-500" />
              </div>
              <h2 className="text-xl font-bold text-slate-300 mb-2">종목을 검색하거나 AI 추천을 시작하세요</h2>
              <p className="text-sm text-slate-500 text-center max-w-md mb-6">
                위 검색창에서 종목명을 입력하거나, 상단의 테마 추천 버튼을 눌러 8대 멀티에이전트가 검증한 모델 포트폴리오를 발굴하세요.
              </p>
              <div className="flex flex-wrap gap-2 justify-center">
                {[
                  { ticker: "005930", name: "삼성전자" },
                  { ticker: "000660", name: "SK하이닉스" },
                  { ticker: "005380", name: "현대차" },
                  { ticker: "035420", name: "NAVER" },
                  { ticker: "051910", name: "LG화학" },
                  { ticker: "005490", name: "POSCO홀딩스" },
                ].map((s) => (
                  <QuickPickChip key={s.ticker} ticker={s.ticker} name={s.name} />
                ))}
              </div>
            </div>
          )}
        </section>

        {/* Tab: Recommendation View */}
        {activeTab === "recommendation" && recommendation && (
          <section>
            <RecommendationView data={recommendation} />
          </section>
        )}

        {/* Plan-and-Execute DAG Pipeline Tracker */}
        {ticker && (
          <section>
            <DagTracker
              plan={plan}
              currentStep={currentStepId}
              completedAgents={completedAgents}
              isAnalyzing={isAnalyzing}
            />
          </section>
        )}

        {/* Tab 1: Comprehensive Dashboard View */}
        {ticker && activeTab === "dashboard" && (
          <div className="space-y-8">
            {/* Top Interactive Full-Width Candlestick Chart */}
            <div>
              <StockChart
                data={candles}
                sma20={sma20}
                sma60={sma60}
                ticker={ticker}
                stockName={stockName}
                isLoading={isCandlesLoading}
                isEmpty={isCandlesEmpty}
                timeframe={timeframe}
                onTimeframeChange={setTimeframe}
              />
            </div>

            {/* 1단계: 실시간 시세 수집 & 웹/뉴스 검색 */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Database className="w-4 h-4 text-blue-400" />
                <h3 className="text-sm font-bold text-slate-200">
                  1단계: 실시간 데이터 수집 & 웹/뉴스 검색 (Real-Time Ingestion & Search)
                </h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <DataProcessingCard data={stepResults.data_processing_agent} />
                <WebSearchCard data={stepResults.web_search_agent} />
              </div>
            </div>

            {/* 2단계: 4대 영역 심층 병렬 분석 */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4 text-indigo-400" />
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

            {/* 3단계: 상승 vs 하락 대립 토론 */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Scale className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-bold text-slate-200">
                  3단계: 상승 vs 하락 대립 토론 & 판사 평결 (Bull vs Bear Debate)
                </h3>
              </div>
              <BullBearDebateCard data={stepResults.bull_bear_debate_agent} />
            </div>

            {/* 4단계: 100% Rule-Based 리스크 관리 심의 */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Shield className="w-4 h-4 text-emerald-400" />
                <h3 className="text-sm font-bold text-slate-200">
                  4단계: 100% Rule-Based 리스크 심의 & 손절선 확정 (CRO Risk Gatekeeping)
                </h3>
              </div>
              <RiskGatekeeperCard data={stepResults.risk_management_agent} />
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
        {ticker && activeTab === "dag" && (
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

/** 퀵픽 종목 칩 — Empty State에서 사용 */
function QuickPickChip({ ticker, name }: { ticker: string; name: string }) {
  const { setStock, setActiveTab } = useAgentStore();
  const { startAnalysis } = useAgentStream();

  const handleClick = () => {
    setStock(ticker, name);
    setActiveTab("dashboard");
    startAnalysis(`${name}(${ticker}) 종합 분석 및 투자 심의해줘`);
  };

  return (
    <button
      onClick={handleClick}
      className="px-3 py-1.5 rounded-full text-xs font-bold bg-slate-800 hover:bg-blue-600/30 border border-slate-700 hover:border-blue-500 text-slate-300 hover:text-blue-300 transition-all duration-150 cursor-pointer"
    >
      {name}
      <span className="ml-1.5 text-[10px] text-slate-500 font-mono">{ticker}</span>
    </button>
  );
}
