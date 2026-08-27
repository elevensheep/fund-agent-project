"use client";

import React from "react";
import { RiskManagementResult } from "@/types/agent";
import { formatKRW, getRiskVerdictStyle } from "@/lib/formatters";
import { cleanDisplayText } from "@/lib/utils";
import { AlertTriangle, Lock, ShieldAlert, ShieldCheck, Percent, DollarSign } from "lucide-react";

interface RiskGatekeeperCardProps {
  data?: RiskManagementResult | string;
}

export const RiskGatekeeperCard: React.FC<RiskGatekeeperCardProps> = ({ data }) => {
  if (!data) return null;

  const isStructured = typeof data === "object" && "verdict" in data;
  const risk = isStructured ? data : null;
  const rawText = typeof data === "string" ? data : (data.raw_output || "");
  const displayText = cleanDisplayText(rawText);

  const isApproved = risk ? risk.verdict === "APPROVED" : true;
  const verdictStyle = risk ? getRiskVerdictStyle(risk.verdict) : null;

  return (
    <div
      className={`flex flex-col justify-between p-5 rounded-2xl border shadow-md backdrop-blur-md transition-all ${
        isApproved
          ? "bg-emerald-950/20 border-emerald-900/50"
          : "bg-rose-950/20 border-rose-900/50"
      }`}
    >
      {/* Header */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <div
              className={`p-1.5 rounded-lg border ${
                isApproved
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                  : "bg-rose-500/10 text-rose-400 border-rose-500/20"
              }`}
            >
              {isApproved ? <ShieldCheck className="w-4 h-4" /> : <ShieldAlert className="w-4 h-4" />}
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-100">🛡️ 100% Rule-Based 리스크 심의</h4>
              <span className="text-[10px] text-slate-400 font-mono">risk_management_agent (28009)</span>
            </div>
          </div>

          {risk && verdictStyle && (
            <span className={`px-3 py-1 rounded-full text-xs font-bold border ${verdictStyle.badge}`}>
              {risk.verdict}
            </span>
          )}
        </div>

        {/* 2-Key Decision Tiles (실제 구조화 데이터가 있을 때만 렌더링) */}
        {risk && (
          <>
            <div className="grid grid-cols-2 gap-3 my-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80">
                <span className="text-slate-400 text-[11px] block mb-1">승인 투자 비중 (Max 15%)</span>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-lg font-black font-mono text-emerald-400">
                    {(risk.approved_weight * 100).toFixed(1)}%
                  </span>
                  <span className="text-[11px] text-slate-500">/ 15.0%</span>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80">
                <span className="text-slate-400 text-[11px] block mb-1">동적 손절선 (ATR 1.5x)</span>
                <span className="text-lg font-black font-mono text-rose-400">
                  {formatKRW(risk.stop_loss_price)}
                </span>
              </div>
            </div>

            {/* Panic Market Trigger Alert */}
            {risk.panic_market_flag ? (
              <div className="flex items-center gap-2 p-2.5 rounded-xl bg-rose-950/80 border border-rose-800 text-rose-300 text-xs my-2.5 animate-pulse">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>⚠️ 코스피 -3.0% 이상 급락장 감지: 신규 매수 전면 차단 발동!</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 p-2 rounded-lg bg-slate-900/40 border border-slate-800/60 text-slate-400 text-[11px] my-2">
                <Lock className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                <span>{risk.reason || "포트폴리오 단일종목 15% 한도 및 리스크 가이드 준수"}</span>
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
