import { parseAPIError, AuthenticationError } from './errors';
import { AlertsAPI } from './api/alerts';
import { SchedulesAPI } from './api/schedules';
import { PortfoliosAPI } from './api/portfolios';
import { WatchlistsAPI } from './api/watchlists';
import { SettingsAPI } from './api/settings';
import { PerformanceAPI } from './api/performance';
import { AnalysisAPI } from './api/analysis';
import { ComparisonAPI } from './api/comparison';

export const API_BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) || 'http://localhost:8000';

/**
 * Request options for API calls
 */
export interface RequestOptions extends Omit<RequestInit, 'body' | 'method'> {
  /** AbortController signal for request cancellation */
  signal?: AbortSignal;
}

/**
 * Core API client with automatic auth injection and error handling
 */
export class APIClient {
  private baseURL: string;
  private getToken: () => string | null;
  private onAuthError?: () => void;

  // Resource APIs
  public readonly alerts: AlertsAPI;
  public readonly schedules: SchedulesAPI;
  public readonly portfolios: PortfoliosAPI;
  public readonly watchlists: WatchlistsAPI;
  public readonly settings: SettingsAPI;
  public readonly performance: PerformanceAPI;
  public readonly analysis: AnalysisAPI;
  public readonly comparison: ComparisonAPI;

  constructor(
    baseURL: string,
    getToken: () => string | null,
    onAuthError?: () => void
  ) {
    this.baseURL = baseURL;
    this.getToken = getToken;
    this.onAuthError = onAuthError;

    // Initialize resource APIs
    this.alerts = new AlertsAPI(this);
    this.schedules = new SchedulesAPI(this);
    this.portfolios = new PortfoliosAPI(this);
    this.watchlists = new WatchlistsAPI(this);
    this.settings = new SettingsAPI(this);
    this.performance = new PerformanceAPI(this);
    this.analysis = new AnalysisAPI(this);
    this.comparison = new ComparisonAPI(this);
  }

  /**
   * Build full URL from endpoint
   */
  private buildURL(endpoint: string): string {
    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${this.baseURL}${normalizedEndpoint}`;
  }

  /**
   * Build headers with automatic auth injection
   */
  private buildHeaders(customHeaders?: HeadersInit, isFormData = false): HeadersInit {
    const headers: Record<string, string> = {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(customHeaders as Record<string, string> || {}),
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  /**
   * Prepare request body and headers
   */
  private preparePayload(data: unknown, customHeaders?: HeadersInit) {
    const isFormData = data instanceof FormData || data instanceof URLSearchParams;
    const body = isFormData ? (data as BodyInit) : (data !== undefined ? JSON.stringify(data) : undefined);
    const headers = this.buildHeaders(customHeaders, isFormData);
    return { body, headers };
  }

  /**
   * Handle API response and errors
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    // Handle no-content responses
    if (response.status === 204) {
      return undefined as T;
    }

    // Try to parse JSON response
    let data: unknown;
    try {
      data = await response.json();
    } catch {
      data = null;
    }

    // Handle errors
    if (!response.ok) {
      const error = parseAPIError(response.status, data);

      // Trigger auth error callback on 401
      if (error instanceof AuthenticationError && this.onAuthError) {
        this.onAuthError();
      }

      throw error;
    }

    return data as T;
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    const response = await fetch(this.buildURL(endpoint), {
      method: 'GET',
      headers: this.buildHeaders(options?.headers),
      signal: options?.signal,
      ...options,
    });

    return this.handleResponse<T>(response);
  }

  /**
   * POST request
   */
  async post<T>(
    endpoint: string,
    data?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    const { body, headers } = this.preparePayload(data, options?.headers);
    const response = await fetch(this.buildURL(endpoint), {
      method: 'POST',
      headers,
      body,
      signal: options?.signal,
      ...options,
    });

    return this.handleResponse<T>(response);
  }

  /**
   * PATCH request
   */
  async patch<T>(
    endpoint: string,
    data?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    const { body, headers } = this.preparePayload(data, options?.headers);
    const response = await fetch(this.buildURL(endpoint), {
      method: 'PATCH',
      headers,
      body,
      signal: options?.signal,
      ...options,
    });

    return this.handleResponse<T>(response);
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    const response = await fetch(this.buildURL(endpoint), {
      method: 'DELETE',
      headers: this.buildHeaders(options?.headers),
      signal: options?.signal,
      ...options,
    });

    return this.handleResponse<T>(response);
  }

  /**
   * PUT request
   */
  async put<T>(
    endpoint: string,
    data?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    const { body, headers } = this.preparePayload(data, options?.headers);
    const response = await fetch(this.buildURL(endpoint), {
      method: 'PUT',
      headers,
      body,
      signal: options?.signal,
      ...options,
    });

    return this.handleResponse<T>(response);
  }
}
