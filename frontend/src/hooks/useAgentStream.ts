import { useCallback } from "react";
import { useAgentStore } from "@/stores/useAgentStore";
import { invokeSupervisor } from "@/lib/api";
import { extractTicker } from "@/lib/utils";
import { MOCK_RESPONSES } from "@/lib/mockData";

export function useAgentStream() {
  const {
    isMockMode,
    setIsAnalyzing,
    setCurrentStepId,
    addCompletedAgent,
    setPlan,
    updateStepResult,
    setFinalReport,
    appendStreamingToken,
    setStock,
    loadResponse,
    resetAnalysis,
  } = useAgentStore();

  const runMockSimulation = useCallback(
    async (ticker: string, stockName: string, query: string) => {
      const mock = MOCK_RESPONSES[ticker] || MOCK_RESPONSES["005930"];
      resetAnalysis();
      setStock(ticker, stockName);

      // Step 1: Data Collection & Web Search
      setCurrentStepId(1);
      setPlan({
        ticker,
        query_intent: "FULL_ANALYSIS",
        steps: mock.plan?.steps || [],
      });
      await new Promise((r) => setTimeout(r, 600));
      addCompletedAgent("data_processing_agent");
      if (mock.step_results?.data_processing_agent) {
        updateStepResult("data_processing_agent", mock.step_results.data_processing_agent);
      }
      await new Promise((r) => setTimeout(r, 400));
      addCompletedAgent("web_search_agent");
      if (mock.step_results?.web_search_agent) {
        updateStepResult("web_search_agent", mock.step_results.web_search_agent);
      }

      // Step 2: 4-Domain Parallel Deep Analysis
      setCurrentStepId(2);
      await new Promise((r) => setTimeout(r, 800));
      addCompletedAgent("fundamental_agent");
      if (mock.step_results?.fundamental_agent) {
        updateStepResult("fundamental_agent", mock.step_results.fundamental_agent);
      }
      addCompletedAgent("technical_agent");
      if (mock.step_results?.technical_agent) {
        updateStepResult("technical_agent", mock.step_results.technical_agent);
      }
      addCompletedAgent("dart_disclosure_agent");
      if (mock.step_results?.dart_disclosure_agent) {
        updateStepResult("dart_disclosure_agent", mock.step_results.dart_disclosure_agent);
      }
      addCompletedAgent("macro_sector_agent");
      if (mock.step_results?.macro_sector_agent) {
        updateStepResult("macro_sector_agent", mock.step_results.macro_sector_agent);
      }

      // Step 3: Bull vs Bear Debate
      setCurrentStepId(3);
      await new Promise((r) => setTimeout(r, 700));
      addCompletedAgent("bull_bear_debate_agent");
      if (mock.step_results?.bull_bear_debate_agent) {
        updateStepResult("bull_bear_debate_agent", mock.step_results.bull_bear_debate_agent);
      }

      // Step 4: Risk Gatekeeper
      setCurrentStepId(4);
      await new Promise((r) => setTimeout(r, 600));
      addCompletedAgent("risk_management_agent");
      if (mock.step_results?.risk_management_agent) {
        updateStepResult("risk_management_agent", mock.step_results.risk_management_agent);
      }

      // Final Synthesizer Report Streaming
      setFinalReport(mock.output);
      setIsAnalyzing(false);
    },
    [
      resetAnalysis,
      setStock,
      setCurrentStepId,
      setPlan,
      addCompletedAgent,
      updateStepResult,
      setFinalReport,
      setIsAnalyzing,
    ]
  );

  const startAnalysis = useCallback(
    async (queryText: string, forceRefresh: boolean = false) => {
      const { ticker, name } = extractTicker(queryText);
      setStock(ticker, name);

      if (isMockMode) {
        await runMockSimulation(ticker, name, queryText);
        return;
      }

      resetAnalysis();

      // Progressive DAG animation while backend is computing
      const stepTimer1 = setTimeout(() => {
        setCurrentStepId(1);
        addCompletedAgent("data_processing_agent");
        addCompletedAgent("web_search_agent");
      }, 1200);

      const stepTimer2 = setTimeout(() => {
        setCurrentStepId(2);
        addCompletedAgent("fundamental_agent");
        addCompletedAgent("technical_agent");
        addCompletedAgent("dart_disclosure_agent");
        addCompletedAgent("macro_sector_agent");
      }, 3500);

      const stepTimer3 = setTimeout(() => {
        setCurrentStepId(3);
        addCompletedAgent("bull_bear_debate_agent");
      }, 6000);

      const stepTimer4 = setTimeout(() => {
        setCurrentStepId(4);
        addCompletedAgent("risk_management_agent");
      }, 8000);

      try {
        const response = await invokeSupervisor(queryText, undefined, false, forceRefresh);
        clearTimeout(stepTimer1);
        clearTimeout(stepTimer2);
        clearTimeout(stepTimer3);
        clearTimeout(stepTimer4);

        loadResponse(response, name);
      } catch (err) {
        console.error("Live analysis failed, switching to simulation:", err);
        clearTimeout(stepTimer1);
        clearTimeout(stepTimer2);
        clearTimeout(stepTimer3);
        clearTimeout(stepTimer4);
        await runMockSimulation(ticker, name, queryText);
      }
    },
    [
      isMockMode,
      setStock,
      resetAnalysis,
      setCurrentStepId,
      addCompletedAgent,
      loadResponse,
      runMockSimulation,
    ]
  );

  return {
    startAnalysis,
    runMockSimulation,
  };
}
