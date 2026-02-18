/**
 * Shared type definitions for API resources
 */

// ==================== Alerts ====================
export interface Alert {
  id: string;
  ticker: string;
  market: string;
  condition: string;
  target_value: number;
  triggered: boolean;
  triggered_at: string | null;
  active: boolean;
  created_at: string;
}

export interface CreateAlertInput {
  ticker: string;
  market: string;
  condition: string;
  target_value: number;
}

// ==================== Schedules ====================
export interface Schedule {
  id: string;
  ticker: string;
  market: string;
  frequency: string;
  time: string;
  active: boolean;
  last_run: string | null;
  next_run: string | null;
  created_at: string;
}

export interface CreateScheduleInput {
  ticker: string;
  market: string;
  frequency: string;
  time: string;
}

// ==================== Portfolios ====================
export interface Portfolio {
  id: string;
  name: string;
  created_at: string;
  positions: Position[];
}

export interface Position {
  id: string;
  portfolio_id: string;
  ticker: string;
  market: string;
  quantity: number;
  avg_entry_price: number;
  added_at: string;
}

export interface CreatePortfolioInput {
  name: string;
}

export interface AddPositionInput {
  ticker: string;
  market: string;
  quantity: number;
  entry_price: number;
}

// ==================== Watchlists ====================
export interface Watchlist {
  id: string;
  name: string;
  created_at: string;
  items: WatchlistItem[];
}

export interface WatchlistItem {
  id: string;
  watchlist_id: string;
  ticker: string;
  market: string;
  added_at: string;
}

export interface CreateWatchlistInput {
  name: string;
}

export interface AddWatchlistItemInput {
  ticker: string;
  market: string;
}

// ==================== Settings ====================
export interface UserProfile {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  created_at: string;
}

export interface UpdateProfileInput {
  first_name?: string;
  last_name?: string;
  email?: string;
}

export interface UpdatePasswordInput {
  current_password: string;
  new_password: string;
}



// ==================== Performance ====================
export interface PerformanceTimeline {
  date: string;
  accuracy: number;
  total_decisions: number;
}

export interface AgentStats {
  agent_name: string;
  accuracy: number;
  total_decisions: number;
  correct_predictions: number;
  last_30_days_accuracy: number;
}

export interface AnalysisOutcome {
  id: string;
  session_id: string;
  ticker: string;
  market: string;
  action: string;
  confidence: number;
  recommendation_price: number;
  outcome_price: number | null;
  is_correct: boolean | null;
  decided_at: string;
  evaluated_at: string | null;
}

export interface PerformanceSummary {
  total_analyses: number;
  tracked_outcomes: number;
  accuracy_7d: number;
  accuracy_30d: number;
}

// ==================== Analysis ====================
export interface AnalysisSession {
  id: string;
  ticker: string;
  market: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  final_decision: FinalDecision | null;
  agent_reports: AgentReport[];
}

export interface FinalDecision {
  action: string;
  confidence: number;
  reasoning: string;
  key_factors: string[];
  price_target: number | null;
}

export interface AgentReport {
  agent_type: string;
  summary: string;
  data: Record<string, unknown>;
  completed_at: string;
}
