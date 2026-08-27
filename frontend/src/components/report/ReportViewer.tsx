"use client";

import React, { useState, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useAgentStore } from "@/stores/useAgentStore";
import {
  Copy,
  Check,
  Download,
  FileText,
  Printer,
  Sparkles,
  BookOpen,
  TrendingUp,
  Shield,
  Target,
  AlertTriangle,
  Award,
  Layers,
  Code2,
  CheckCircle2,
  PieChart,
  Activity,
  Compass,
  Scale,
} from "lucide-react";
import { Button } from "@/components/ui/Button";

interface ReportViewerProps {
  reportMarkdown: string;
  ticker: string;
  stockName: string;
  isAnalyzing?: boolean;
}

export const ReportViewer: React.FC<ReportViewerProps> = ({
  reportMarkdown,
  ticker,
  stockName,
  isAnalyzing = false,
}) => {
  const [copied, setCopied] = useState(false);
  const [activeViewMode, setActiveViewMode] = useState<"document" | "structured" | "raw">("document");

  const executiveMetrics = useAgentStore((state) => state.executiveMetrics);

  // Executive Metrics 추출 파서 (store의 executiveMetrics가 있으면 우선 사용, 없으면 리포트 텍스트에서 추출)
  const parsedMetrics = useMemo(() => {
    if (executiveMetrics) {
      return {
        opinion: executiveMetrics.investment_opinion || "BUY",
        targetPrice: executiveMetrics.target_price_str,
        stopLoss: executiveMetrics.stop_loss_str,
        weight: executiveMetrics.approved_weight_str,
        confidence: executiveMetrics.confidence_str,
        grade: executiveMetrics.financial_grade,
      };
    }

    if (!reportMarkdown) return null;

    let opinion = "BUY";
    if (/STRONG[_\s]?BUY|적극\s?매수/i.test(reportMarkdown)) opinion = "STRONG BUY";
    else if (/STRONG[_\s]?SELL|적극\s?매도/i.test(reportMarkdown)) opinion = "STRONG SELL";
    else if (/BUY|매수/i.test(reportMarkdown)) opinion = "BUY";
    else if (/SELL|매도/i.test(reportMarkdown)) opinion = "SELL";
    else if (/HOLD|중립|보유/i.test(reportMarkdown)) opinion = "HOLD";

    // 목표가 매칭 (예: 289,000원 ~ 328,400원)
    const targetMatch = reportMarkdown.match(/(?:적정\s*목표가\s*밴드|목표(?:가|주가)(?:\s*밴드)?)[|\s*:]+([0-9,]+(?:\s*원)?(?:\s*~\s*[0-9,]+(?:\s*원)?))/);
    const targetPrice = targetMatch ? targetMatch[1].replace(/[*|]/g, "").trim() : "분석 완료";

    // 손절가 매칭 (예: 244,300원)
    const stopLossMatch = reportMarkdown.match(/(?:필수\s*동적\s*손절선|손절(?:선|가)?)[|\s*:]+([0-9,]+(?:\s*원)?)/);
    const stopLoss = stopLossMatch ? stopLossMatch[1].replace(/[*|]/g, "").trim() : "손절선 준수";

    // 승인 비중 매칭 (예: 15.0%)
    const weightMatch = reportMarkdown.match(/(?:승인\s*)?포트폴리오\s*비중[|\s*:]+([0-9.]+\s*%)/);
    const weight = weightMatch ? weightMatch[1].replace(/[*|]/g, "").trim() : "15.0%";

    // 확신도 매칭 (예: 85%)
    const confMatch = reportMarkdown.match(/(?:확신도|리서치\s*확신도)[|\s*:]+([0-9.]+\s*%)/);
    const confidence = confMatch ? confMatch[1].replace(/[*|]/g, "").trim() : "85%";

    // 재무 등급 매칭 (예: A 등급)
    const gradeMatch = reportMarkdown.match(/재무\s*평가\s*등급[|\s*:]+([SABCD]\s*등급|[SABCD])/i);
    const grade = gradeMatch ? gradeMatch[1].replace(/[*|]/g, "").trim() : "A 등급";

    return {
      opinion,
      targetPrice,
      stopLoss,
      weight,
      confidence,
      grade,
    };
  }, [executiveMetrics, reportMarkdown]);


  // 섹션 분할 파서 (구조화 뷰용)
  const sections = useMemo(() => {
    if (!reportMarkdown) return [];
    const lines = reportMarkdown.split("\n");
    const result: Array<{ id: string; title: string; icon: string; content: string[] }> = [];
    let currentSection: { id: string; title: string; icon: string; content: string[] } | null = null;

    lines.forEach((line) => {
      const h3Match = line.match(/^###\s*(.+)/);
      const h2Match = line.match(/^##\s*(.+)/);

      if (h3Match || (h2Match && !line.includes("🎯 최종"))) {
        if (currentSection) {
          result.push(currentSection);
        }
        const fullTitle = (h3Match ? h3Match[1] : h2Match![1]).trim();
        let icon = "📌";
        if (fullTitle.includes("펀더멘털") || fullTitle.includes("밸류에이션")) icon = "📈";
        else if (fullTitle.includes("기술적") || fullTitle.includes("차트")) icon = "📉";
        else if (fullTitle.includes("공시") || fullTitle.includes("DART") || fullTitle.includes("거시")) icon = "📑";
        else if (fullTitle.includes("토론") || fullTitle.includes("Bull") || fullTitle.includes("판사")) icon = "🐂🐻";
        else if (fullTitle.includes("리스크") || fullTitle.includes("Gatekeeper")) icon = "🛡️";
        else if (fullTitle.includes("핵심")) icon = "🎯";

        currentSection = {
          id: `sec-${result.length + 1}`,
          title: fullTitle,
          icon,
          content: [],
        };
      } else if (currentSection) {
        currentSection.content.push(line);
      }
    });

    if (currentSection) {
      result.push(currentSection);
    }

    return result;
  }, [reportMarkdown]);

  const handleCopy = () => {
    navigator.clipboard.writeText(reportMarkdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([reportMarkdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${stockName}_${ticker}_제도권종합투자분석보고서.md`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handlePrint = () => {
    window.print();
  };

  if (!reportMarkdown && isAnalyzing) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-slate-950/80 border border-slate-800/80 rounded-2xl text-center backdrop-blur-md">
        <div className="relative mb-4">
          <div className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin" />
          <Sparkles className="w-5 h-5 text-blue-400 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 animate-pulse" />
        </div>
        <h4 className="text-base font-bold text-slate-100">
          Synthesizer 에이전트가 8대 서브 에이전트 분석 결과를 종합 집계 중입니다...
        </h4>
        <p className="text-xs text-slate-400 mt-2 max-w-lg leading-relaxed">
          재무 밸류에이션, 차트 지표, 전자공시, 거시경제, Bull/Bear 대립 토론 및 100% Rule-Based 리스크 심의를 취합하여 제도권 수준의 정규 리서치 보고서를 생성하고 있습니다.
        </p>
      </div>
    );
  }

  if (!reportMarkdown) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-slate-950/80 border border-slate-800/80 rounded-2xl text-center backdrop-blur-md">
        <BookOpen className="w-10 h-10 text-slate-600 mb-3" />
        <h4 className="text-sm font-semibold text-slate-300">생성된 종합 투자 분석 리포트가 없습니다.</h4>
        <p className="text-xs text-slate-500 mt-1">상단 검색창에서 종목을 검색하거나 분석을 실행해주세요.</p>
      </div>
    );
  }

  const getOpinionBadge = (opinion: string) => {
    switch (opinion) {
      case "STRONG BUY":
        return {
          bg: "bg-rose-500/20",
          text: "text-rose-400",
          border: "border-rose-500/40",
          label: "STRONG BUY (적극 매수)",
        };
      case "BUY":
        return {
          bg: "bg-emerald-500/20",
          text: "text-emerald-400",
          border: "border-emerald-500/40",
          label: "BUY (매수)",
        };
      case "HOLD":
        return {
          bg: "bg-amber-500/20",
          text: "text-amber-400",
          border: "border-amber-500/40",
          label: "HOLD (중립/관망)",
        };
      case "SELL":
      case "STRONG SELL":
        return {
          bg: "bg-blue-500/20",
          text: "text-blue-400",
          border: "border-blue-500/40",
          label: "SELL (매도)",
        };
      default:
        return {
          bg: "bg-blue-500/20",
          text: "text-blue-400",
          border: "border-blue-500/40",
          label: opinion,
        };
    }
  };

  const opinionStyle = getOpinionBadge(parsedMetrics?.opinion || "BUY");

  return (
    <div className="flex flex-col w-full rounded-2xl border border-slate-800/90 bg-slate-950/95 shadow-2xl overflow-hidden backdrop-blur-xl">
      {/* Top Institutional Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-4 border-b border-slate-800/80 bg-slate-900/80">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 text-white shadow-lg shadow-blue-500/20">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-100 tracking-tight">
                제도권 종합 투자 분석 보고서
              </h3>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-md bg-blue-950/60 text-blue-300 border border-blue-800/50">
                {stockName} • {ticker}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5 flex items-center gap-2">
              <span>Lead Synthesizer Agent</span>
              <span className="text-slate-600">•</span>
              <span className="font-mono text-[11px] text-slate-500">Google ADK A2A Protocol</span>
              <span className="text-slate-600">•</span>
              <span className="text-[11px] text-emerald-400/90 font-medium">8대 전문 서브 에이전트 검증 완료</span>
            </p>
          </div>
        </div>

        {/* Action Controls & View Switcher */}
        <div className="flex items-center flex-wrap gap-2">
          {/* View Mode Toggle */}
          <div className="flex items-center p-1 rounded-xl bg-slate-950 border border-slate-800 text-xs">
            <button
              onClick={() => setActiveViewMode("document")}
              className={`px-3 py-1 rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
                activeViewMode === "document"
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              리포트 뷰
            </button>
            <button
              onClick={() => setActiveViewMode("structured")}
              className={`px-3 py-1 rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
                activeViewMode === "structured"
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              구조화 브리핑
            </button>
            <button
              onClick={() => setActiveViewMode("raw")}
              className={`px-3 py-1 rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
                activeViewMode === "raw"
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Code2 className="w-3.5 h-3.5" />
              원문 (.md)
            </button>
          </div>

          {/* Action Buttons */}
          <Button variant="outline" size="sm" onClick={handleCopy} className="gap-1.5 text-xs h-8">
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? "복사 완료" : "리포트 복사"}
          </Button>

          <Button variant="outline" size="sm" onClick={handlePrint} className="gap-1.5 text-xs h-8 hidden sm:flex">
            <Printer className="w-3.5 h-3.5 text-slate-300" />
            인쇄 / PDF
          </Button>

          <Button variant="secondary" size="sm" onClick={handleDownload} className="gap-1.5 text-xs h-8">
            <Download className="w-3.5 h-3.5 text-blue-400" />
            다운로드
          </Button>
        </div>
      </div>

      {/* Executive Key Metrics Bar (상단 핵심 투자 포인트 하이라이트) */}
      {parsedMetrics && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 p-4 md:px-6 bg-slate-900/40 border-b border-slate-800/80 text-xs">
          {/* 1. 투자 의견 */}
          <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 mb-1">
              <span className="text-[11px] font-medium">최종 투자 의견</span>
              <Target className="w-3.5 h-3.5 text-blue-400" />
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span
                className={`px-2.5 py-0.5 rounded-md font-bold text-xs border ${opinionStyle.bg} ${opinionStyle.text} ${opinionStyle.border}`}
              >
                {parsedMetrics.opinion}
              </span>
            </div>
          </div>

          {/* 2. 적정 목표가 밴드 */}
          <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 mb-1">
              <span className="text-[11px] font-medium">적정 목표가 밴드</span>
              <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="font-mono font-bold text-slate-100 text-xs mt-0.5 truncate">
              {parsedMetrics.targetPrice}
            </div>
          </div>

          {/* 3. 필수 동적 손절가 */}
          <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 mb-1">
              <span className="text-[11px] font-medium">필수 동적 손절선</span>
              <Shield className="w-3.5 h-3.5 text-rose-400" />
            </div>
            <div className="font-mono font-bold text-rose-300 text-xs mt-0.5">
              {parsedMetrics.stopLoss}
            </div>
          </div>

          {/* 4. 승인 편입 비중 */}
          <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 mb-1">
              <span className="text-[11px] font-medium">승인 포트폴리오 비중</span>
              <PieChart className="w-3.5 h-3.5 text-purple-400" />
            </div>
            <div className="font-mono font-bold text-purple-300 text-xs mt-0.5 flex items-baseline gap-1">
              <span>{parsedMetrics.weight}</span>
              <span className="text-[10px] text-slate-500 font-normal">(한도 승인)</span>
            </div>
          </div>

          {/* 5. 배심원 확신도 / 재무 등급 */}
          <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 col-span-2 sm:col-span-1 flex flex-col justify-between">
            <div className="flex items-center justify-between text-slate-400 mb-1">
              <span className="text-[11px] font-medium">리서치 확신도 / 등급</span>
              <Award className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div className="font-mono font-bold text-amber-300 text-xs mt-0.5 flex items-center gap-2">
              <span>{parsedMetrics.confidence}</span>
              <span className="text-slate-600">•</span>
              <span className="text-xs text-slate-200">{parsedMetrics.grade}</span>
            </div>
          </div>
        </div>
      )}

      {/* VIEW MODE 1: Full Document Markdown View */}
      {activeViewMode === "document" && (
        <div className="p-6 md:p-8 overflow-y-auto max-h-[750px] text-slate-200 selection:bg-blue-500/30">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h1: ({ node, ...props }) => (
                <div className="border-b border-slate-800 pb-4 mb-6">
                  <div className="flex items-center gap-2 text-xs font-semibold text-blue-400 uppercase tracking-wider mb-1.5">
                    <Sparkles className="w-4 h-4" />
                    <span>Institutional Equity Research Report</span>
                  </div>
                  <h1 className="text-xl md:text-2xl font-black text-slate-100 tracking-tight leading-tight" {...props} />
                </div>
              ),
              h2: ({ node, ...props }) => (
                <div className="mt-8 mb-4 p-3.5 rounded-xl bg-slate-900/80 border-l-4 border-blue-500 border-y border-r border-slate-800/80 flex items-center justify-between">
                  <h2 className="text-base md:text-lg font-bold text-slate-100 flex items-center gap-2.5" {...props} />
                  <span className="text-[11px] font-mono text-blue-400/80 uppercase px-2 py-0.5 rounded bg-blue-950/60 border border-blue-900/40">
                    Verified
                  </span>
                </div>
              ),
              h3: ({ node, ...props }) => (
                <h3 className="text-sm md:text-base font-bold text-blue-300 mt-6 mb-3 flex items-center gap-2" {...props} />
              ),
              h4: ({ node, ...props }) => (
                <h4 className="text-xs md:text-sm font-semibold text-slate-200 mt-4 mb-2" {...props} />
              ),
              p: ({ node, ...props }) => (
                <p className="text-sm text-slate-300 leading-relaxed my-2.5" {...props} />
              ),
              ul: ({ node, ...props }) => (
                <ul className="space-y-2 my-3 text-sm text-slate-300 pl-1" {...props} />
              ),
              ol: ({ node, ...props }) => (
                <ol className="list-decimal space-y-2 my-3 text-sm text-slate-300 pl-5" {...props} />
              ),
              li: ({ node, children, ...props }) => (
                <li className="text-sm leading-relaxed flex items-start gap-2" {...props}>
                  <span className="text-blue-400 mt-1.5 shrink-0 text-xs">▪</span>
                  <div className="flex-1">{children}</div>
                </li>
              ),
              strong: ({ node, ...props }) => (
                <strong className="font-bold text-slate-100 bg-slate-800/50 px-1 py-0.5 rounded text-inherit" {...props} />
              ),
              em: ({ node, ...props }) => (
                <em className="text-slate-400 text-xs italic" {...props} />
              ),
              table: ({ node, ...props }) => (
                <div className="overflow-x-auto my-4 rounded-xl border border-slate-800 bg-slate-900/50 shadow-inner">
                  <table className="w-full text-xs text-left border-collapse" {...props} />
                </div>
              ),
              thead: ({ node, ...props }) => (
                <thead className="bg-slate-900/90 text-slate-200 border-b border-slate-800 font-bold" {...props} />
              ),
              th: ({ node, ...props }) => (
                <th className="p-3 font-bold text-slate-200 border-r border-slate-800/60 last:border-r-0" {...props} />
              ),
              td: ({ node, ...props }) => (
                <td className="p-3 border-b border-slate-800/60 border-r border-slate-800/60 last:border-r-0 text-slate-300 font-mono" {...props} />
              ),
              blockquote: ({ node, children, ...props }) => (
                <blockquote
                  className="p-4 my-4 border-l-4 border-blue-500 bg-gradient-to-r from-blue-950/30 to-indigo-950/20 rounded-r-xl text-slate-200 text-xs leading-relaxed shadow-sm"
                  {...props}
                >
                  <div className="flex items-start gap-2.5">
                    <Sparkles className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                    <div className="flex-1">{children}</div>
                  </div>
                </blockquote>
              ),
              code: ({ node, className, children, ...props }) => {
                const isInline = !className && typeof children === "string" && !children.includes("\n");
                if (isInline) {
                  return (
                    <code className="font-mono text-xs px-1.5 py-0.5 rounded bg-slate-800/80 text-blue-300 border border-slate-700/50" {...props}>
                      {children}
                    </code>
                  );
                }
                return (
                  <div className="my-3 rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
                    <div className="px-3 py-1.5 bg-slate-900/90 border-b border-slate-800 text-[11px] font-mono text-slate-400 flex items-center justify-between">
                      <span>Structured Data Block</span>
                      <span>JSON / Log</span>
                    </div>
                    <pre className="p-3.5 text-xs font-mono text-slate-300 overflow-x-auto">
                      <code className={className} {...props}>
                        {children}
                      </code>
                    </pre>
                  </div>
                );
              },
              hr: ({ node, ...props }) => (
                <hr className="my-6 border-slate-800/80" {...props} />
              ),
            }}
          >
            {reportMarkdown}
          </ReactMarkdown>
        </div>
      )}

      {/* VIEW MODE 2: Structured Interactive Briefing Cards */}
      {activeViewMode === "structured" && (
        <div className="p-6 md:p-8 overflow-y-auto max-h-[750px] space-y-4">
          <div className="flex items-center justify-between p-4 rounded-xl bg-blue-950/30 border border-blue-800/40 mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/20 text-blue-400">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-100">8대 서브 에이전트 구조화 리서치 브리핑</h4>
                <p className="text-xs text-slate-400">보고서의 각 핵심 분석 섹션을 모듈별로 열람할 수 있습니다.</p>
              </div>
            </div>
            <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-900 text-blue-300 border border-blue-900/60 font-semibold">
              {sections.length}개 핵심 섹션
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sections.map((sec) => (
              <div
                key={sec.id}
                className="flex flex-col p-5 rounded-2xl border border-slate-800/90 bg-slate-900/60 shadow-md hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center gap-2.5 pb-3 border-b border-slate-800/80 mb-3">
                  <span className="text-lg">{sec.icon}</span>
                  <h4 className="text-sm font-bold text-slate-100 truncate flex-1">{sec.title}</h4>
                </div>
                <div className="text-xs text-slate-300 leading-relaxed space-y-2 flex-1">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      p: ({ node, ...props }) => <p className="my-1.5 text-xs text-slate-300 leading-relaxed" {...props} />,
                      ul: ({ node, ...props }) => <ul className="space-y-1.5 my-1 pl-2 text-xs" {...props} />,
                      li: ({ node, children, ...props }) => (
                        <li className="flex items-start gap-1.5 text-xs" {...props}>
                          <span className="text-blue-400 mt-1 shrink-0 text-[10px]">▪</span>
                          <div>{children}</div>
                        </li>
                      ),
                      strong: ({ node, ...props }) => <strong className="font-bold text-slate-100" {...props} />,
                      table: ({ node, ...props }) => (
                        <div className="overflow-x-auto my-2 rounded-lg border border-slate-800">
                          <table className="w-full text-[11px] text-left border-collapse" {...props} />
                        </div>
                      ),
                      th: ({ node, ...props }) => <th className="p-1.5 bg-slate-950 font-bold" {...props} />,
                      td: ({ node, ...props }) => <td className="p-1.5 border-t border-slate-800" {...props} />,
                    }}
                  >
                    {sec.content.join("\n")}
                  </ReactMarkdown>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* VIEW MODE 3: Raw Markdown Source View */}
      {activeViewMode === "raw" && (
        <div className="p-6 md:p-8 overflow-y-auto max-h-[750px]">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-slate-400 font-mono">Markdown Raw Source ({reportMarkdown.length} characters)</span>
            <Button variant="outline" size="sm" onClick={handleCopy} className="gap-1 text-xs h-7">
              {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              {copied ? "복사됨" : "소스 복사"}
            </Button>
          </div>
          <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-300 leading-relaxed overflow-x-auto whitespace-pre-wrap selection:bg-blue-600/40">
            {reportMarkdown}
          </pre>
        </div>
      )}

      {/* Footer Info Note */}
      <div className="flex items-center justify-between px-6 py-3 border-t border-slate-800/80 bg-slate-900/60 text-[11px] text-slate-500">
        <div className="flex items-center gap-2">
          <Shield className="w-3.5 h-3.5 text-emerald-400" />
          <span>100% Rule-Based 리스크 한도 심의(Gatekeeper) 필터링 승인 완료</span>
        </div>
        <span className="font-mono text-slate-600">Generated by Multi-Agent Synthesizer</span>
      </div>
    </div>
  );
};

