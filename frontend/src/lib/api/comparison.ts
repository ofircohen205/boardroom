import type { APIClient } from '../apiClient';

export interface Sector {
  key: string;
  name: string;
  ticker_count: number;
}

export interface ComparisonResult {
  best_pick: string;
  comparison_summary: string;
  rankings: Array<{
    ticker: string;
    rank: number;
    score: number;
    decision: {
      action: string;
      confidence: number;
    };
    rationale: string;
  }>;
  stock_data?: Record<string, unknown>;
  price_histories?: Record<string, Array<{ time: string; close: number }>>;
  relative_strength?: {
    relative_performance: Record<string, number>;
  };
}

/**
 * Comparison API - Stock comparison and sector analysis
 */
export class ComparisonAPI {
  constructor(private client: APIClient) {}

  /**
   * Get available sectors
   */
  async getSectors(): Promise<Sector[]> {
    const response = await this.client.get<{ sectors: Sector[] }>('/api/compare/sectors');
    return response.sectors || [];
  }

  /**
   * Compare multiple stocks
   */
  async compareStocks(tickers: string[], market = 'US'): Promise<ComparisonResult> {
    return this.client.post<ComparisonResult>('/api/compare/stocks', { tickers, market });
  }

  /**
   * Analyze stocks in a sector
   */
  async analyzeSector(sector: string, limit = 5, market = 'US'): Promise<ComparisonResult> {
    return this.client.post<ComparisonResult>('/api/compare/sector', { sector, limit, market });
  }
}
