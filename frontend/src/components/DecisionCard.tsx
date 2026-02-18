import type { Decision } from '@/types';
import { useAPIClient } from '@/contexts/APIContext';
import { useFetch } from '@/hooks/useFetch';
import { useCopyToClipboard } from '@/hooks/useCopyToClipboard';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertTriangle, ArrowUpCircle, ArrowDownCircle, MinusCircle, Copy, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Props {
  decision: Decision | null;
  vetoed: boolean;
  vetoReason?: string | null;
}

const actionConfig = {
  BUY: {
    icon: ArrowUpCircle,
    label: 'Buy',
    color: 'text-success',
    accent: 'oklch(0.72 0.20 155)',
    bg: 'from-success/20 to-success/5',
    border: 'border-success/30',
    shadow: 'shadow-success/20',
  },
  SELL: {
    icon: ArrowDownCircle,
    label: 'Sell',
    color: 'text-destructive',
    accent: 'oklch(0.65 0.24 20)',
    bg: 'from-destructive/20 to-destructive/5',
    border: 'border-destructive/30',
    shadow: 'shadow-destructive/20',
  },
  HOLD: {
    icon: MinusCircle,
    label: 'Hold',
    color: 'text-warning',
    accent: 'oklch(0.82 0.17 80)',
    bg: 'from-warning/20 to-warning/5',
    border: 'border-warning/30',
    shadow: 'shadow-warning/20',
  },
} as const;

export function DecisionCard({ decision, vetoed, vetoReason }: Props) {
  const apiClient = useAPIClient();
  const { copy, copied } = useCopyToClipboard();

  // Fetch chairperson performance
  const { data: performance } = useFetch(
    () => apiClient.performance.getAgentStats('chairperson'),
    {
      immediate: !!decision,
      dependencies: [apiClient, decision],
    }
  );

  const handleCopy = () => {
    if (!decision) return;
    const text = `
Decision: ${decision.action} (${Math.round(decision.confidence * 100)}% confidence)
${decision.rationale ? `\nRationale: ${decision.rationale}` : ''}
    `.trim();
    copy(text);
  };

  if (vetoed) {
    return (
      <Card className="glass animate-fade-up border-destructive/40 bg-gradient-to-br from-destructive/10 to-transparent overflow-hidden relative">
        <div className="absolute inset-0 bg-destructive/5 animate-pulse-glow" style={{ animationDuration: '3s' }} />
        <CardContent className="flex items-center gap-6 p-8 relative z-10">
          <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full border-2 border-destructive/30 bg-destructive/10">
            <AlertTriangle className="h-8 w-8 text-destructive animate-pulse" />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-destructive mb-2">
              Risk Protocol Activated
            </p>
            <h2 className="text-3xl font-black text-white tracking-tight mb-2">Trade Vetoed</h2>
            {vetoReason && (
              <p className="text-sm font-mono text-destructive-foreground/80 leading-relaxed border-l-2 border-destructive/30 pl-3">
                {vetoReason}
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!decision) return null;

  const config = actionConfig[decision.action];
  const Icon = config.icon;
  const confidence = Math.round(decision.confidence * 100);
  const trackRecord = performance?.[0]?.accuracy; // Overall accuracy for chairperson

  return (
    <Card
      className={cn(
        'animate-fade-up overflow-hidden border transition-all duration-500',
        config.border,
        `shadow-2xl ${config.shadow}`,
        'bg-white/5 backdrop-blur-md'
      )}
    >
      <div className={cn('bg-gradient-to-br', config.bg, 'p-8 relative')}>
        {/* Copy Button */}
        <Button
          variant="ghost"
          size="icon"
          onClick={handleCopy}
          className="absolute top-2 right-2 opacity-60 hover:opacity-100"
          title="Copy decision to clipboard"
        >
          {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
        </Button>

        <div className="flex flex-col gap-8 sm:flex-row sm:items-center justify-between">
          {/* Main Verdict */}
          <div className="flex items-center gap-6">
            <div
              className={cn(
                'flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl border-2 shadow-inner',
                config.border,
                'bg-white/5 backdrop-blur-sm'
              )}
            >
              <Icon className={cn('h-10 w-10', config.color)} />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground mb-1">Final Verdict</p>
              <div className="flex items-baseline gap-4">
                <span className={cn('text-5xl font-black tracking-tighter drop-shadow-lg', config.color)}>
                  {decision.action}
                </span>
                <div className="flex flex-col">
                  <span className="text-2xl font-bold tabular-nums text-white">{confidence}%</span>
                  <span className="text-[10px] uppercase text-muted-foreground font-medium">Confidence</span>
                </div>
              </div>
            </div>
          </div>

          {/* Confidence Meter */}
          <div className="flex-1 sm:max-w-xs w-full bg-black/20 rounded-xl p-4 border border-white/5">
            <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
              <span className="uppercase tracking-wider font-semibold">Consensus Strength</span>
            </div>
            <div className="h-3 w-full overflow-hidden rounded-full bg-black/40 shadow-inner">
              <div
                className={cn(
                  'h-full rounded-full transition-all duration-1000 ease-out shadow-[0_0_10px_currentColor]',
                  config.color
                )}
                style={{
                  width: `${confidence}%`,
                  backgroundColor: config.accent,
                }}
              />
            </div>
            <div className="flex justify-between mt-2 text-[10px] text-muted-foreground/50 font-mono">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>
        </div>

        {/* Rationale Section */}
        {decision.rationale && (
          <div className="mt-8 pt-6 border-t border-white/10">
            <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-2">Analysis Summary</p>
            <p className="text-base text-foreground/90 leading-relaxed font-light">{decision.rationale}</p>
          </div>
        )}

        {trackRecord !== undefined && (
          <div className="mt-4 text-xs text-center text-muted-foreground">
            Chairperson's overall accuracy: {(trackRecord * 100).toFixed(0)}%
          </div>
        )}
      </div>
    </Card>
  );
}
