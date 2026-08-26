import { create } from "zustand";
import { ExecutionPlan, InvokeResponse, StepResults } from "@/types/agent";
import { MOCK_RESPONSES } from "@/lib/mockData";

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
  finalReport: string;
  streamingTokens: string;
  isMockMode: boolean;
  activeTab: "dashboard" | "dag" | "report" | "monitoring";
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
  setFinalReport: (report: string) => void;
  appendStreamingToken: (token: string) => void;
  setMockMode: (isMock: boolean) => void;
  setActiveTab: (tab: "dashboard" | "dag" | "report" | "monitoring") => void;
  setIsSystemStatusOpen: (open: boolean) => void;
  resetAnalysis: () => void;
  loadResponse: (resp: InvokeResponse, stockName?: string) => void;
}

const defaultSamsung = MOCK_RESPONSES["005930"];

export const useAgentStore = create<AgentState>((set) => ({
  ticker: "005930",
  stockName: "삼성전자",
  query: "삼성전자(005930) 종합 분석 및 투자 심의해줘",
  intent: "FULL_ANALYSIS",
  isAnalyzing: false,
  currentStepId: 4,
  completedAgents: [
    "data_processing_agent",
    "web_search_agent",
    "fundamental_agent",
    "technical_agent",
    "dart_disclosure_agent",
    "macro_sector_agent",
    "bull_bear_debate_agent",
    "risk_management_agent",
  ],
  plan: defaultSamsung.plan || null,
  stepResults: defaultSamsung.step_results || {},
  finalReport: defaultSamsung.output,
  streamingTokens: "",
  isMockMode: false,
  activeTab: "dashboard",
  isSystemStatusOpen: false,
  history: [
    { ticker: "005930", name: "삼성전자", query: "삼성전자 종합 분석", timestamp: "방금 전" },
    { ticker: "000660", name: "SK하이닉스", query: "SK하이닉스 HBM 분석", timestamp: "1시간 전" },
    { ticker: "005380", name: "현대차", query: "현대차 밸류에이션", timestamp: "어제" },
  ],

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
  setFinalReport: (finalReport) => set({ finalReport }),
  appendStreamingToken: (token) =>
    set((state) => ({ streamingTokens: state.streamingTokens + token })),
  setMockMode: (isMockMode) => set({ isMockMode }),
  setActiveTab: (activeTab) => set({ activeTab }),
  setIsSystemStatusOpen: (isSystemStatusOpen) => set({ isSystemStatusOpen }),

  resetAnalysis: () =>
    set({
      isAnalyzing: true,
      currentStepId: 1,
      completedAgents: [],
      stepResults: {},
      finalReport: "",
      streamingTokens: "",
    }),

  loadResponse: (resp, stockName) =>
    set((state) => ({
      isAnalyzing: false,
      currentStepId: 4,
      plan: resp.plan || state.plan,
      stepResults: resp.step_results || state.stepResults,
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
    })),
}));
