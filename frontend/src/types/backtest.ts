/**
 * TypeScript types for backtesting features.
 */

export interface EquityPoint {
  date: string;
  equity: number;
  cash: number;
  position_value: number;
}

export interface Trade {
  date: string;
  type: "BUY" | "SELL";
  quantity: number;
  price: number;
  total: number;
  commission?: number;
}

export interface BacktestResult {
  id?: string;
  ticker: string;
  strategy_id: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  total_return: number;
  annualized_return: number;
  sharpe_ratio: number | null;
  max_drawdown: number;
  win_rate: number;
  total_trades: number;
  buy_and_hold_return: number;
  equity_curve: EquityPoint[];
  trades: Trade[];
  execution_time_seconds: number | null;
}

export interface BacktestConfig {
  ticker: string;
  strategy_id: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  check_frequency: "daily" | "weekly";
  position_size_pct: number;
  stop_loss_pct?: number;
  take_profit_pct?: number;
}

export interface BacktestProgress {
  status: "idle" | "fetching_data" | "running_backtest" | "completed" | "error";
  message?: string;
  progress_pct?: number;
}
