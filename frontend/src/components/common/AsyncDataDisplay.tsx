import type { ReactNode } from 'react';
import type { LucideIcon } from 'lucide-react';
import { LoadingState } from './LoadingState';
import { ErrorState } from './ErrorState';
import { EmptyState } from './EmptyState';

interface AsyncDataDisplayProps<T> {
  /** Loading state */
  isLoading: boolean;
  /** Error message (if any) */
  error: string | null;
  /** Data to display */
  data: T | null;
  /** Custom empty check (default: array length check) */
  isEmpty?: (data: T) => boolean;
  /** Empty state message */
  emptyMessage?: string;
  /** Empty state icon */
  emptyIcon?: LucideIcon;
  /** Loading state message */
  loadingMessage?: string;
  /** Retry callback for error state */
  onRetry?: () => void;
  /** Render function for data */
  children: (data: T) => ReactNode;
}

/**
 * Unified wrapper for loading/error/empty states
 *
 * Consolidates common pattern of conditional rendering
 *
 * @example
 * ```tsx
 * <AsyncDataDisplay
 *   isLoading={isLoading}
 *   error={error}
 *   data={alerts}
 *   emptyMessage="No alerts yet"
 *   emptyIcon={Bell}
 *   onRetry={refetch}
 * >
 *   {(alerts) => (
 *     <div className="space-y-3">
 *       {alerts.map(alert => <AlertCard key={alert.id} alert={alert} />)}
 *     </div>
 *   )}
 * </AsyncDataDisplay>
 * ```
 */
export function AsyncDataDisplay<T>({
  isLoading,
  error,
  data,
  isEmpty = (d) => Array.isArray(d) && d.length === 0,
  emptyMessage = 'No data available',
  emptyIcon,
  loadingMessage,
  onRetry,
  children,
}: AsyncDataDisplayProps<T>) {
  if (isLoading) {
    return <LoadingState message={loadingMessage} />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={onRetry} />;
  }

  if (!data || isEmpty(data)) {
    return <EmptyState message={emptyMessage} icon={emptyIcon} />;
  }

  return <>{children(data)}</>;
}
