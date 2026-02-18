import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { LucideIcon } from 'lucide-react';
import { CheckCircle, XCircle, Clock, Bell, Power } from 'lucide-react';

type BadgeVariant = 'default' | 'secondary' | 'destructive' | 'outline';

interface StatusConfig {
  label: string;
  variant: BadgeVariant;
  className?: string;
  icon?: LucideIcon;
}

/**
 * Action status configurations (BUY/SELL/HOLD)
 */
const ACTION_CONFIGS: Record<string, StatusConfig> = {
  BUY: {
    label: 'BUY',
    variant: 'default',
    className: 'bg-green-600 hover:bg-green-700 text-white',
    icon: CheckCircle,
  },
  SELL: {
    label: 'SELL',
    variant: 'destructive',
    icon: XCircle,
  },
  HOLD: {
    label: 'HOLD',
    variant: 'secondary',
    className: 'bg-yellow-600 hover:bg-yellow-700 text-white',
    icon: Clock,
  },
};

/**
 * Alert status configurations
 */
const ALERT_CONFIGS: Record<string, StatusConfig> = {
  triggered: {
    label: 'Triggered',
    variant: 'default',
    className: 'bg-yellow-500 hover:bg-yellow-600 text-white',
    icon: Bell,
  },
  active: {
    label: 'Active',
    variant: 'default',
    className: 'bg-green-600 hover:bg-green-700 text-white',
    icon: Power,
  },
  paused: {
    label: 'Paused',
    variant: 'secondary',
  },
};

/**
 * Schedule status configurations
 */
const SCHEDULE_CONFIGS: Record<string, StatusConfig> = {
  active: {
    label: 'Active',
    variant: 'default',
    className: 'bg-green-600 hover:bg-green-700 text-white',
  },
  paused: {
    label: 'Paused',
    variant: 'secondary',
  },
};

type StatusBadgeSize = 'sm' | 'md' | 'lg';

const sizeClasses: Record<StatusBadgeSize, string> = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-0.5',
  lg: 'text-base px-3 py-1',
};

interface StatusBadgeProps {
  /** Badge type (determines config mapping) */
  type: 'action' | 'alert' | 'schedule' | 'generic';
  /** Status value */
  status: string;
  /** Badge size */
  size?: StatusBadgeSize;
  /** Custom class name */
  className?: string;
}

/**
 * Unified status badge component
 *
 * Standardizes badge display across the app for actions, alerts, schedules, etc.
 *
 * @example
 * ```tsx
 * <StatusBadge type="action" status="BUY" />
 * <StatusBadge type="alert" status={alert.triggered ? 'triggered' : 'paused'} />
 * <StatusBadge type="schedule" status={schedule.active ? 'active' : 'paused'} size="sm" />
 * ```
 */
export function StatusBadge({ type, status, size = 'md', className }: StatusBadgeProps) {
  const configs =
    type === 'action'
      ? ACTION_CONFIGS
      : type === 'alert'
        ? ALERT_CONFIGS
        : type === 'schedule'
          ? SCHEDULE_CONFIGS
          : {};

  const config = configs[status] || {
    label: status,
    variant: 'outline' as BadgeVariant,
  };

  const Icon = config.icon;

  return (
    <Badge
      variant={config.variant}
      className={cn(config.className, sizeClasses[size], className)}
    >
      {Icon && <Icon className="w-3 h-3 mr-1" />}
      {config.label}
    </Badge>
  );
}
