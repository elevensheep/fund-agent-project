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
  stock_name?: string;
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
  debt_ratio?: number;
  upside_rate?: number;
  fcf?: number;
  fcf_summary?: string;
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
  trend?: "UPTREND" | "DOWNTREND" | "SIDEWAYS" | string;
  golden_cross?: boolean;
  rsi_state?: "OVERSOLD" | "NEUTRAL" | "OVERBOUGHT" | string;
}

export interface TechnicalResult {
  ticker: string;
  signal_result: TechnicalSignalResult;
  raw_output?: string;
}

export interface DartDisclosureAnalysis {
  recent_disclosures_count: number;
  dilution_risk: "HIGH" | "MEDIUM" | "LOW" | string;
  overhang_warning: boolean;
  overall_sentiment?: "POSITIVE_HIGH" | "POSITIVE_MODERATE" | "NEUTRAL" | "NEGATIVE_MODERATE" | "NEGATIVE_HIGH" | string;
  cb_bw_status?: string;
  latest_filings?: Array<{
    title: string;
    date: string;
    category: string;
    impact: "POSITIVE" | "NEUTRAL" | "NEGATIVE" | string;
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
  sector_relative_strength?: number;
  rs_description?: string;
  fx_impact?: string;
  rate_impact?: string;
  outlook?: string;
  interest_rate_env?: string;
  fx_usd_krw?: number;
  sector_momentum?: "STRONG_BULL" | "BULL" | "NEUTRAL" | "BEAR" | "LEADING" | "WEAKENING" | "IMPROVING" | "LAGGING" | string;
}

export interface MacroSectorResult {
  ticker: string;
  sector_data: SectorData;
  raw_output?: string;
}

export interface JudgeVerdict {
  decision: "STRONG_BUY" | "BUY" | "HOLD" | "SELL" | "STRONG_SELL" | string;
  confidence_score: number; // 0 to 100
  bull_summary: string;
  bear_summary: string;
  bull_points?: string[];
  bear_points?: string[];
  core_conflict?: string;
  target_price?: number;
  stop_loss_price?: number;
}

export interface BullBearDebateResult {
  ticker: string;
  judge_verdict: JudgeVerdict;
  raw_output?: string;
}

export type RiskVerdict = "APPROVED" | "REJECTED" | "ADJUSTED" | string;

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

export interface ExecutiveMetrics {
  current_price: number;
  target_price_low: number;
  target_price_high: number;
  target_price_str: string;
  stop_loss_price: number;
  stop_loss_str: string;
  approved_weight: number;
  approved_weight_str: string;
  confidence_score: number;
  confidence_str: string;
  financial_grade: string;
  support_levels?: number[];
  resistance_levels?: number[];
  investment_opinion?: string;
}

export interface InvokeResponse {
  status?: "success" | "error";
  output: string;
  used_agents: string[];
  plan?: ExecutionPlan;
  remote_response?: string | Record<string, any>;
  step_results?: StepResults;
  executive_metrics?: ExecutiveMetrics;
  recommendation?: RecommendationResponse | null;
  session_id?: string;
  timestamp?: string;
  is_cached?: boolean;
  cached_at?: string;
  ttl_remaining?: number;
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

export interface RecommendedStock {
  rank: number;
  ticker: string;
  name: string;
  current_price: number;
  opinion: string;
  target_price_range: [number, number];
  target_price_str: string;
  upside_percent: number;
  buy_levels: [number, number];
  stop_loss_price: number;
  approved_weight: number;
  financial_grade: string;
  key_catalyst: string;
}

export interface PortfolioSummary {
  total_equity_weight: number;
  cash_reserve_weight: number;
  expected_return: string;
  risk_level: string;
}

export interface RecommendationResponse {
  intent: string;
  theme: string;
  recommended_stocks: RecommendedStock[];
  portfolio_summary: PortfolioSummary;
  report_markdown: string;
}

