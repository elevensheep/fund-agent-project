"use client";

import React from "react";
import { BullBearDebateResult } from "@/types/agent";
import { getSignalStyle } from "@/lib/formatters";
import { cleanDisplayText } from "@/lib/utils";
import { Flame, Gavel, Scale, Swords, ThumbsDown, ThumbsUp } from "lucide-react";

interface BullBearDebateCardProps {
  data?: BullBearDebateResult | string;
}

export const BullBearDebateCard: React.FC<BullBearDebateCardProps> = ({ data }) => {
  if (!data) return null;

  const isStructured = typeof data === "object" && "judge_verdict" in data;
  const verdict = isStructured ? data.judge_verdict : null;
  const rawText = typeof data === "string" ? data : (data.raw_output || "");
  const displayText = cleanDisplayText(rawText);

  const signalStyle = verdict?.decision ? getSignalStyle(verdict.decision) : null;

  return (
    <div className="flex flex-col justify-between p-5 rounded-2xl border border-slate-800/90 bg-slate-950/80 shadow-md backdrop-blur-md">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-orange-500/10 text-orange-400 border border-orange-500/20">
              <Swords className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-100">🐂🐻 Bull vs Bear 대립 토론 & 판사</h4>
              <span className="text-[10px] text-slate-400 font-mono">bull_bear_debate_agent (28008)</span>
            </div>
          </div>

          {verdict && signalStyle && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">확신도: {verdict.confidence_score}%</span>
              <span
                className={`px-3 py-1 rounded-full text-xs font-bold border ${signalStyle.bg} ${signalStyle.text} ${signalStyle.border}`}
              >
                판사: {verdict.decision}
              </span>
            </div>
          )}
        </div>

        {/* Bull vs Bear 2-Column Duel (실제 데이터 있을 때만) */}
        {verdict && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 my-3 text-xs">
              {verdict.bull_summary && (
                <div className="p-3 rounded-xl bg-red-950/20 border border-red-900/40">
                  <div className="flex items-center gap-1.5 text-red-400 font-bold mb-1.5">
                    <ThumbsUp className="w-3.5 h-3.5" />
                    <span>🐂 상승론자 (Bull 논거)</span>
                  </div>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    {verdict.bull_summary}
                  </p>
                </div>
              )}

              {verdict.bear_summary && (
                <div className="p-3 rounded-xl bg-blue-950/20 border border-blue-900/40">
                  <div className="flex items-center gap-1.5 text-blue-400 font-bold mb-1.5">
                    <ThumbsDown className="w-3.5 h-3.5" />
                    <span>🐻 하락론자 (Bear 논거)</span>
                  </div>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    {verdict.bear_summary}
                  </p>
                </div>
              )}
            </div>

            {/* Judge Verdict Summary */}
            <div className="p-3 rounded-xl bg-slate-900/70 border border-slate-800/80 text-xs my-2.5 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-slate-300 font-medium">
                  <Gavel className="w-4 h-4 text-amber-400 flex-shrink-0" />
                  <strong className="text-amber-300">판사 최종 평결:</strong> {verdict.decision}
                </span>
                <span className="text-slate-400 font-mono text-[11px]">확신도 {verdict.confidence_score}%</span>
              </div>
              {(verdict.target_price || verdict.stop_loss_price) && (
                <div className="flex items-center gap-3 pt-1 border-t border-slate-800/60 text-[11px] font-mono">
                  {verdict.target_price && (
                    <span className="text-purple-300">
                      🎯 권고 목표가: <strong>{verdict.target_price.toLocaleString("ko-KR")}원</strong>
                    </span>
                  )}
                  {verdict.stop_loss_price && (
                    <span className="text-rose-400">
                      🛑 권고 손절가: <strong>{verdict.stop_loss_price.toLocaleString("ko-KR")}원</strong>
                    </span>
                  )}
                </div>
              )}
            </div>
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
