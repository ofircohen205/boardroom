import type { APIClient } from '../apiClient';
import type { Schedule, CreateScheduleInput } from './types';

/**
 * Schedules API - Scheduled analysis management
 */
export class SchedulesAPI {
  constructor(private client: APIClient) {}

  /**
   * List all scheduled analyses
   */
  async list(): Promise<Schedule[]> {
    return this.client.get<Schedule[]>('/api/schedules');
  }

  /**
   * Create a new scheduled analysis
   */
  async create(data: CreateScheduleInput): Promise<Schedule> {
    return this.client.post<Schedule>('/api/schedules', data);
  }

  /**
   * Delete a scheduled analysis
   */
  async delete(id: string): Promise<void> {
    return this.client.delete<void>(`/api/schedules/${id}`);
  }

  /**
   * Toggle schedule active status
   */
  async toggle(id: string, active: boolean): Promise<Schedule> {
    return this.client.patch<Schedule>(`/api/schedules/${id}/toggle`, { active });
  }
}
