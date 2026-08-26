"use client";

import React, { useState } from "react";
import { useAgentStore } from "@/stores/useAgentStore";
import { useAgentStream } from "@/hooks/useAgentStream";
import { POPULAR_STOCKS } from "@/lib/mockData";
import { formatKRW, formatPercent } from "@/lib/formatters";
import { ArrowRight, Flame, Layers, Search, Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/Button";

export const SearchBar: React.FC = () => {
  const { query, setQuery, intent, setIntent, isAnalyzing, ticker, stockName } = useAgentStore();
  const { startAnalysis } = useAgentStream();
  const [inputValue, setInputValue] = useState(query);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputValue.trim() || isAnalyzing) return;
    setQuery(inputValue);
    startAnalysis(inputValue);
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
      <form onSubmit={handleSubmit} className="relative w-full">
        <div className="relative flex items-center w-full rounded-2xl bg-slate-900/90 border border-slate-700/80 shadow-xl focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all">
          <div className="pl-4 text-slate-400">
            <Search className="w-5 h-5" />
          </div>

          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="종목명 또는 6자리 종목코드 입력 (예: 삼성전자, 000660, 현대차 투자 심의해줘)"
            className="w-full h-14 pl-3 pr-28 bg-transparent text-sm md:text-base text-slate-100 placeholder-slate-500 focus:outline-none"
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

          <div className="absolute right-2">
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
