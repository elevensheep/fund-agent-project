"use client";

import React, { useState } from "react";
import { useAgentStore } from "@/stores/useAgentStore";
import { useAgentStream } from "@/hooks/useAgentStream";
import { POPULAR_STOCKS } from "@/lib/mockData";
import { formatKRW, formatPercent } from "@/lib/formatters";
import { ArrowRight, Flame, Layers, Search, Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/Button";

export const SearchBar: React.FC = () => {
  const { query, setQuery, isAnalyzing, ticker, stockName, isCached, cachedAt, ttlRemaining } = useAgentStore();
  const { startAnalysis } = useAgentStream();
  const [inputValue, setInputValue] = useState(query);

  const handleSubmit = (e?: React.FormEvent, forceRefresh: boolean = false) => {
    if (e) e.preventDefault();
    if (!inputValue.trim() || isAnalyzing) return;
    setQuery(inputValue);
    startAnalysis(inputValue, forceRefresh);
  };

  const handleSelectStock = (stockTicker: string, name: string) => {
    const newQuery = `${name}(${stockTicker}) 종합 분석 및 투자 심의해줘`;
    setInputValue(newQuery);
    setQuery(newQuery);
    startAnalysis(newQuery);
  };

  return (
    <div className="w-full flex flex-col gap-3">
      {/* Search Input Bar */}
      <form onSubmit={(e) => handleSubmit(e, false)} className="relative w-full">
        <div className="relative flex items-center w-full rounded-2xl bg-slate-900/90 border border-slate-700/80 shadow-xl focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all">
          <div className="pl-4 text-slate-400">
            <Search className="w-5 h-5" />
          </div>

          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="종목명 또는 6자리 종목코드 입력 (예: 삼성전자, 000660, 현대차 투자 심의해줘)"
            className="w-full h-14 pl-3 pr-44 bg-transparent text-sm md:text-base text-slate-100 placeholder-slate-500 focus:outline-none"
            disabled={isAnalyzing}
          />

          {inputValue && !isAnalyzing && (
            <button
              type="button"
              onClick={() => setInputValue("")}
              className="p-1 mr-2 text-slate-500 hover:text-slate-300 rounded-md transition"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          <div className="absolute right-2 flex items-center gap-1.5">
            {isCached && !isAnalyzing && (
              <button
                type="button"
                onClick={() => handleSubmit(undefined, true)}
                title="캐시를 무시하고 8대 서브 에이전트를 실시간으로 재실행합니다"
                className="hidden sm:flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-400 hover:text-amber-300 border border-amber-500/30 text-xs font-semibold transition"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>강제 재분석</span>
              </button>
            )}

            <Button
              type="submit"
              variant="primary"
              size="md"
              isLoading={isAnalyzing}
              disabled={!inputValue.trim() || isAnalyzing}
              className="gap-2 px-5 font-bold text-xs md:text-sm"
            >
              <Sparkles className="w-4 h-4" />
              {isAnalyzing ? "분석 중" : "분석 시작"}
            </Button>
          </div>
        </div>
      </form>

      {/* Cache Status Banner if cached */}
      {isCached && (
        <div className="flex items-center justify-between px-3.5 py-2 rounded-xl bg-amber-950/40 border border-amber-800/50 text-amber-300 text-xs">
          <div className="flex items-center gap-2">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
            </span>
            <span className="font-semibold">⚡ Redis 고속 캐시 적용됨</span>
            <span className="text-amber-400/80 text-[11px] hidden sm:inline">
              (동일 종목 최근 분석 결과가 캐시에서 즉시 로드되었습니다{ttlRemaining ? ` • 잔여 TTL: ${ttlRemaining}초` : ""})
            </span>
          </div>
          <button
            type="button"
            onClick={() => handleSubmit(undefined, true)}
            disabled={isAnalyzing}
            className="font-bold underline text-amber-200 hover:text-white transition text-xs flex items-center gap-1"
          >
            실시간 갱신하기 →
          </button>
        </div>
      )}

      {/* Popular Stock Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs no-scrollbar">
        <div className="flex items-center gap-1 text-slate-400 font-medium whitespace-nowrap pl-1 pr-2">
          <Flame className="w-3.5 h-3.5 text-rose-500" />
          <span>실시간 인기 종목:</span>
        </div>

        {POPULAR_STOCKS.map((stock) => {
          const isSelected = stock.ticker === ticker;
          const isUp = stock.change >= 0;

          return (
            <button
              key={stock.ticker}
              type="button"
              onClick={() => handleSelectStock(stock.ticker, stock.name)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border transition-all whitespace-nowrap ${
                isSelected
                  ? "bg-blue-950/80 border-blue-500/80 text-blue-200 ring-1 ring-blue-500/40 shadow-sm"
                  : "bg-slate-900/60 hover:bg-slate-800 border-slate-800/80 text-slate-300"
              }`}
            >
              <span className="font-semibold text-slate-200">{stock.name}</span>
              <span className="font-mono text-slate-400 text-[11px]">{formatKRW(stock.price)}</span>
              <span
                className={`font-mono text-[11px] font-bold ${
                  isUp ? "text-rose-400" : "text-blue-400"
                }`}
              >
                {formatPercent(stock.changePercent, { includeSign: true, decimals: 1 })}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
