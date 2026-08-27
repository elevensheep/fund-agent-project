"use client";

import React from "react";
import { FundamentalResult } from "@/types/agent";
import { formatKRW, formatPercent, getGradeBadgeStyle } from "@/lib/formatters";
import { cleanDisplayText } from "@/lib/utils";
import { Award, DollarSign, PieChart, Sparkles } from "lucide-react";

interface FundamentalCardProps {
  data?: FundamentalResult | string;
}

export const FundamentalCard: React.FC<FundamentalCardProps> = ({ data }) => {
  if (!data) return null;

  const isStructured = typeof data === "object" && "valuation_metrics" in data;
  const metrics = isStructured ? data.valuation_metrics : null;
  const rawText = typeof data === "string" ? data : (data.analysis_summary || data.raw_output || "");
  const displayText = cleanDisplayText(rawText);

  const gradeStyle = metrics ? getGradeBadgeStyle(metrics.grade) : null;

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

          {metrics && gradeStyle && (
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-slate-400">재무 등급</span>
              <span
                className={`px-3 py-0.5 rounded-full text-xs border ${gradeStyle.bg} ${gradeStyle.text} ${gradeStyle.border}`}
              >
                {metrics.grade} 등급
              </span>
            </div>
          )}
        </div>

        {/* 4-Core Multiples (PER, PBR, ROE, 부채비율) */}
        {metrics && (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 my-3 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80 text-center">
                <span className="text-slate-400 text-[11px] block mb-0.5">PER (주가수익)</span>
                <span className="text-sm font-black font-mono text-slate-100">{metrics.per.toFixed(1)}배</span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80 text-center">
                <span className="text-slate-400 text-[11px] block mb-0.5">PBR (주가순자산)</span>
                <span className="text-sm font-black font-mono text-slate-100">{metrics.pbr.toFixed(2)}배</span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80 text-center">
                <span className="text-slate-400 text-[11px] block mb-0.5">ROE (자기자본)</span>
                <span className="text-sm font-black font-mono text-emerald-400">
                  {formatPercent(metrics.roe)}
                </span>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80 text-center">
                <span className="text-slate-400 text-[11px] block mb-0.5">부채비율</span>
                <span className="text-sm font-black font-mono text-slate-200">
                  {metrics.debt_ratio !== undefined ? `${metrics.debt_ratio.toFixed(1)}%` : "건전"}
                </span>
              </div>
            </div>

            {/* Target Price Range Band */}
            {metrics.target_price_range && metrics.target_price_range[0] > 0 && (
              <div className="p-3 rounded-xl bg-gradient-to-r from-purple-950/30 to-blue-950/30 border border-purple-900/40 text-xs my-3">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-slate-300 font-medium flex items-center gap-1">
                    <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                    적정가치 목표 밴드
                    {metrics.upside_rate !== undefined && metrics.upside_rate > 0 && (
                      <span className="text-[10px] text-emerald-400 font-bold ml-1">
                        (+{metrics.upside_rate.toFixed(1)}%)
                      </span>
                    )}
                  </span>
                  <span className="font-mono font-bold text-purple-300">
                    {formatKRW(metrics.target_price_range[0])} ~ {formatKRW(metrics.target_price_range[1])}
                  </span>
                </div>
              </div>
            )}
          </>
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
