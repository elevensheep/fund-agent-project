"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { useAgentStore } from "@/stores/useAgentStore";
import { useAgentStream } from "@/hooks/useAgentStream";
import { ArrowRight, Database, Search, Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface SearchResultItem {
  ticker: string;
  name: string;
  market: "KOSPI" | "KOSDAQ" | string;
  sector?: string;
  default_price?: number;
}

export const SearchBar: React.FC = () => {
  const {
    query,
    setQuery,
    setStock,
    isAnalyzing,
    ticker,
    isCached,
    ttlRemaining,
  } = useAgentStore();
  const { startAnalysis } = useAgentStream();

  const [inputValue, setInputValue] = useState("");
  const [suggestions, setSuggestions] = useState<SearchResultItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [highlightIdx, setHighlightIdx] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  // Orchestrator backend stock search API debounced call
  const performSearch = useCallback(async (text: string) => {
    if (!text.trim()) {
      setSuggestions([]);
      setIsOpen(false);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    try {
      const res = await fetch(`/api/stock/search?query=${encodeURIComponent(text.trim())}&limit=10`);
      if (res.ok) {
        const data: SearchResultItem[] = await res.json();
        setSuggestions(data);
        setIsOpen(data.length > 0);
      } else {
        setSuggestions([]);
      }
    } catch (err) {
      console.error("Stock search failed:", err);
      setSuggestions([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  const handleInputChange = (value: string) => {
    setInputValue(value);
    setHighlightIdx(-1);

    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    if (value.trim().length >= 1) {
      debounceTimeoutRef.current = setTimeout(() => {
        performSearch(value);
      }, 150);
    } else {
      setSuggestions([]);
      setIsOpen(false);
    }
  };

  const selectStock = useCallback(
    async (stock: SearchResultItem) => {
      const newQuery = `${stock.name}(${stock.ticker}) 종합 분석 및 투자 심의해줘`;
      setInputValue(stock.name);
      setQuery(newQuery);
      setStock(stock.ticker, stock.name);
      setIsOpen(false);
      setSuggestions([]);

      // 1. Register to DB stock_watchlist (triggers stream_worker live polling on-demand)
      try {
        await fetch("/api/stock/watchlist", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ticker: stock.ticker, name: stock.name }),
        });
      } catch (e) {
        console.warn("Watchlist add error:", e);
      }

      // 2. Start full 4-stage multi-agent analysis
      startAnalysis(newQuery);
    },
    [setQuery, setStock, startAnalysis]
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlightIdx((i) => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlightIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (highlightIdx >= 0 && suggestions[highlightIdx]) {
        selectStock(suggestions[highlightIdx]);
      } else if (suggestions.length > 0) {
        selectStock(suggestions[0]);
      } else {
        handleSubmit(undefined, false);
      }
    } else if (e.key === "Escape") {
      setIsOpen(false);
    }
  };

  const handleSubmit = (e?: React.FormEvent, forceRefresh: boolean = false) => {
    if (e) e.preventDefault();
    const trimmed = inputValue.trim();
    if (!trimmed) return;
    setQuery(trimmed);
    startAnalysis(trimmed, forceRefresh);
    setIsOpen(false);
  };

  return (
    <div className="w-full flex flex-col gap-3" ref={containerRef}>
      {/* Search Input Bar */}
      <form onSubmit={(e) => handleSubmit(e, false)} className="relative w-full">
        <div className="relative flex items-center w-full rounded-2xl bg-slate-900/90 border border-slate-700/80 shadow-xl focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all">
          <div className="pl-4 text-slate-400">
            <Search className="w-5 h-5" />
          </div>

          <input
            type="text"
            value={inputValue}
            onChange={(e) => handleInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => {
              if (suggestions.length > 0) setIsOpen(true);
            }}
            placeholder="오케스트레이터 실시간 종목 검색 (예: 한화에어로스페이스, 카카오, 005930…)"
            className="w-full h-14 pl-3 pr-44 bg-transparent text-sm md:text-base text-slate-100 placeholder-slate-500 focus:outline-none"
            autoComplete="off"
          />

          {inputValue && (
            <button
              type="button"
              onClick={() => {
                setInputValue("");
                setSuggestions([]);
                setIsOpen(false);
              }}
              className="p-1 mr-2 text-slate-500 hover:text-slate-300 rounded-md transition"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          <div className="absolute right-2 flex items-center gap-1.5">
            {isCached && (
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
              disabled={!inputValue.trim()}
              className="gap-2 px-5 font-bold text-xs md:text-sm"
            >
              <Sparkles className="w-4 h-4" />
              {isAnalyzing && !inputValue.trim() ? "분석 중..." : "분석 시작"}
            </Button>
          </div>
        </div>

        {/* Autocomplete Dropdown backed by Orchestrator Stock Search */}
        {isOpen && suggestions.length > 0 && (
          <div className="absolute z-50 top-full mt-1 w-full rounded-xl bg-slate-900 border border-slate-700 shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between px-3 py-1.5 text-[10px] text-slate-500 border-b border-slate-800 font-medium">
              <span className="flex items-center gap-1 text-blue-400">
                <Database className="w-3 h-3" />
                오케스트레이터 DB 검색 결과 ({suggestions.length}건)
              </span>
              <span>선택 시 실시간 시세 수집 및 4단계 분석 시작</span>
            </div>
            <ul className="max-h-60 overflow-y-auto">
              {suggestions.map((stock, idx) => (
                <li key={stock.ticker}>
                  <button
                    type="button"
                    onMouseDown={(e) => {
                      e.preventDefault();
                      selectStock(stock);
                    }}
                    className={`w-full flex items-center justify-between px-4 py-2.5 text-sm hover:bg-slate-800 transition-colors ${
                      idx === highlightIdx ? "bg-slate-800" : ""
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-700 flex items-center justify-center font-bold text-xs text-white flex-shrink-0">
                        {stock.name.slice(0, 1)}
                      </div>
                      <div className="text-left">
                        <p className="font-semibold text-slate-100">{stock.name}</p>
                        {stock.sector && (
                          <p className="text-[11px] text-slate-500">{stock.sector}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-right">
                      <span className="text-xs font-mono text-slate-400">{stock.ticker}</span>
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                          stock.market === "KOSPI"
                            ? "bg-blue-900/50 text-blue-300"
                            : "bg-emerald-900/50 text-emerald-300"
                        }`}
                      >
                        {stock.market || "KOSPI"}
                      </span>
                      <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </form>

      {/* Cache Status Banner */}
      {isCached && (
        <div className="flex items-center justify-between px-3.5 py-2 rounded-xl bg-amber-950/40 border border-amber-800/50 text-amber-300 text-xs">
          <div className="flex items-center gap-2">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
            </span>
            <span className="font-semibold">⚡ Redis 고속 캐시 적용됨</span>
            <span className="text-amber-400/80 text-[11px] hidden sm:inline">
              (동일 종목 최근 분석 결과 캐시 로드{ttlRemaining ? ` • 잔여 TTL: ${ttlRemaining}초` : ""})
            </span>
          </div>
          <button
            type="button"
            onClick={() => handleSubmit(undefined, true)}
            className="font-bold underline text-amber-200 hover:text-white transition text-xs flex items-center gap-1"
          >
            실시간 갱신하기 →
          </button>
        </div>
      )}

      {/* Selected stock pill */}
      {ticker && (
        <div className="flex items-center gap-2 text-xs text-slate-500 pl-1">
          <span>현재 분석 종목:</span>
          <span className="px-2 py-0.5 rounded-full bg-blue-900/40 border border-blue-700/50 text-blue-300 font-semibold">
            {useAgentStore.getState().stockName} ({ticker})
          </span>
        </div>
      )}
    </div>
  );
};
