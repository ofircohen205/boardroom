import type { APIClient } from '../apiClient';
import type { PerformanceTimeline, AgentStats, AnalysisOutcome, PerformanceSummary } from './types';

/**
 * Performance API - Performance tracking and analytics
 */
export class PerformanceAPI {
  constructor(private client: APIClient) {}

  /**
   * Get performance summary
   */
  async getSummary(): Promise<PerformanceSummary> {
    return this.client.get<PerformanceSummary>('/api/performance/summary');
  }

  /**
   * Get performance timeline data
   * @param days - Number of days to include (default: 30)
   */
  async getTimeline(days = 30): Promise<PerformanceTimeline[]> {
    return this.client.get<PerformanceTimeline[]>(`/api/performance/timeline?days=${days}`);
  }

  /**
   * Get agent statistics
   * @param agentName - Specific agent name (optional)
   */
  async getAgentStats(agentName?: string): Promise<AgentStats[]> {
    const endpoint = agentName
      ? `/api/performance/agents/${agentName}`
      : '/api/performance/agents';
    return this.client.get<AgentStats[]>(endpoint);
  }

  /**
   * Get analysis outcomes
   * @param limit - Maximum number of outcomes to return
   */
  async getOutcomes(limit = 20): Promise<AnalysisOutcome[]> {
    return this.client.get<AnalysisOutcome[]>(`/api/performance/recent?limit=${limit}`);
  }
}
