import type { APIClient } from '../apiClient';
import type {
  UserProfile,
  UpdateProfileInput,
  UpdatePasswordInput,

} from './types';

/**
 * Settings API - User profile and settings management
 */
export class SettingsAPI {
  constructor(private client: APIClient) {}

  /**
   * Get user profile
   */
  async getProfile(): Promise<UserProfile> {
    return this.client.get<UserProfile>('/api/settings/profile');
  }

  /**
   * Update user profile
   */
  async updateProfile(data: UpdateProfileInput): Promise<UserProfile> {
    return this.client.patch<UserProfile>('/api/settings/profile', data);
  }

  /**
   * Update password
   */
  async updatePassword(data: UpdatePasswordInput): Promise<void> {
    return this.client.post<void>('/api/settings/password', data);
  }
}
