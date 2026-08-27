"use client";

import React from "react";
import { DataProcessingResult } from "@/types/agent";
import { formatKRW, formatPercent } from "@/lib/formatters";
import { cleanDisplayText } from "@/lib/utils";
import { Database, Newspaper, Sparkles, Tag } from "lucide-react";

interface DataProcessingCardProps {
  data?: DataProcessingResult | string;
}

export const DataProcessingCard: React.FC<DataProcessingCardProps> = ({ data }) => {
  if (!data) return null;

  const isStructured = typeof data === "object" && "technical_metrics" in data;
  const metrics = isStructured ? data.technical_metrics : null;
  const news = isStructured && data.news_analysis ? data.news_analysis : null;
  const rawText = typeof data === "string" ? data : (data.raw_output || "");
  const displayText = cleanDisplayText(rawText);

  return (
    <div className="flex flex-col justify-between p-5 rounded-2xl border border-slate-800/90 bg-slate-950/80 shadow-md backdrop-blur-md">
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Database className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-100">📊 실시간 시세 & 뉴스 정제</h4>
              <span className="text-[10px] text-slate-400 font-mono">data_processing_agent (28001)</span>
            </div>
          </div>

          {news && (
            <span className="px-3 py-0.5 rounded-full text-xs font-bold border bg-emerald-500/15 text-emerald-300 border-emerald-500/30">
              뉴스 센티먼트: {news.sentiment} ({(news.sentiment_score * 100).toFixed(0)}%)
            </span>
          )}
        </div>

        {/* Moving Averages Row (실제 구조화 데이터가 있을 때만 렌더링) */}
        {metrics && (
          <div className="grid grid-cols-3 gap-2 my-3 text-xs">
            <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-800/80 text-center">
              <span className="text-slate-400 text-[10px] block">20일 이평선</span>
              <span className="font-mono font-bold text-yellow-400">{formatKRW(metrics.sma_20)}</span>
            </div>
            <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-800/80 text-center">
              <span className="text-slate-400 text-[10px] block">60일 이평선</span>
              <span className="font-mono font-bold text-cyan-400">{formatKRW(metrics.sma_60)}</span>
            </div>
            <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-800/80 text-center">
              <span className="text-slate-400 text-[10px] block">RSI (14일)</span>
              <span className="font-mono font-bold text-indigo-400">{metrics.rsi_14.toFixed(1)}</span>
            </div>
          </div>
        )}

        {/* News Keywords */}
        {news && news.key_keywords && news.key_keywords.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 my-2">
            <span className="text-[11px] text-slate-400 flex items-center gap-1 mr-1">
              <Tag className="w-3 h-3 text-indigo-400" />
              핵심 키워드:
            </span>
            {news.key_keywords.map((kw, i) => (
              <span
                key={i}
                className="px-2 py-0.5 rounded-md bg-slate-900 text-slate-300 border border-slate-800 text-[11px]"
              >
                #{kw}
              </span>
            ))}
          </div>
        )}
      </div>

      {displayText && (
        <div className="text-xs text-slate-300 leading-relaxed mt-2 pt-2 border-t border-slate-800/60 whitespace-pre-line">
          {displayText}
        </div>
      )}
    </div>
  );
};
