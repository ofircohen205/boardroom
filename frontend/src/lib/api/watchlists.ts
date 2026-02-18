import type { APIClient } from '../apiClient';
import type { Watchlist, CreateWatchlistInput, AddWatchlistItemInput, WatchlistItem } from './types';

/**
 * Watchlists API - Watchlist management
 */
export class WatchlistsAPI {
  constructor(private client: APIClient) {}

  /**
   * List all watchlists
   */
  async list(): Promise<Watchlist[]> {
    return this.client.get<Watchlist[]>('/api/watchlists');
  }

  /**
   * Get a specific watchlist by ID
   */
  async get(id: string): Promise<Watchlist> {
    return this.client.get<Watchlist>(`/api/watchlists/${id}`);
  }

  /**
   * Create a new watchlist
   */
  async create(data: CreateWatchlistInput): Promise<Watchlist> {
    return this.client.post<Watchlist>('/api/watchlists', data);
  }

  /**
   * Delete a watchlist
   */
  async delete(id: string): Promise<void> {
    return this.client.delete<void>(`/api/watchlists/${id}`);
  }

  /**
   * Add an item to a watchlist
   */
  async addItem(watchlistId: string, data: AddWatchlistItemInput): Promise<WatchlistItem> {
    return this.client.post<WatchlistItem>(`/api/watchlists/${watchlistId}/items`, data);
  }

  /**
   * Remove an item from a watchlist
   */
  async removeItem(watchlistId: string, itemId: string): Promise<void> {
    return this.client.delete<void>(`/api/watchlists/${watchlistId}/items/${itemId}`);
  }
}
