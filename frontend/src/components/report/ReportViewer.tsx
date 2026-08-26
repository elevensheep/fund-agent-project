"use client";

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, Check, Download, FileText, Share2, Sparkles, BookOpen } from "lucide-react";
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
    link.download = `${stockName}_${ticker}_투자분석리포트.md`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (!reportMarkdown && isAnalyzing) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-slate-950/80 border border-slate-800/80 rounded-2xl text-center backdrop-blur-md">
        <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4" />
        <h4 className="text-base font-bold text-slate-200">
          Synthesizer 에이전트가 8대 서브 에이전트 결과를 종합 분석 중입니다...
        </h4>
        <p className="text-xs text-slate-400 mt-1 max-w-md">
          재무 밸류에이션, 차트 지표, 전자공시, 거시경제, Bull/Bear 토론 및 100% Rule-Based 리스크 심의를 취합하여 제도권 리서치 보고서를 생성합니다.
        </p>
      </div>
    );
  }

  if (!reportMarkdown) {
    return (
      <div className="flex flex-col items-center justify-center p-12 bg-slate-950/80 border border-slate-800/80 rounded-2xl text-center backdrop-blur-md">
        <BookOpen className="w-8 h-8 text-slate-600 mb-2" />
        <p className="text-sm text-slate-400">생성된 종합 투자 분석 리포트가 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col w-full rounded-2xl border border-slate-800/90 bg-slate-950/90 shadow-xl overflow-hidden backdrop-blur-md">
      {/* Top Action Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-4 border-b border-slate-800/80 bg-slate-900/70">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-500/20">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              제도권 종합 투자 분석 보고서
              <span className="text-xs font-mono font-normal text-slate-400">
                ({stockName} • {ticker})
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">
              Lead Synthesizer Agent • 다중 서브 에이전트 결론 통합 보고서
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleCopy} className="gap-1.5 text-xs">
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? "복사 완료" : "리포트 복사"}
          </Button>

          <Button variant="secondary" size="sm" onClick={handleDownload} className="gap-1.5 text-xs">
            <Download className="w-3.5 h-3.5 text-blue-400" />
            다운로드 (.md)
          </Button>
        </div>
      </div>

      {/* Markdown Content Body */}
      <div className="p-6 md:p-8 overflow-y-auto max-h-[750px] prose prose-invert max-w-none text-slate-200">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h1: ({ node, ...props }) => (
              <h1 className="text-xl md:text-2xl font-black text-slate-100 pb-3 mb-4 border-b border-slate-800" {...props} />
            ),
            h2: ({ node, ...props }) => (
              <h2 className="text-lg md:text-xl font-bold text-blue-300 mt-6 mb-3 flex items-center gap-2" {...props} />
            ),
            h3: ({ node, ...props }) => (
              <h3 className="text-base font-semibold text-slate-200 mt-4 mb-2" {...props} />
            ),
            p: ({ node, ...props }) => (
              <p className="text-sm text-slate-300 leading-relaxed my-2" {...props} />
            ),
            ul: ({ node, ...props }) => (
              <ul className="list-disc list-inside space-y-1.5 my-2 text-sm text-slate-300 pl-2" {...props} />
            ),
            ol: ({ node, ...props }) => (
              <ol className="list-decimal list-inside space-y-1.5 my-2 text-sm text-slate-300 pl-2" {...props} />
            ),
            li: ({ node, ...props }) => <li className="text-sm leading-relaxed" {...props} />,
            strong: ({ node, ...props }) => <strong className="font-bold text-slate-100" {...props} />,
            table: ({ node, ...props }) => (
              <div className="overflow-x-auto my-4 rounded-xl border border-slate-800">
                <table className="w-full text-xs text-left border-collapse" {...props} />
              </div>
            ),
            thead: ({ node, ...props }) => <thead className="bg-slate-900/90 text-slate-300 border-b border-slate-800" {...props} />,
            th: ({ node, ...props }) => <th className="p-2.5 font-bold" {...props} />,
            td: ({ node, ...props }) => <td className="p-2.5 border-b border-slate-900 text-slate-300" {...props} />,
            blockquote: ({ node, ...props }) => (
              <blockquote className="p-3 my-3 border-l-4 border-blue-500 bg-blue-950/20 rounded-r-xl text-slate-300 text-xs italic" {...props} />
            ),
            hr: ({ node, ...props }) => <hr className="my-6 border-slate-800" {...props} />,
          }}
        >
          {reportMarkdown}
        </ReactMarkdown>
      </div>
    </div>
  );
};
