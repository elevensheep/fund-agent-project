"use client";

import React, { useEffect, useState } from "react";
import { useAgentStore } from "@/stores/useAgentStore";
import { fetchSupervisorInfo } from "@/lib/api";
import {
  Activity,
  BarChart3,
  Bot,
  Compass,
  Cpu,
  Layers,
  Network,
  Radio,
  Server,
  Shield,
  Sparkles,
  FileText as FileTextIcon,
} from "lucide-react";

import { Switch } from "@/components/ui/Switch";
import { Button } from "@/components/ui/Button";

export const Header: React.FC = () => {
  const {
    activeTab,
    setActiveTab,
    setIsSystemStatusOpen,
  } = useAgentStore();


  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    fetchSupervisorInfo().then((info) => {
      setBackendOnline(!!info);
    });
  }, []);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand / Logo */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20 ring-1 ring-white/20">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-black tracking-tight text-white flex items-center gap-1.5">
                Financial Multi-Agent
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                  Ecosystem
                </span>
              </h1>
              <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-500/10 text-blue-400 border border-blue-500/30">
                v1.0 A2A
              </span>
            </div>
            <p className="text-[10px] text-slate-400 flex items-center gap-1.5">
              <span>8 Sub-Agents • Plan-and-Execute DAG</span>
              <span className="w-1 h-1 rounded-full bg-slate-600" />
              <span>MCP FastMCP SSE</span>
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center rounded-xl bg-slate-900/90 p-1 border border-slate-800/80">
          <button
            type="button"
            onClick={() => setActiveTab("dashboard")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === "dashboard"
                ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/50"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            종합 대시보드
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("dag")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === "dag"
                ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/50"
            }`}
          >
            <Radio className="w-3.5 h-3.5" />
            DAG 파이프라인
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("recommendation")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === "recommendation"
                ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/50"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            AI 종목 추천
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("report")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === "report"
                ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/50"
            }`}
          >
            <FileTextIcon className="w-3.5 h-3.5" />
            최종 리포트
          </button>


          <button
            type="button"
            onClick={() => setActiveTab("monitoring")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === "monitoring"
                ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/50"
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            Observability
          </button>
        </nav>

        {/* Right Tools: Mode Switch & Status */}
        <div className="flex items-center gap-3">
          {/* Status Badge */}
          <button
            type="button"
            onClick={() => setIsSystemStatusOpen(true)}
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-850 border border-slate-800 transition text-xs"
          >
            <span
              className={`w-2 h-2 rounded-full ${
                backendOnline === false
                  ? "bg-rose-400"
                  : "bg-emerald-400 animate-pulse shadow-sm shadow-emerald-400/50"
              }`}
            />
            <span className="hidden sm:inline text-[11px] font-medium text-slate-300">
              {backendOnline === false ? "서버 오프라인" : "8 에이전트 가동중"}
            </span>
          </button>
        </div>
      </div>
    </header>
  );
};

