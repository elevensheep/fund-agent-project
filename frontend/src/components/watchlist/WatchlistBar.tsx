"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useAgentStore } from "@/stores/useAgentStore";
import { useAgentStream } from "@/hooks/useAgentStream";
import { formatKRW, formatPercent } from "@/lib/formatters";
import { Activity, Plus, Radio, Trash2, X } from "lucide-react";

interface WatchlistItem {
  ticker: string;
  name: string;
  market: string;
  price: number;
  changePercent: number;
  volume: number;
}

export const WatchlistBar: React.FC = () => {
  const { ticker: currentTicker, setStock, setActiveTab } = useAgentStore();
  const { startAnalysis } = useAgentStream();
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchWatchlist = useCallback(async () => {
    try {
      const res = await fetch("/api/stock/watchlist", { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        if (data && data.watchlist) {
          setItems(data.watchlist);
        }
      }
    } catch (e) {
      // ignore
    }
  }, []);

  useEffect(() => {
    fetchWatchlist();
    const interval = setInterval(fetchWatchlist, 4000);
    return () => clearInterval(interval);
  }, [fetchWatchlist]);

  const handleSelect = (item: WatchlistItem) => {
    setStock(item.ticker, item.name);
    setActiveTab("dashboard");
    startAnalysis(`${item.name}(${item.ticker}) 종합 분석해줘`);
  };

  const handleRemove = async (e: React.MouseEvent, ticker: string) => {
    e.stopPropagation();
    try {
      await fetch(`/api/stock/watchlist?ticker=${ticker}`, { method: "DELETE" });
      setItems((prev) => prev.filter((i) => i.ticker !== ticker));
    } catch (err) {
      console.error("Failed to remove watchlist item:", err);
    }
  };

  if (items.length === 0) return null;

  return (
    <div className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md overflow-x-auto scrollbar-none text-xs">
      <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-blue-950/40 border border-blue-800/50 text-blue-300 font-bold flex-shrink-0">
        <Radio className="w-3 h-3 text-blue-400 animate-pulse" />
        <span className="text-[11px]">실시간 스트림 워치리스트</span>
      </div>

      <div className="flex items-center gap-2">
        {items.map((item) => {
          const isSelected = item.ticker === currentTicker;
          const isUp = item.changePercent >= 0;

          return (
            <div
              key={item.ticker}
              onClick={() => handleSelect(item)}
              role="button"
              tabIndex={0}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-all cursor-pointer flex-shrink-0 ${
                isSelected
                  ? "bg-blue-600/20 border-blue-500/60 text-white shadow-sm"
                  : "bg-slate-950/80 hover:bg-slate-900 border-slate-800 text-slate-300"
              }`}
            >
              <div className="text-left">
                <div className="flex items-center gap-1">
                  <span className="font-semibold text-slate-100">{item.name}</span>
                  <span className="text-[10px] font-mono text-slate-500">{item.ticker}</span>
                </div>
                {item.price > 0 && (
                  <div className="flex items-center gap-1 font-mono text-[10px]">
                    <span className="text-slate-300">{formatKRW(item.price)}</span>
                    <span className={isUp ? "text-rose-400 font-bold" : "text-blue-400 font-bold"}>
                      {isUp ? "▲" : "▼"} {formatPercent(item.changePercent, { includeSign: true })}
                    </span>
                  </div>
                )}
              </div>

              {items.length > 1 && (
                <button
                  type="button"
                  onClick={(e) => handleRemove(e, item.ticker)}
                  title="워치리스트에서 삭제"
                  className="p-1 text-slate-500 hover:text-rose-400 rounded transition"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
