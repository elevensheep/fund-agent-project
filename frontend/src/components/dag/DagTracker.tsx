"use client";

import React from "react";
import { CheckCircle2, CircleDashed, Loader2, PlayCircle, ShieldCheck, Zap, ArrowRight } from "lucide-react";
import { ExecutionPlan } from "@/types/agent";

interface DagTrackerProps {
  plan: ExecutionPlan | null;
  currentStep: number;
  completedAgents: string[];
  isAnalyzing?: boolean;
  onSelectAgent?: (agentName: string) => void;
}

const AGENT_LABELS: Record<string, { label: string; icon: string; role: string }> = {
  data_processing_agent: { label: "시세/뉴스 수집", icon: "📊", role: "Hybrid Collection & DB" },
  web_search_agent: { label: "웹 실시간 검색", icon: "🔍", role: "DuckDuckGo ReAct" },
  fundamental_agent: { label: "펀더멘털 분석", icon: "📈", role: "재무3표 & 밸류에이션" },
  technical_agent: { label: "기술적 지표", icon: "📉", role: "차트 패턴 & 매매신호" },
  dart_disclosure_agent: { label: "DART 공시", icon: "📑", role: "오버행 & 전자공시" },
  macro_sector_agent: { label: "매크로 & 섹터", icon: "🌐", role: "거시경제 & RS 랭킹" },
  bull_bear_debate_agent: { label: "상승 vs 하락 토론", icon: "🐂🐻", role: "다자간 토론 & 판사 판정" },
  risk_management_agent: { label: "리스크 게이트키퍼", icon: "🛡️", role: "100% Rule-Based 심의" },
};

