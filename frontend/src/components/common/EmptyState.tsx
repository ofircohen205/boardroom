import type { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  message: string;
  icon?: LucideIcon;
}

/**
 * Standardized empty state component
 */
export function EmptyState({ message, icon: Icon }: EmptyStateProps) {
  return (
    <div className="text-center py-12">
      {Icon && <Icon className="w-12 h-12 text-muted-foreground mx-auto mb-4" />}
      <p className="text-muted-foreground">{message}</p>
    </div>
  );
}
