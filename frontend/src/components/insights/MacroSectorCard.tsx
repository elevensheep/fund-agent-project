"use client";

import React from "react";
import { MacroSectorResult } from "@/types/agent";
import { cleanDisplayText } from "@/lib/utils";
import { Globe, Gauge, Compass, Zap } from "lucide-react";

interface MacroSectorCardProps {
  data?: MacroSectorResult | string;
}

export const MacroSectorCard: React.FC<MacroSectorCardProps> = ({ data }) => {
  if (!data) return null;

  const isStructured = typeof data === "object" && "sector_data" in data;
  const sector = isStructured ? data.sector_data : null;
  const rawText = typeof data === "string" ? data : (data.raw_output || "");
  const displayText = cleanDisplayText(rawText);

  return (
    <div className="flex flex-col justify-between p-5 rounded-2xl border border-slate-800/90 bg-slate-950/80 shadow-md backdrop-blur-md">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-teal-500/10 text-teal-400 border border-teal-500/20">
              <Globe className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-100">🌐 거시경제 & 섹터 트렌드</h4>
              <span className="text-[10px] text-slate-400 font-mono">macro_sector_agent (28007)</span>
            </div>
          </div>

          {sector && sector.sector_momentum && (
            <span className="px-3 py-0.5 rounded-full text-xs font-bold border bg-teal-500/15 text-teal-300 border-teal-500/30">
              {sector.sector_momentum}
            </span>
          )}
        </div>

        {/* Metrics Grid (실제 데이터 있을 때만) */}
        {sector && (
          <>
            <div className="grid grid-cols-2 gap-2.5 my-3 text-xs">
              {sector.sector_name && (
                <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80">
                  <span className="text-slate-400 text-[11px] block mb-0.5">소속 업종 섹터</span>
                  <span className="font-bold text-slate-100 truncate block">{sector.sector_name}</span>
                </div>
              )}

              <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800/80">
                <span className="text-slate-400 text-[11px] block mb-0.5">섹터 상대강도 (RS)</span>
                <span className="font-bold text-teal-400">
                  {sector.sector_relative_strength ? `RS ${sector.sector_relative_strength.toFixed(2)}` : `상위 ${sector.relative_strength_rank || 1}위`}
                </span>
              </div>
            </div>

            {/* Macro Score Bar */}
            {sector.macro_score !== undefined && (
              <div className="p-3 rounded-xl bg-slate-900/50 border border-slate-800/60 text-xs my-2.5">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-slate-400 flex items-center gap-1">
                    <Gauge className="w-3.5 h-3.5 text-teal-400" />
                    거시경제 종합 점수
                  </span>
                  <span className="font-bold font-mono text-teal-300">{sector.macro_score} / 100점</span>
                </div>
                <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-teal-500 to-emerald-400 h-full rounded-full transition-all duration-500"
                    style={{ width: `${sector.macro_score}%` }}
                  />
                </div>
              </div>
            )}

            {/* FX & Interest Rate Impacts if present */}
            {(sector.fx_impact || sector.rate_impact) && (
              <div className="p-2.5 rounded-xl bg-teal-950/20 border border-teal-900/30 text-slate-300 text-[11px] space-y-1 my-2">
                {sector.fx_impact && (
                  <div className="flex items-start gap-1.5">
                    <span className="font-bold text-teal-400 flex-shrink-0">💱 환율/금리:</span>
                    <span>{sector.fx_impact}</span>
                  </div>
                )}
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
