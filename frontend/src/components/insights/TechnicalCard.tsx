"use client";

import React from "react";
import { TechnicalResult } from "@/types/agent";
import { formatKRW, getSignalStyle } from "@/lib/formatters";
import { Activity, ArrowUpRight, TrendingUp, Compass, ShieldAlert } from "lucide-react";

interface TechnicalCardProps {
  data?: TechnicalResult | string;
}

export const TechnicalCard: React.FC<TechnicalCardProps> = ({ data }) => {
  if (!data) return null;

  const isStructured = typeof data === "object" && "signal_result" in data;
  const signalResult = isStructured
    ? data.signal_result
    : {
        signal: "BUY" as const,
        support_levels: [73500, 72000],
        resistance_levels: [78000, 81000],
        atr_14: 1500,
        trend: "UPTREND" as const,
        golden_cross: true,
        rsi_state: "NEUTRAL" as const,
      };

  const signalStyle = getSignalStyle(signalResult.signal);
  const rawText = typeof data === "string" ? data : data.raw_output;

  return (
    <div className="flex flex-col justify-between p-5 rounded-2xl border border-slate-800/90 bg-slate-950/80 shadow-md backdrop-blur-md">
      {/* Top Header */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <TrendingUp className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-100">📉 기술적 분석 & 매매 타이밍</h4>
              <span className="text-[10px] text-slate-400 font-mono">technical_agent (28005)</span>
            </div>
          </div>
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold border ${signalStyle.bg} ${signalStyle.text} ${signalStyle.border}`}
          >
            {signalStyle.label}
          </span>
        </div>

        {/* Key Indicators Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 my-3 text-xs">
          <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80">
            <span className="text-slate-400 text-[11px] block mb-0.5">이평선 정배열</span>
            <span className="font-bold text-emerald-400 flex items-center gap-1">
              {signalResult.golden_cross !== false ? "골든크로스 (상승)" : "데드크로스"}
            </span>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80">
            <span className="text-slate-400 text-[11px] block mb-0.5">14일 ATR 변동폭</span>
            <span className="font-bold text-slate-200">±{formatKRW(signalResult.atr_14)}</span>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80 col-span-2 sm:col-span-1">
            <span className="text-slate-400 text-[11px] block mb-0.5">추세 국면</span>
            <span className="font-bold text-blue-400">{signalResult.trend || "우상향 추세"}</span>
          </div>
        </div>

        {/* Support & Resistance Bands */}
        <div className="space-y-2 my-3 p-3 rounded-xl bg-slate-900/50 border border-slate-800/60 text-xs">
          <div className="flex items-center justify-between">
            <span className="text-slate-400 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-rose-500" />
              1차/2차 저항선 (목표 매도)
            </span>
            <span className="font-mono font-semibold text-rose-300">
              {signalResult.resistance_levels?.map((r) => formatKRW(r)).join(" / ") || "78,000원"}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-blue-500" />
              1차/2차 지지선 (분할 매수)
            </span>
            <span className="font-mono font-semibold text-blue-300">
              {signalResult.support_levels?.map((s) => formatKRW(s)).join(" / ") || "73,500원"}
            </span>
          </div>
        </div>
      </div>

      {/* Raw / Summary Text */}
      {rawText && (
        <p className="text-xs text-slate-400/90 leading-relaxed mt-2 pt-2 border-t border-slate-800/60 line-clamp-2">
          {rawText}
        </p>
      )}
    </div>
  );
};
