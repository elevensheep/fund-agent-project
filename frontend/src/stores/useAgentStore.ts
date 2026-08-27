import { create } from "zustand";
import { ExecutionPlan, ExecutiveMetrics, InvokeResponse, RecommendationResponse, StepResults } from "@/types/agent";

interface AgentState {
  ticker: string;
  stockName: string;
  query: string;
  intent: string;
  isAnalyzing: boolean;
  currentStepId: number;
  completedAgents: string[];
  plan: ExecutionPlan | null;
  stepResults: StepResults;
  executiveMetrics: ExecutiveMetrics | null;
  recommendation: RecommendationResponse | null;
  finalReport: string;
  streamingTokens: string;
  isCached: boolean;
  cachedAt: string | null;
  ttlRemaining: number | null;
  activeTab: "dashboard" | "dag" | "report" | "recommendation" | "monitoring";
  isSystemStatusOpen: boolean;
  history: Array<{ ticker: string; name: string; query: string; timestamp: string }>;

  // Actions
  setQuery: (query: string) => void;
  setStock: (ticker: string, stockName: string) => void;
  setIntent: (intent: string) => void;
  setIsAnalyzing: (isAnalyzing: boolean) => void;
  setCurrentStepId: (stepId: number) => void;
  addCompletedAgent: (agentName: string) => void;
  setPlan: (plan: ExecutionPlan | null) => void;
  setStepResults: (results: StepResults) => void;
  updateStepResult: (agentName: string, result: any) => void;
  setExecutiveMetrics: (metrics: ExecutiveMetrics | null) => void;
  setRecommendation: (rec: RecommendationResponse | null) => void;
  setFinalReport: (report: string) => void;
  appendStreamingToken: (token: string) => void;
  setIsCached: (isCached: boolean, cachedAt?: string, ttl?: number) => void;
  setActiveTab: (tab: "dashboard" | "dag" | "report" | "recommendation" | "monitoring") => void;
  setIsSystemStatusOpen: (open: boolean) => void;
  resetAnalysis: () => void;
  loadResponse: (resp: InvokeResponse, stockName?: string) => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  ticker: "",
  stockName: "",
  query: "",
  intent: "FULL_ANALYSIS",
  isAnalyzing: false,
  currentStepId: 0,
  completedAgents: [],
  plan: null,
  stepResults: {},
  executiveMetrics: null,
  recommendation: null,
  finalReport: "",
  streamingTokens: "",
  isCached: false,
  cachedAt: null,
  ttlRemaining: null,
  activeTab: "dashboard",
  isSystemStatusOpen: false,
  history: [],

  setQuery: (query) => set({ query }),
  setStock: (ticker, stockName) => set({ ticker, stockName }),
  setIntent: (intent) => set({ intent }),
  setIsAnalyzing: (isAnalyzing) => set({ isAnalyzing }),
  setCurrentStepId: (currentStepId) => set({ currentStepId }),
  addCompletedAgent: (agentName) =>
    set((state) => ({
      completedAgents: state.completedAgents.includes(agentName)
        ? state.completedAgents
        : [...state.completedAgents, agentName],
    })),
  setPlan: (plan) => set({ plan }),
  setStepResults: (stepResults) => set({ stepResults }),
  updateStepResult: (agentName, result) =>
    set((state) => ({
      stepResults: { ...state.stepResults, [agentName]: result },
    })),
  setExecutiveMetrics: (executiveMetrics) => set({ executiveMetrics }),
  setRecommendation: (recommendation) => set({ recommendation }),
  setFinalReport: (finalReport) => set({ finalReport }),
  appendStreamingToken: (token) =>
    set((state) => ({
      streamingTokens: state.streamingTokens + token,
    })),
  setIsCached: (isCached, cachedAt, ttlRemaining) =>
    set({ isCached, cachedAt: cachedAt || null, ttlRemaining: ttlRemaining || null }),
  setActiveTab: (activeTab) => set({ activeTab }),
  setIsSystemStatusOpen: (isSystemStatusOpen) => set({ isSystemStatusOpen }),

  resetAnalysis: () =>
    set({
      isAnalyzing: true,
      currentStepId: 1,
      completedAgents: [],
      stepResults: {},
      executiveMetrics: null,
      recommendation: null,
      finalReport: "",
      streamingTokens: "",
      isCached: false,
      cachedAt: null,
      ttlRemaining: null,
    }),

  loadResponse: (resp, stockName) =>
    set((state) => {
      const isRec = Boolean(resp.recommendation);
      return {
        isAnalyzing: false,
        currentStepId: 4,
        isCached: Boolean(resp.is_cached),
        cachedAt: resp.cached_at || null,
        ttlRemaining: resp.ttl_remaining || null,
        plan: resp.plan || state.plan,
        stepResults: resp.step_results || state.stepResults,
        executiveMetrics: resp.executive_metrics || state.executiveMetrics,
        recommendation: resp.recommendation || null,
        activeTab: isRec ? "recommendation" : state.activeTab,
        finalReport: resp.output,
        completedAgents: resp.used_agents || [
          "data_processing_agent",
          "web_search_agent",
          "fundamental_agent",
          "technical_agent",
          "dart_disclosure_agent",
          "macro_sector_agent",
          "bull_bear_debate_agent",
          "risk_management_agent",
        ],
        stockName: stockName || state.stockName,
        history: [
          {
            ticker: resp.plan?.ticker || state.ticker,
            name: stockName || state.stockName,
            query: state.query,
            timestamp: "방금 전",
          },
          ...state.history.slice(0, 4),
        ],
      };
    }),
}));
