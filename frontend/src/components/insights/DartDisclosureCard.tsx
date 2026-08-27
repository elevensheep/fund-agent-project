"use client";

import React from "react";
import { DartDisclosureResult } from "@/types/agent";
import { cleanDisplayText } from "@/lib/utils";
import { AlertCircle, AlertTriangle, CheckCircle, FileText, ShieldAlert } from "lucide-react";

interface DartDisclosureCardProps {
  data?: DartDisclosureResult | string;
}

export const DartDisclosureCard: React.FC<DartDisclosureCardProps> = ({ data }) => {
  if (!data) return null;

  const isStructured = typeof data === "object" && "disclosure_analysis" in data;
  const analysis = isStructured ? data.disclosure_analysis : null;
  const rawText = typeof data === "string" ? data : (data.raw_output || "");
  const displayText = cleanDisplayText(rawText);

  const isLowRisk = analysis?.dilution_risk === "LOW";

  return (
    <div className="flex flex-col justify-between p-5 rounded-2xl border border-slate-800/90 bg-slate-950/80 shadow-md backdrop-blur-md">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-amber-500/10 text-amber-400 border border-blue-500/20">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-100">📑 DART 전자공시 & 오버행</h4>
              <span className="text-[10px] text-slate-400 font-mono">dart_disclosure_agent (28006)</span>
            </div>
          </div>

          {analysis && (
            <span
              className={`px-3 py-0.5 rounded-full text-xs font-bold border ${
                isLowRisk
                  ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                  : "bg-rose-500/15 text-rose-300 border-rose-500/30"
              }`}
            >
              희석 리스크: {analysis.dilution_risk}
            </span>
          )}
        </div>

        {/* Structured Analysis View (실제 데이터 있을 때만) */}
        {analysis && (
          <>
            {analysis.overhang_warning ? (
              <div className="flex items-center gap-2 p-2.5 rounded-xl bg-rose-950/40 border border-rose-800/50 text-rose-300 text-xs my-2.5">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>⚠️ {analysis.cb_bw_status || "잠재 전환사채(CB/BW) 물량 출회 및 주가 희석 주의"}</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 p-2.5 rounded-xl bg-emerald-950/30 border border-emerald-800/40 text-emerald-300 text-xs my-2.5">
                <CheckCircle className="w-4 h-4 flex-shrink-0" />
                <span>{analysis.cb_bw_status || "✅ 오버행(CB/BW) 리스크 없음 • 주주환원 양호"}</span>
              </div>
            )}

            {analysis.latest_filings && analysis.latest_filings.length > 0 && (
              <div className="space-y-1.5 my-2.5 text-xs">
                <span className="text-[11px] font-bold text-slate-400 block mb-1">최근 주요 공시 내역 ({analysis.latest_filings.length}건):</span>
                {analysis.latest_filings.map((f, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800/60"
                  >
                    <div className="flex items-center gap-1.5 truncate max-w-[240px]">
                      <span className="px-1.5 py-0.2 rounded bg-slate-800 text-[10px] text-amber-300 font-mono flex-shrink-0">
                        {f.category || "공시"}
                      </span>
                      <span className="text-slate-300 truncate text-[11px]">{f.title}</span>
                    </div>
                    <span className="text-[10px] font-mono text-slate-500 flex-shrink-0">{f.date}</span>
                  </div>
                ))}
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
