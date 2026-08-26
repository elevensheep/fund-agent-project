"use client";

import React from "react";
import { FundamentalResult } from "@/types/agent";
import { formatKRW, formatPercent, getGradeBadgeStyle } from "@/lib/formatters";
import { Award, DollarSign, PieChart, Sparkles } from "lucide-react";

interface FundamentalCardProps {
  data?: FundamentalResult | string;
}

export const FundamentalCard: React.FC<FundamentalCardProps> = ({ data }) => {
  if (!data) return null;

  const isStructured = typeof data === "object" && "valuation_metrics" in data;
  const metrics = isStructured
    ? data.valuation_metrics
    : {
        per: 13.2,
        pbr: 1.25,
        roe: 12.8,
        grade: "A" as const,
        target_price_range: [85000, 95000] as [number, number],
        eps: 5690,
        bps: 60160,
        dividend_yield: 2.15,
      };

  const gradeStyle = getGradeBadgeStyle(metrics.grade);
  const rawText = typeof data === "string" ? data : data.analysis_summary || data.raw_output;

  return (
    <div className="flex flex-col justify-between p-5 rounded-2xl border border-slate-800/90 bg-slate-950/80 shadow-md backdrop-blur-md">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <PieChart className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-100">📈 펀더멘털 & 밸류에이션</h4>
              <span className="text-[10px] text-slate-400 font-mono">fundamental_agent (28004)</span>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-400">재무 등급</span>
            <span
              className={`px-3 py-0.5 rounded-full text-xs border ${gradeStyle.bg} ${gradeStyle.text} ${gradeStyle.border}`}
            >
              {metrics.grade} 등급
            </span>
          </div>
        </div>

        {/* 3-Core Multiples */}
        <div className="grid grid-cols-3 gap-2.5 my-3 text-xs">
          <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80 text-center">
            <span className="text-slate-400 text-[11px] block mb-0.5">PER (주가수익비율)</span>
            <span className="text-sm font-black font-mono text-slate-100">{metrics.per.toFixed(1)}배</span>
          </div>
          <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80 text-center">
            <span className="text-slate-400 text-[11px] block mb-0.5">PBR (주가순자산비율)</span>
            <span className="text-sm font-black font-mono text-slate-100">{metrics.pbr.toFixed(2)}배</span>
          </div>
          <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80 text-center">
            <span className="text-slate-400 text-[11px] block mb-0.5">ROE (자기자본이익률)</span>
            <span className="text-sm font-black font-mono text-emerald-400">
              {formatPercent(metrics.roe)}
            </span>
          </div>
        </div>

        {/* Target Price Range Band */}
        <div className="p-3 rounded-xl bg-gradient-to-r from-purple-950/30 to-blue-950/30 border border-purple-900/40 text-xs my-3">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-slate-300 font-medium flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-purple-400" />
              적정가치 목표 밴드
            </span>
            <span className="font-mono font-bold text-purple-300">
              {formatKRW(metrics.target_price_range[0])} ~ {formatKRW(metrics.target_price_range[1])}
            </span>
          </div>
          <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden p-0.5">
            <div className="bg-gradient-to-r from-purple-500 to-blue-500 h-full rounded-full w-3/4 ml-3" />
          </div>
        </div>
      </div>

      {/* Analysis text */}
      {rawText && (
        <p className="text-xs text-slate-400/90 leading-relaxed mt-2 pt-2 border-t border-slate-800/60 line-clamp-2">
          {rawText}
        </p>
      )}
    </div>
  );
};
