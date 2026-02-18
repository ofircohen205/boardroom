import { useState, useCallback } from 'react';

/**
 * Options for useMutation hook
 */
export interface UseMutationOptions<TData> {
  /** Success callback */
  onSuccess?: (data: TData) => void;
  /** Error callback */
  onError?: (error: string) => void;
}

/**
 * Reusable hook for mutations (create/update/delete) with loading/error states
 *
 * Standardizes pattern for write operations
 *
 * @example
 * ```tsx
 * const { mutate, isLoading, error } = useMutation(
 *   (data: CreateAlertInput) => apiClient.alerts.create(data),
 *   {
 *     onSuccess: () => {
 *       setShowForm(false);
 *       refetch();
 *     }
 *   }
 * );
 *
 * const handleSubmit = (e) => {
 *   e.preventDefault();
 *   mutate({ ticker, market, condition, target_value });
 * };
 * ```
 */
export function useMutation<TData, TVariables = void>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options: UseMutationOptions<TData> = {}
) {
  const { onSuccess, onError } = options;
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mutate = useCallback(
    async (variables: TVariables): Promise<TData | undefined> => {
      setIsLoading(true);
      setError(null);

      try {
        const result = await mutationFn(variables);
        onSuccess?.(result);
        return result;
      } catch (err: unknown) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const errorMsg = (err as any).message || 'Operation failed';
        setError(errorMsg);
        onError?.(errorMsg);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [mutationFn, onSuccess, onError]
  );

  const reset = useCallback(() => {
    setError(null);
  }, []);

  return {
    /** Execute the mutation */
    mutate,
    /** Loading state */
    isLoading,
    /** Error message (if any) */
    error,
    /** Reset error state */
    reset,
  };
}
