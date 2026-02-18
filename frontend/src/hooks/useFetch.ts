import { useState, useEffect, useCallback } from 'react';

/**
 * Options for useFetch hook
 */
export interface UseFetchOptions<T> {
  /** Auto-fetch on mount (default: true) */
  immediate?: boolean;
  /** Re-fetch when dependencies change */
  dependencies?: unknown[];
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
  const { immediate = true, dependencies = [], onSuccess, onError } = options;
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(immediate);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await fetcher();
      setData(result);
      onSuccess?.(result);
    } catch (err: unknown) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const errorMsg = (err as any).message || 'An error occurred';
      setError(errorMsg);
      onError?.(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, [fetcher, onSuccess, onError]);

  useEffect(() => {
    if (immediate) {
      execute();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...dependencies, execute, immediate]);

  return {
    data,
    isLoading,
    error,
    /** Manually re-fetch data */
    refetch: execute,
  };
}
