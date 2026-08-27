import { useCallback, useRef } from "react";
import { useAgentStore } from "@/stores/useAgentStore";
import { invokeSupervisor } from "@/lib/api";
import { extractTicker } from "@/lib/utils";

export function useAgentStream() {
  const {
    setIsAnalyzing,
    setCurrentStepId,
    addCompletedAgent,
    setStock,
    loadResponse,
    resetAnalysis,
    setFinalReport,
  } = useAgentStore();

  const abortControllerRef = useRef<AbortController | null>(null);
  const timersRef = useRef<NodeJS.Timeout[]>([]);
  const reqIdRef = useRef<number>(0);

  const startAnalysis = useCallback(
    async (queryText: string, forceRefresh: boolean = false) => {
      // 1. Cancel any previous in-flight analysis & timers
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      timersRef.current.forEach(clearTimeout);
      timersRef.current = [];

      const abortController = new AbortController();
      abortControllerRef.current = abortController;
      const currentReqId = ++reqIdRef.current;

      let { ticker, name } = extractTicker(queryText);

      // 로컬 마스터에서 못 찾은 경우 백엔드 오케스트레이터 검색 API로 2차 탐색
      if (!ticker) {
        try {
          const searchRes = await fetch(
            `/api/stock/search?query=${encodeURIComponent(queryText.trim())}&limit=1`,
            { signal: abortController.signal }
          );
          if (searchRes.ok) {
            const results = await searchRes.json();
            if (Array.isArray(results) && results.length > 0) {
              ticker = results[0].ticker;
              name = results[0].name;
            }
          }
        } catch (e: any) {
          if (e?.name === "AbortError" || abortController.signal.aborted) return;
          console.debug("Backend fallback stock resolution error:", e);
        }
      }

      if (currentReqId !== reqIdRef.current || abortController.signal.aborted) {
        return;
      }

      // 종목을 전혀 찾을 수 없는 경우 (없는 회사/문자열)
      if (!ticker) {
        setIsAnalyzing(false);
        resetAnalysis();
        setFinalReport(
          `## 🔍 종목을 찾을 수 없습니다\n\n입력하신 **"${queryText}"**에 해당하는 국내 상장 종목이 존재하지 않거나 식별되지 않았습니다.\n\n### 💡 추천 검색 방법:\n- **정확한 종목명**: 예) \`카카오\`, \`현대차\`, \`한화에어로스페이스\`, \`SK하이닉스\`, \`두산에너빌리티\`\n- **6자리 종목코드**: 예) \`005930\`, \`000660\`, \`035720\`\n- **상단 AI 테마 버튼**: \`🔥 AI 반도체 Top Picks\`, \`💎 저PBR 밸류업 추천\` 버튼 클릭`
        );
        return;
      }

      // 종목이 정상 식별된 경우
      setStock(ticker, name);
      resetAnalysis();
      setIsAnalyzing(true);

      // On-demand Watchlist 등록 (stream_worker 백그라운드 수집 트리거)
      try {
        fetch("/api/stock/watchlist", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ticker, name }),
        }).catch(() => {});
      } catch {}

      // Progressive DAG animation while backend is computing
      const t1 = setTimeout(() => {
        if (currentReqId === reqIdRef.current) {
          setCurrentStepId(1);
          addCompletedAgent("data_processing_agent");
          addCompletedAgent("web_search_agent");
        }
      }, 1200);

      const t2 = setTimeout(() => {
        if (currentReqId === reqIdRef.current) {
          setCurrentStepId(2);
          addCompletedAgent("fundamental_agent");
          addCompletedAgent("technical_agent");
          addCompletedAgent("dart_disclosure_agent");
          addCompletedAgent("macro_sector_agent");
        }
      }, 3500);

      const t3 = setTimeout(() => {
        if (currentReqId === reqIdRef.current) {
          setCurrentStepId(3);
          addCompletedAgent("bull_bear_debate_agent");
        }
      }, 6000);

      const t4 = setTimeout(() => {
        if (currentReqId === reqIdRef.current) {
          setCurrentStepId(4);
          addCompletedAgent("risk_management_agent");
        }
      }, 8000);

      timersRef.current = [t1, t2, t3, t4];

      try {
        const response = await invokeSupervisor(
          queryText,
          undefined,
          false,
          forceRefresh,
          abortController.signal
        );

        if (currentReqId !== reqIdRef.current || abortController.signal.aborted) {
          return;
        }

        timersRef.current.forEach(clearTimeout);
        timersRef.current = [];

        loadResponse(response, name);
      } catch (err: any) {
        if (err?.name === "AbortError" || abortController.signal.aborted) {
          return;
        }
        if (currentReqId !== reqIdRef.current) {
          return;
        }

        console.error("Live analysis request failed:", err);
        timersRef.current.forEach(clearTimeout);
        timersRef.current = [];
        setIsAnalyzing(false);
        setFinalReport(
          `## ⚠️ 분석 요청 실패\n오케스트레이터 서버와의 통신 중 오류가 발생했습니다: ${err instanceof Error ? err.message : String(err)}\n\n잠시 후 다시 시도해 주세요.`
        );
      }
    },
    [
      setStock,
      resetAnalysis,
      setCurrentStepId,
      addCompletedAgent,
      loadResponse,
      setIsAnalyzing,
      setFinalReport,
    ]
  );

  return {
    startAnalysis,
  };
}
