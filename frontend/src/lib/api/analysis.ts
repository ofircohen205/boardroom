import type { APIClient } from '../apiClient';
import type { AnalysisSession } from './types';

/**
 * Analysis API - Analysis history and session management
 */
export class AnalysisAPI {
  constructor(private client: APIClient) {}

  /**
   * Get analysis history
   * @param limit - Maximum number of sessions to return
   */
  async getHistory(limit = 20): Promise<AnalysisSession[]> {
    return this.client.get<AnalysisSession[]>(`/api/analysis/history?limit=${limit}`);
  }

  /**
   * Get a specific analysis session
   */
  async getSession(id: string): Promise<AnalysisSession> {
    return this.client.get<AnalysisSession>(`/api/analysis/sessions/${id}`);
  }
}