export const DagTracker: React.FC<DagTrackerProps> = ({
  plan,
  currentStep,
  completedAgents,
  isAnalyzing = false,
  onSelectAgent,
}) => {
  if (!plan || !plan.steps.length) {
    return (
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 my-4 backdrop-blur-md text-center">
        <p className="text-xs text-slate-500">대기 중인 실행 계획이 없습니다. 종목을 검색하여 분석을 시작하세요.</p>
      </div>
    );
  }

  // Group steps by step_id
  const groupedSteps = plan.steps.reduce((acc, step) => {
    if (!acc[step.step_id]) acc[step.step_id] = [];
    acc[step.step_id].push(step);
    return acc;
  }, {} as Record<number, typeof plan.steps>);

  const stepTitles: Record<number, { title: string; subtitle: string }> = {
    1: { title: "1단계: 데이터 수집 & 정제", subtitle: "시세 틱 & 웹 뉴스 병렬 수집" },
    2: { title: "2단계: 4대 심층 병렬 분석", subtitle: "재무, 차트, 공시, 매크로 동시 진단" },
    3: { title: "3단계: Bull vs Bear 격돌", subtitle: "상승론 vs 하락론 대립 토론" },
    4: { title: "4단계: 리스크 심의 & 승인", subtitle: "100% Rule-Based 비중/손절선" },
  };

  const totalSteps = Object.keys(groupedSteps).length;
  const progressPercent = Math.min(100, Math.round((currentStep / totalSteps) * 100));

  return (
    <div className="bg-slate-950/80 border border-slate-800/90 rounded-2xl p-5 my-4 shadow-xl backdrop-blur-md">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-800/60">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Zap className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              Plan-and-Execute DAG 파이프라인
              <span className="text-xs font-mono font-normal text-slate-400">[{plan.ticker}]</span>
            </h3>
            <p className="text-[11px] text-slate-400">
              비동기 병렬 오케스트레이션 • 8대 금융 전문 서브 에이전트 조율
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-1 rounded-md bg-blue-950/80 text-blue-300 border border-blue-800/60 font-semibold font-mono">
            {plan.query_intent}
          </span>
          {isAnalyzing ? (
            <span className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md bg-amber-950/80 text-amber-300 border border-amber-800/60 animate-pulse">
              <Loader2 className="w-3 h-3 animate-spin" />
              {currentStep}단계 실행 중...
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md bg-emerald-950/80 text-emerald-300 border border-emerald-800/60 font-semibold">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              파이프라인 완료
            </span>
          )}
        </div>
      </div>

      {/* Grid of Steps */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {Object.entries(groupedSteps).map(([stepIdStr, steps]) => {
          const stepId = Number(stepIdStr);
          const isCurrent = currentStep === stepId && isAnalyzing;
          const isDone = currentStep > stepId || (!isAnalyzing && currentStep >= stepId);
          const isPending = currentStep < stepId;

          const meta = stepTitles[stepId] || {
            title: `${stepId}단계`,
            subtitle: "서브 에이전트 실행",
          };

          return (
            <div
              key={stepId}
              className={`relative flex flex-col justify-between p-3.5 rounded-xl border transition-all duration-300 ${
                isCurrent
                  ? "bg-gradient-to-b from-blue-950/60 to-slate-900/90 border-blue-500 shadow-lg shadow-blue-500/10 ring-1 ring-blue-500/50"
                  : isDone
                  ? "bg-slate-900/60 border-slate-800 hover:border-slate-700 text-slate-300"
                  : "bg-slate-950/40 border-slate-900/80 text-slate-600 opacity-60"
              }`}
            >
              {/* Step Header */}
              <div>
                <div className="flex items-center justify-between gap-1.5 mb-2">
                  <div className="flex items-center gap-2">
                    {isCurrent ? (
                      <Loader2 className="w-4 h-4 text-blue-400 animate-spin flex-shrink-0" />
                    ) : isDone ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                    ) : (
                      <CircleDashed className="w-4 h-4 text-slate-600 flex-shrink-0" />
                    )}
                    <span className="text-xs font-bold text-slate-100">{meta.title}</span>
                  </div>
                  <span
                    className={`text-[10px] font-mono px-1.5 py-0.2 rounded ${
                      isCurrent
                        ? "bg-blue-500/20 text-blue-300"
                        : isDone
                        ? "bg-emerald-500/10 text-emerald-400"
                        : "bg-slate-800 text-slate-500"
                    }`}
                  >
                    STEP {stepId}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mb-3 line-clamp-1">{meta.subtitle}</p>
              </div>

              {/* Sub-agents inside this step */}
              <div className="space-y-1.5 mt-auto pt-2 border-t border-slate-800/60">
                {steps.map((s) => {
                  const agentDone = completedAgents.includes(s.agent_name);
                  const agentMeta = AGENT_LABELS[s.agent_name] || {
                    label: s.agent_name,
                    icon: "⚡",
                    role: "Sub Agent",
                  };

                  return (
                    <button
                      key={s.agent_name}
                      type="button"
                      onClick={() => onSelectAgent && onSelectAgent(s.agent_name)}
                      className={`w-full flex items-center justify-between p-2 rounded-lg text-left transition-all ${
                        agentDone
                          ? "bg-slate-800/40 hover:bg-slate-800 text-slate-200 border border-slate-700/40"
                          : isCurrent
                          ? "bg-blue-950/40 text-blue-200 border border-blue-800/40"
                          : "bg-slate-950 text-slate-600 border border-slate-900"
                      }`}
                    >
                      <div className="flex items-center gap-1.5 truncate">
                        <span className="text-xs">{agentMeta.icon}</span>
                        <span className="text-[11px] font-medium truncate">{agentMeta.label}</span>
                      </div>
                      <div className="flex items-center gap-1 text-[10px] font-mono flex-shrink-0">
                        {agentDone ? (
                          <span className="text-emerald-400 font-semibold flex items-center gap-0.5">
                            ✓ 완료
                          </span>
                        ) : isCurrent ? (
                          <span className="text-blue-400 animate-pulse">호출중...</span>
                        ) : (
                          <span className="text-slate-600">대기</span>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
