"use client";

import React from "react";
import { WebSearchResult } from "@/types/agent";
import { cleanDisplayText } from "@/lib/utils";
import { ExternalLink, Globe2, Search } from "lucide-react";

interface WebSearchCardProps {
  data?: WebSearchResult | string;
}

export const WebSearchCard: React.FC<WebSearchCardProps> = ({ data }) => {
  if (!data) return null;

  const isStructured = typeof data === "object" && "sources" in data;
  const search = isStructured ? data : null;
  const rawText = typeof data === "string" ? data : (data.summary || data.raw_output || "");
  const displayText = cleanDisplayText(rawText);

  return (
    <div className="flex flex-col justify-between p-5 rounded-2xl border border-slate-800/90 bg-slate-950/80 shadow-md backdrop-blur-md">
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20">
              <Search className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-100">🔍 실시간 웹 검색 & 이슈 브리핑</h4>
              <span className="text-[10px] text-slate-400 font-mono">web_search_agent (28003)</span>
            </div>
          </div>

          <span className="px-2.5 py-0.5 rounded-md bg-sky-950/80 text-sky-300 border border-sky-800/60 text-xs font-mono">
            ReAct Engine
          </span>
        </div>

        {displayText && (
          <div className="text-xs text-slate-200 leading-relaxed my-2 bg-slate-900/60 p-3 rounded-xl border border-slate-800/60 whitespace-pre-line">
            {displayText}
          </div>
        )}

        {/* Source Citations (실제 소스가 있을 때만 렌더링) */}
        {search && search.sources && search.sources.length > 0 && (
          <div className="space-y-1.5 mt-2">
            {search.sources.slice(0, 3).map((s, idx) => (
              <a
                key={idx}
                href={s.url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-between p-2 rounded-lg bg-slate-900/40 hover:bg-slate-900 text-slate-300 text-xs border border-slate-800/40 transition-colors group"
              >
                <span className="truncate max-w-[280px] group-hover:text-blue-400">{s.title}</span>
                <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-blue-400 flex-shrink-0" />
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
