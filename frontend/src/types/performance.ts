export interface PerformanceSummary {
  total_analyses: number;
  tracked_outcomes: number;
  accuracy_7d: number;
  accuracy_30d: number;
  best_calls: Call[];
  worst_calls: Call[];
}

export interface Call {
  ticker: string;
  action: string;
  price_at_recommendation: number;
  price_after_period: number;
  performance: number;
}

export interface AgentAccuracy {
  agent_type: string;
  period: string;
  total_signals: number;
  correct_signals: number;
  accuracy: number;
}

export interface RecentOutcome {
  ticker: string;
  action_recommended: string;
  price_at_recommendation: number;
  price_after_7d: number | null;
  outcome_correct: boolean | null;
  created_at: string;
}

export interface TimelinePoint {
  date: string;
  accuracy: number;
}

export interface AgentPerformance {
  agent_type: string;
  overall_accuracy: number;
  action_accuracy: {
    [action: string]: number;
  };
}
