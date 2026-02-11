/**
 * TypeScript types for paper trading.
 */

export interface PaperPosition {
  id: string;
  ticker: string;
  quantity: number;
  average_entry_price: number;
  current_price?: number;
  market_value?: number;
  unrealized_pnl?: number;
  unrealized_pnl_pct?: number;
  created_at: string;
  updated_at: string;
}

export interface PaperAccount {
  id: string;
  user_id: string;
  strategy_id: string;
  name: string;
  initial_balance: number;
  current_balance: number;
  total_value?: number;
  total_pnl?: number;
  total_pnl_pct?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  positions?: PaperPosition[];
}

export interface PaperAccountCreate {
  name: string;
  strategy_id: string;
  initial_balance: number;
}

export interface PaperTrade {
  id: string;
  account_id: string;
  ticker: string;
  trade_type: "BUY" | "SELL";
  quantity: number;
  price: number;
  total_value: number;
  analysis_session_id?: string;
  executed_at: string;
}

export interface PaperTradeRequest {
  ticker: string;
  trade_type: "BUY" | "SELL";
  quantity: number;
  price?: number;
  analysis_session_id?: string;
}

export interface PaperPerformance {
  account_id: string;
  initial_balance: number;
  current_value: number;
  total_return: number;
  total_pnl: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  avg_win?: number;
  avg_loss?: number;
  largest_win?: number;
  largest_loss?: number;
  equity_curve?: Array<{ date: string; value: number }>;
}
