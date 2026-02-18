import type { APIClient } from '../apiClient';
import type { Portfolio, CreatePortfolioInput, AddPositionInput, Position } from './types';

/**
 * Portfolios API - Portfolio and position management
 */
export class PortfoliosAPI {
  constructor(private client: APIClient) {}

  /**
   * List all portfolios
   */
  async list(): Promise<Portfolio[]> {
    return this.client.get<Portfolio[]>('/api/portfolios');
  }

  /**
   * Get a specific portfolio by ID
   */
  async get(id: string): Promise<Portfolio> {
    return this.client.get<Portfolio>(`/api/portfolios/${id}`);
  }

  /**
   * Create a new portfolio
   */
  async create(data: CreatePortfolioInput): Promise<Portfolio> {
    return this.client.post<Portfolio>('/api/portfolios', data);
  }

  /**
   * Delete a portfolio
   */
  async delete(id: string): Promise<void> {
    return this.client.delete<void>(`/api/portfolios/${id}`);
  }

  /**
   * Add a position to a portfolio
   */
  async addPosition(portfolioId: string, data: AddPositionInput): Promise<Position> {
    return this.client.post<Position>(`/api/portfolios/${portfolioId}/positions`, data);
  }

  /**
   * Delete a position from a portfolio
   */
  async deletePosition(portfolioId: string, positionId: string): Promise<void> {
    return this.client.delete<void>(`/api/portfolios/${portfolioId}/positions/${positionId}`);
  }
}
