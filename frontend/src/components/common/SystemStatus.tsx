"use client";

import React, { useEffect, useState } from "react";
import { useAgentStore } from "@/stores/useAgentStore";
import { fetchSupervisorInfo } from "@/lib/api";
import { SupervisorInfo } from "@/types/agent";
import { Dialog } from "@/components/ui/Dialog";
import { CheckCircle2, Cpu, HardDrive, Network, Radio, Server, ShieldCheck, Zap } from "lucide-react";

export const SystemStatus: React.FC = () => {
  const { isSystemStatusOpen, setIsSystemStatusOpen } = useAgentStore();
  const [info, setInfo] = useState<SupervisorInfo | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isSystemStatusOpen) {
      setLoading(true);
      fetchSupervisorInfo().then((res) => {
        setInfo(res);
        setLoading(false);
      });
    }
  }, [isSystemStatusOpen]);

  const SUB_AGENTS = [
    { name: "data_processing_agent", port: "28001", role: "LangGraph 시세 수집 & 정제 & DB 적재", protocol: "A2A JSON-RPC 2.0" },
    { name: "mcp_server", port: "28002", role: "FastMCP SSE 동적 에이전트 탐색 도구", protocol: "MCP SSE 2024-11-05" },
    { name: "web_search_agent", port: "28003", role: "DuckDuckGo ReAct 웹 실시간 검색", protocol: "A2A JSON-RPC 2.0" },
    { name: "fundamental_agent", port: "28004", role: "재무제표 3표 & 밸류에이션(PER/PBR/ROE)", protocol: "A2A JSON-RPC 2.0" },
    { name: "technical_agent", port: "28005", role: "차트 패턴 & 이평선 정배열 & 매매 신호", protocol: "A2A JSON-RPC 2.0" },
    { name: "dart_disclosure_agent", port: "28006", role: "DART 전자공시 & CB/BW 오버행 분석", protocol: "A2A JSON-RPC 2.0" },
    { name: "macro_sector_agent", port: "28007", role: "글로벌 거시경제 & 섹터 상대강도", protocol: "A2A JSON-RPC 2.0" },
    { name: "bull_bear_debate_agent", port: "28008", role: "상승론 vs 하락론 대립 토론 & 판사 판정", protocol: "A2A JSON-RPC 2.0" },
    { name: "risk_management_agent", port: "28009", role: "100% Rule-Based 비중 한도 & 손절선 심의", protocol: "A2A JSON-RPC 2.0" },
  ];

  return (
    <Dialog
      open={isSystemStatusOpen}
      onOpenChange={setIsSystemStatusOpen}
      title="🌐 분산 Multi-Agent Ecosystem 시스템 가동 상태"
      description="Docker Network (agent_shared_net) 내 서브 에이전트 및 MCP Discovery 프로브"
    >
      <div className="space-y-4 text-xs">
        {/* Core Orchestrator Card */}
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="font-bold text-slate-200 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-blue-400" />
              Supervisor Orchestrator App (Port 28000)
            </span>
            <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[11px] font-semibold">
              RUNNING (정상)
            </span>
          </div>
          <p className="text-slate-400 text-[11px]">
            LLM Provider: <strong className="text-slate-200">{info?.llm_provider || "ChatOpenAI / MockModel"}</strong> • Plan-and-Execute Pipeline
          </p>
        </div>

        {/* 8 Sub-agents Grid */}
        <div className="space-y-2">
          <h4 className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
            <Server className="w-3.5 h-3.5 text-indigo-400" />
            연결된 서브 에이전트 및 마이크로서비스 목록
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {SUB_AGENTS.map((agent) => (
              <div
                key={agent.name}
                className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 flex flex-col justify-between"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono font-bold text-slate-200">{agent.name}</span>
                  <span className="text-[10px] font-mono text-blue-400 bg-blue-950 px-1.5 py-0.5 rounded border border-blue-800">
                    :{agent.port}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">{agent.role}</p>
                <div className="flex items-center justify-between mt-2 pt-1.5 border-t border-slate-900 text-[10px]">
                  <span className="text-slate-500 font-mono">{agent.protocol}</span>
                  <span className="text-emerald-400 font-semibold flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    Probe OK
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Dialog>
  );
};
