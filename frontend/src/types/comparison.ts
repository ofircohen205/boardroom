import type { Decision } from "./index";

export interface StockRanking {
  ticker: string;
  rank: number;
  score: number;
  rationale: string;
  decision: Decision;
}

export interface RelativeStrength {
  correlation_matrix: Record<string, Record<string, number>>;
  relative_performance: Record<string, number>;
  valuation_comparison: Record<string, Record<string, number>>;
}

export interface ComparisonResult {
  tickers: string[];
  rankings: StockRanking[];
  best_pick: string;
  comparison_summary: string;
  relative_strength?: RelativeStrength;
  price_histories?: Record<string, Array<{ time: string; close: number }>>;
  stock_data?: Record<string, Record<string, unknown>>;  // Full analysis data for each stock
}

export interface ComparisonState {
  tickers: string[];
  results: Record<string, Record<string, unknown>>;  // Per-ticker analysis results
  comparison: ComparisonResult | null;
  isLoading: boolean;
  error: string | null;
}

export interface Sector {
  key: string;
  name: string;
  description: string;
  ticker_count: number;
}
