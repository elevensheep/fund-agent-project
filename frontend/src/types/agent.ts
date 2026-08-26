export type QueryIntent = "FULL_ANALYSIS" | "NEWS_ONLY" | "CHART_ONLY" | "DEBATE_ONLY" | "RISK_ONLY";

export interface PlanStep {
  step_id: number;
  agent_name: string;
  task_prompt: string;
  description?: string;
  status?: "pending" | "running" | "completed" | "error";
  duration_ms?: number;
}

export interface ExecutionPlan {
  ticker: string;
  query_intent: QueryIntent | string;
  steps: PlanStep[];
}

export interface DataProcessingMetrics {
  current_price: number;
  open_price?: number;
  high_price?: number;
  low_price?: number;
  change?: number;
  change_percent?: number;
  volume?: number;
  sma_20: number;
  sma_60: number;
  sma_120: number;
  rsi_14: number;
}

export interface NewsAnalysis {
  sentiment: "POSITIVE" | "NEUTRAL" | "NEGATIVE";
  sentiment_score: number; // -1.0 to +1.0
  key_keywords: string[];
  recent_news_count?: number;
}

export interface DataProcessingResult {
  ticker: string;
  technical_metrics: DataProcessingMetrics;
  news_analysis: NewsAnalysis;
  raw_output?: string;
}

export interface WebSearchSource {
  title: string;
  url: string;
  snippet: string;
  date?: string;
}

export interface WebSearchResult {
  query: string;
  summary: string;
  sources: WebSearchSource[];
  raw_output?: string;
}

export interface ValuationMetrics {
  per: number;
  pbr: number;
  roe: number;
  grade: "S" | "A" | "B" | "C" | "D";
  target_price_range: [number, number];
  eps?: number;
  bps?: number;
  dividend_yield?: number;
  industry_avg_per?: number;
}

export interface FundamentalResult {
  ticker: string;
  valuation_metrics: ValuationMetrics;
  analysis_summary?: string;
  raw_output?: string;
}

export type SignalType = "STRONG_BUY" | "BUY" | "NEUTRAL" | "SELL" | "STRONG_SELL";

export interface TechnicalSignalResult {
  signal: SignalType;
  support_levels: number[];
  resistance_levels: number[];
  atr_14: number;
  trend?: "UPTREND" | "DOWNTREND" | "SIDEWAYS";
  golden_cross?: boolean;
  rsi_state?: "OVERSOLD" | "NEUTRAL" | "OVERBOUGHT";
}

export interface TechnicalResult {
  ticker: string;
  signal_result: TechnicalSignalResult;
  raw_output?: string;
}

export interface DartDisclosureAnalysis {
  recent_disclosures_count: number;
  dilution_risk: "HIGH" | "MEDIUM" | "LOW";
  overhang_warning: boolean;
  overall_sentiment?: "POSITIVE_HIGH" | "NEUTRAL" | "NEGATIVE_HIGH";
  cb_bw_status?: string;
  latest_filings?: Array<{
    title: string;
    date: string;
    category: string;
    impact: "POSITIVE" | "NEUTRAL" | "NEGATIVE";
  }>;
}

export interface DartDisclosureResult {
  ticker: string;
  disclosure_analysis: DartDisclosureAnalysis;
  raw_output?: string;
}

export interface SectorData {
  sector_name: string;
  relative_strength_rank: number; // 1 to 20
  macro_score: number; // 0 to 100
  interest_rate_env?: string;
  fx_usd_krw?: number;
  sector_momentum?: "LEADING" | "WEAKENING" | "IMPROVING" | "LAGGING";
}

export interface MacroSectorResult {
  ticker: string;
  sector_data: SectorData;
  raw_output?: string;
}

export interface JudgeVerdict {
  decision: "STRONG_BUY" | "BUY" | "HOLD" | "SELL" | "STRONG_SELL";
  confidence_score: number; // 0 to 100
  bull_summary: string;
  bear_summary: string;
  bull_points?: string[];
  bear_points?: string[];
  core_conflict?: string;
}

export interface BullBearDebateResult {
  ticker: string;
  judge_verdict: JudgeVerdict;
  raw_output?: string;
}

export type RiskVerdict = "APPROVED" | "REJECTED" | "ADJUSTED";

export interface RiskManagementResult {
  ticker: string;
  verdict: RiskVerdict;
  approved_weight: number; // 0.0 to 0.15 (Max 15%)
  stop_loss_price: number;
  panic_market_flag: boolean;
  reason: string;
  max_weight?: number;
  atr_multiplier?: number;
  raw_output?: string;
}

export interface StepResults {
  data_processing_agent?: DataProcessingResult | string;
  web_search_agent?: WebSearchResult | string;
  fundamental_agent?: FundamentalResult | string;
  technical_agent?: TechnicalResult | string;
  dart_disclosure_agent?: DartDisclosureResult | string;
  macro_sector_agent?: MacroSectorResult | string;
  bull_bear_debate_agent?: BullBearDebateResult | string;
  risk_management_agent?: RiskManagementResult | string;
  [key: string]: any;
}

export interface InvokeResponse {
  status?: "success" | "error";
  output: string;
  used_agents: string[];
  plan?: ExecutionPlan;
  remote_response?: string | Record<string, any>;
  step_results?: StepResults;
  session_id?: string;
  timestamp?: string;
}

export interface CandleData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface SmaLineData {
  time: string;
  value: number;
}

export interface StockQuote {
  ticker: string;
  name: string;
  market: "KOSPI" | "KOSDAQ";
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  prevClose: number;
  updatedAt: string;
}

export interface AgentCardInfo {
  name: string;
  description: string;
  supportedInterfaces?: Array<{ url: string; protocolBinding: string; protocolVersion: string }>;
  version?: string;
  capabilities?: { streaming: boolean; pushNotifications: boolean };
}

export interface SupervisorInfo {
  name: string;
  llm_provider: string;
  remote_agents: Record<string, string>;
  agent_cards: Record<string, string | AgentCardInfo>;
}
