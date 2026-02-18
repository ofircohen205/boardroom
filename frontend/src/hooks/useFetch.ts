import { useState, useEffect, useCallback } from 'react';

/**
 * Options for useFetch hook
 */
export interface UseFetchOptions<T> {
  /** Auto-fetch on mount (default: true) */
  immediate?: boolean;
  /** Re-fetch when dependencies change */
  dependencies?: any[];
  /** Success callback */
  onSuccess?: (data: T) => void;
  /** Error callback */
  onError?: (error: string) => void;
}

/**
 * Reusable hook for data fetching with loading/error states
 *
 * Consolidates common pattern of fetch + loading + error handling
 *
 * @example
 * ```tsx
 * const { data, isLoading, error, refetch } = useFetch(
 *   () => apiClient.alerts.list(),
 *   { dependencies: [apiClient] }
 * );
 * ```
 */
export function useFetch<T>(
  fetcher: () => Promise<T>,
  options: UseFetchOptions<T> = {}
) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(options.immediate !== false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await fetcher();
      setData(result);
      options.onSuccess?.(result);
    } catch (err: any) {
      const errorMsg = err.message || 'An error occurred';
      setError(errorMsg);
      options.onError?.(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, [fetcher, options.onSuccess, options.onError]);

  useEffect(() => {
    if (options.immediate !== false) {
      execute();
    }
  }, options.dependencies || [execute]);

  return {
    data,
    isLoading,
    error,
    /** Manually re-fetch data */
    refetch: execute,
  };
}
