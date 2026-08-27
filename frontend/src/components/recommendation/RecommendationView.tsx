"use client";

import React, { useState } from "react";
import { RecommendationResponse, RecommendedStock } from "@/types/agent";
import { formatKRW, formatPercent } from "@/lib/formatters";
import {
  Award,
  BarChart3,
  Check,
  ChevronRight,
  Compass,
  DollarSign,
  PieChart,
  Plus,
  Shield,
  Sparkles,
  TrendingUp,
  Zap,
} from "lucide-react";
import { useAgentStore } from "@/stores/useAgentStore";
import { useAgentStream } from "@/hooks/useAgentStream";

interface RecommendationViewProps {
  data: RecommendationResponse;
}

export const RecommendationView: React.FC<RecommendationViewProps> = ({ data }) => {
  const { setStock, setActiveTab } = useAgentStore();
  const { startAnalysis } = useAgentStream();
  const [addedTickers, setAddedTickers] = useState<Record<string, boolean>>({});
  const [adding, setAdding] = useState<Record<string, boolean>>({});

  const handleAddToWatchlist = async (s: RecommendedStock) => {
    setAdding((prev) => ({ ...prev, [s.ticker]: true }));
    try {
      const res = await fetch("/api/stock/watchlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker: s.ticker }),
      });
      if (res.ok) {
        setAddedTickers((prev) => ({ ...prev, [s.ticker]: true }));
      }
    } catch (e) {
      console.error("Failed to add to watchlist:", e);
    } finally {
      setAdding((prev) => ({ ...prev, [s.ticker]: false }));
    }
  };

  const handleDeepAnalyze = (s: RecommendedStock) => {
    setStock(s.ticker, s.name);
    setActiveTab("dashboard");
    startAnalysis(`${s.name}(${s.ticker}) 종합 심층 투자 분석 리포트 작성해줘`);
  };

  const { theme, recommended_stocks, portfolio_summary } = data;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-950/50 via-indigo-950/40 to-slate-950/60 border border-blue-800/40 shadow-xl backdrop-blur-md">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-3 py-1 rounded-full bg-blue-500/20 border border-blue-400/40 text-blue-300 text-xs font-bold flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                8대 AI 멀티에이전트 검증 완료 Top Picks
              </span>
              <span className="text-xs text-slate-400 font-mono">100% Rule-Based Pricing Engine</span>
            </div>
            <h2 className="text-2xl font-black text-white tracking-tight">{theme}</h2>
            <p className="text-xs text-slate-300 mt-1">
              거시경제 매크로, DART 공시 오버행 심의, 100% Rule-Based 재무 건전성 및 5대 기술적 지표를 종합하여 엄선된 모델 포트폴리오입니다.
            </p>
          </div>

          {/* Model Portfolio Metrics Pill */}
          <div className="flex items-center gap-4 bg-slate-900/80 p-4 rounded-xl border border-slate-800">
            <div>
              <span className="text-[10px] text-slate-400 block font-medium">총 주식 편입 비중</span>
              <span className="text-lg font-black font-mono text-emerald-400">
                {(portfolio_summary.total_equity_weight * 100).toFixed(0)}%
              </span>
            </div>
            <div className="w-px h-8 bg-slate-800" />
            <div>
              <span className="text-[10px] text-slate-400 block font-medium">현금 완충 비중</span>
              <span className="text-lg font-black font-mono text-slate-300">
                {(portfolio_summary.cash_reserve_weight * 100).toFixed(0)}%
              </span>
            </div>
            <div className="w-px h-8 bg-slate-800" />
            <div>
              <span className="text-[10px] text-slate-400 block font-medium">평균 기대 수익률</span>
              <span className="text-lg font-black font-mono text-rose-400">
                {portfolio_summary.expected_return}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Recommended 3-Column Stock Card Deck */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {recommended_stocks.map((stock) => {
          const isAdded = addedTickers[stock.ticker];
          const isProcessing = adding[stock.ticker];

          return (
            <div
              key={stock.ticker}
              className={`flex flex-col justify-between p-6 rounded-2xl border transition-all shadow-xl backdrop-blur-md ${
                stock.rank === 1
                  ? "bg-slate-950/90 border-blue-500/60 shadow-blue-500/10 ring-1 ring-blue-500/30"
                  : "bg-slate-950/80 border-slate-800/90 hover:border-slate-700"
              }`}
            >
              <div>
                {/* Header Rank Badge */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-7 h-7 rounded-lg flex items-center justify-center font-black text-xs ${
                        stock.rank === 1
                          ? "bg-amber-400 text-slate-950 shadow-md shadow-amber-400/20"
                          : stock.rank === 2
                          ? "bg-slate-300 text-slate-950"
                          : "bg-amber-700 text-white"
                      }`}
                    >
                      {stock.rank}위
                    </span>
                    <div>
                      <h3 className="text-lg font-bold text-slate-100">{stock.name}</h3>
                      <span className="text-xs font-mono text-slate-400">{stock.ticker}</span>
                    </div>
                  </div>

                  <span className="px-2.5 py-1 rounded-full text-xs font-bold border bg-rose-500/15 text-rose-300 border-rose-500/30">
                    +{stock.upside_percent.toFixed(1)}% 기대
                  </span>
                </div>

                {/* Price & Target Range */}
                <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800/80 my-3 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">실시간 현재가 ($P_0$)</span>
                    <span className="text-base font-black font-mono text-white">
                      {formatKRW(stock.current_price)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">적정 목표 밴드</span>
                    <span className="font-bold font-mono text-purple-300">
                      {stock.target_price_str}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">필수 동적 손절선</span>
                    <span className="font-bold font-mono text-rose-400">
                      {formatKRW(stock.stop_loss_price)}
                    </span>
                  </div>
                </div>

                {/* Entry & Weight Strategy */}
                <div className="grid grid-cols-2 gap-2 text-xs my-3">
                  <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/60">
                    <span className="text-slate-500 block text-[10px]">추천 편입 비중</span>
                    <span className="font-bold font-mono text-emerald-400">
                      {(stock.approved_weight * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/60">
                    <span className="text-slate-500 block text-[10px]">재무 건전성 등급</span>
                    <span className="font-bold text-slate-200">{stock.financial_grade}</span>
                  </div>
                </div>

                {/* Key Catalyst */}
                <div className="my-3 text-xs">
                  <span className="text-slate-400 text-[11px] block mb-1">핵심 투자 포인트</span>
                  <p className="text-slate-300 bg-slate-900/40 p-2.5 rounded-lg border border-slate-800/40 leading-relaxed text-[11px]">
                    {stock.key_catalyst}
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-4 border-t border-slate-800/60 space-y-2 mt-2">
                <button
                  type="button"
                  onClick={() => handleDeepAnalyze(stock)}
                  className="w-full py-2.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition shadow-md shadow-blue-600/20"
                >
                  <BarChart3 className="w-3.5 h-3.5" />
                  <span>8대 에이전트 상세 심층 분석 보기</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>

                <button
                  type="button"
                  onClick={() => handleAddToWatchlist(stock)}
                  disabled={isAdded || isProcessing}
                  className={`w-full py-2 px-4 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition border ${
                    isAdded
                      ? "bg-emerald-950/40 border-emerald-800/60 text-emerald-300"
                      : "bg-slate-900 hover:bg-slate-850 border-slate-800 text-slate-300 hover:text-white"
                  }`}
                >
                  {isAdded ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span>관심종목(실시간 폴링) 등록 완료</span>
                    </>
                  ) : (
                    <>
                      <Plus className="w-3.5 h-3.5" />
                      <span>{isProcessing ? "등록 중..." : "관심종목(Watchlist)에 추가"}</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
