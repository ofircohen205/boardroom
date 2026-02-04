export type Market = "US" | "TASE";
export type Action = "BUY" | "SELL" | "HOLD";
export type Trend = "bullish" | "bearish" | "neutral";
export type AgentType = "fundamental" | "sentiment" | "technical" | "risk" | "chairperson";
export type WSMessageType = "analysis_started" | "agent_started" | "agent_completed" | "veto" | "decision" | "error";

export interface WSMessage {
  type: WSMessageType;
  agent: AgentType | null;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface FundamentalReport {
  revenue_growth: number;
  pe_ratio: number;
  debt_to_equity: number;
  market_cap: number;
  summary: string;
}

export interface SentimentReport {
  overall_sentiment: number;
  news_items: NewsItem[];
  social_mentions: SocialMention[];
  summary: string;
}

export interface NewsItem {
  source: string;
  title: string;
  url: string;
  published_at: string;
  sentiment: number;
  snippet: string;
}

export interface SocialMention {
  source: string;
  content: string;
  author: string;
  url: string;
  timestamp: string;
  engagement: number;
}

export interface TechnicalReport {
  current_price: number;
  ma_50: number;
  ma_200: number;
  rsi: number;
  trend: Trend;
  price_history: PricePoint[];
  summary: string;
}

export interface PricePoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface RiskAssessment {
  sector: string;
  portfolio_sector_weight: number;
  var_95: number;
  veto: boolean;
  veto_reason: string | null;
}

export interface Decision {
  action: Action;
  confidence: number;
  rationale: string;
}

export interface AnalysisState {
  ticker: string | null;
  market: Market;
  fundamental: FundamentalReport | null;
  sentiment: SentimentReport | null;
  technical: TechnicalReport | null;
  risk: RiskAssessment | null;
  decision: Decision | null;
  activeAgents: Set<AgentType>;
  completedAgents: Set<AgentType>;
  vetoed: boolean;
  error: string | null;
}
