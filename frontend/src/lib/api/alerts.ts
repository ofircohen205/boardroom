import type { APIClient } from '../apiClient';
import type { Alert, CreateAlertInput } from './types';

/**
 * Alerts API - Price alert management
 */
export class AlertsAPI {
  constructor(private client: APIClient) {}

  /**
   * List all alerts
   * @param activeOnly - If true, only return active alerts
   */
  async list(activeOnly = false): Promise<Alert[]> {
    return this.client.get<Alert[]>(`/api/alerts?active_only=${activeOnly}`);
  }

  /**
   * Create a new alert
   */
  async create(data: CreateAlertInput): Promise<Alert> {
    return this.client.post<Alert>('/api/alerts', data);
  }

  /**
   * Delete an alert
   */
  async delete(id: string): Promise<void> {
    return this.client.delete<void>(`/api/alerts/${id}`);
  }

  /**
   * Toggle alert active status
   */
  async toggle(id: string, active: boolean): Promise<Alert> {
    return this.client.patch<Alert>(`/api/alerts/${id}/toggle`, { active });
  }

  /**
   * Reset a triggered alert
   */
  async reset(id: string): Promise<Alert> {
    return this.client.patch<Alert>(`/api/alerts/${id}/reset`);
  }
}
