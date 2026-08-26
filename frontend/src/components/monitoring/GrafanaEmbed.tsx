"use client";

import React, { useState } from "react";
import { Activity, BarChart2, ExternalLink, HardDrive, RefreshCw, Server, Shield, Zap } from "lucide-react";
import { Button } from "@/components/ui/Button";

export const GrafanaEmbed: React.FC = () => {
  const [iframeKey, setIframeKey] = useState(0);
  const grafanaUrl = process.env.NEXT_PUBLIC_GRAFANA_URL || "http://localhost:23000";
  const dashboardUrl = `${grafanaUrl}/d/agent-ecosystem-main/financial-multi-agent-ecosystem-dashboard?kiosk=tv&theme=dark`;

  return (
    <div className="flex flex-col w-full rounded-2xl border border-slate-800/90 bg-slate-950/90 shadow-xl overflow-hidden backdrop-blur-md">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-4 border-b border-slate-800/80 bg-slate-900/70">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-amber-600 to-orange-600 text-white shadow-md shadow-orange-500/20">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              시스템 Observability & Grafana 대시보드
            </h3>
            <p className="text-[11px] text-slate-400">
              FastAPI Prometheus 메트릭 • Loki 구조화 로그 • 컨테이너 상태 실시간 모니터링
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIframeKey((prev) => prev + 1)}
            className="gap-1.5 text-xs"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            새로고침
          </Button>

          <a href={grafanaUrl} target="_blank" rel="noreferrer">
            <Button variant="secondary" size="sm" className="gap-1.5 text-xs">
              <ExternalLink className="w-3.5 h-3.5 text-blue-400" />
              Grafana 새 창 열기
            </Button>
          </a>
        </div>
      </div>

      {/* KPI Tiles */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-5 border-b border-slate-800/60 bg-slate-900/30 text-xs">
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80">
          <span className="text-slate-400 text-[11px] flex items-center gap-1 mb-1">
            <Server className="w-3.5 h-3.5 text-blue-400" />
            활성 서브 에이전트
          </span>
          <span className="text-lg font-black font-mono text-blue-400">8 / 8 Active</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80">
          <span className="text-slate-400 text-[11px] flex items-center gap-1 mb-1">
            <Zap className="w-3.5 h-3.5 text-emerald-400" />
            A2A JSON-RPC 상태
          </span>
          <span className="text-lg font-black font-mono text-emerald-400">100% 정상</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80">
          <span className="text-slate-400 text-[11px] flex items-center gap-1 mb-1">
            <Shield className="w-3.5 h-3.5 text-purple-400" />
            MCP SSE Discovery
          </span>
          <span className="text-lg font-black font-mono text-purple-400">Port 28002 Connected</span>
        </div>

        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800/80">
          <span className="text-slate-400 text-[11px] flex items-center gap-1 mb-1">
            <HardDrive className="w-3.5 h-3.5 text-cyan-400" />
            PostgreSQL 시계열 DB
          </span>
          <span className="text-lg font-black font-mono text-cyan-400">Port 5432 Ready</span>
        </div>
      </div>

      {/* Embedded Grafana iframe */}
      <div className="w-full h-[650px] relative bg-slate-950">
        <iframe
          key={iframeKey}
          src={dashboardUrl}
          className="w-full h-full border-0"
          title="Grafana Dashboard"
          loading="lazy"
        />
      </div>
    </div>
  );
};
