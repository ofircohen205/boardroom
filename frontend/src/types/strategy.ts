/**
 * TypeScript types for trading strategies.
 */

export interface StrategyWeights {
  fundamental: number;
  technical: number;
  sentiment: number;
}

export interface StrategyThresholds {
  buy: number;
  sell: number;
}

export interface StrategyRiskParams {
  max_position_size: number;
  stop_loss?: number;
  take_profit?: number;
}

export interface StrategyConfig {
  weights: StrategyWeights;
  thresholds: StrategyThresholds;
  risk_params: StrategyRiskParams;
}

export interface Strategy {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  config: StrategyConfig;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface StrategyCreate {
  name: string;
  description?: string;
  config: StrategyConfig;
}

export interface StrategyUpdate {
  name?: string;
  description?: string;
  config?: StrategyConfig;
  is_active?: boolean;
}
