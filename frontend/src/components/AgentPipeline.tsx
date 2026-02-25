import {
  BarChart3,
  MessageSquare,
  TrendingUp,
  Shield,
  Gavel,
  Check,
  Loader2,
} from "lucide-react";
import { type ElementType } from "react";
import type { AgentType } from "@/types";
import { cn } from "@/lib/utils";

interface Props {
  activeAgents: Set<AgentType>;
  completedAgents: Set<AgentType>;
  hasDecision: boolean;
}

const PHASE_1 = [
  { key: "fundamental" as AgentType, icon: BarChart3, label: "Fundamental" },
  { key: "sentiment" as AgentType, icon: MessageSquare, label: "Sentiment" },
  { key: "technical" as AgentType, icon: TrendingUp, label: "Technical" },
] as const;

const PHASE_2 = [
  { key: "risk" as AgentType, icon: Shield, label: "Risk" },
] as const;

function AgentNode({
  icon: Icon,
  label,
  isActive,
  isComplete,
}: {
  icon: ElementType;
  label: string;
  isActive: boolean;
  isComplete: boolean;
}) {
  return (
    <div className="flex flex-col items-center gap-3 min-w-[72px] relative z-10">
      <div
        className={cn(
          "relative flex h-12 w-12 items-center justify-center rounded-2xl transition-all duration-500 border-2 shadow-lg",
          isComplete && "bg-primary text-primary-foreground border-primary shadow-[0_0_25px_rgba(var(--primary),0.6)] scale-105",
          isActive && "bg-primary/20 text-primary border-primary animate-pulse-glow shadow-[0_0_20px_rgba(var(--primary),0.4)]",
          !isComplete && !isActive && "bg-muted/30 text-muted-foreground border-border",
        )}
      >
        {isComplete ? (
          <Check className="h-6 w-6" />
        ) : isActive ? (
          <Loader2 className="h-6 w-6 animate-spin" />
        ) : (
          <Icon className="h-5 w-5" />
        )}
      </div>
      <span
        className={cn(
          "hidden text-[10px] font-bold tracking-[0.2em] uppercase transition-colors sm:block",
          isComplete ? "text-primary text-glow" : isActive ? "text-foreground" : "text-muted-foreground/60",
        )}
      >
        {label}
      </span>
    </div>
  );
}

function ConnectingLine({ filled }: { filled: boolean }) {
  return (
    <div className="flex-1 h-[2px] bg-muted-foreground/20 relative overflow-hidden rounded-full mx-2 self-start mt-6">
      <div
        className={cn(
          "absolute inset-0 transition-all duration-1000 w-full origin-left bg-gradient-to-r from-primary to-primary/50",
          filled ? "scale-x-100" : "scale-x-0",
        )}
      />
    </div>
  );
}

export function AgentPipeline({ activeAgents, completedAgents, hasDecision }: Props) {
  const allPhase1Complete =
    completedAgents.has("fundamental") &&
    completedAgents.has("sentiment") &&
    completedAgents.has("technical");

  return (
    <div className="glass rounded-2xl px-8 py-6 border-border bg-card/80 backdrop-blur-xl space-y-4">

      {/* Phase 1 */}
      <div className="flex items-start gap-4">
        <div className="flex flex-col items-start gap-0.5 min-w-[72px] pt-1">
          <span className="text-[9px] font-black tracking-[0.25em] uppercase text-primary/70">Phase 1</span>
          <span className="text-[9px] tracking-wider uppercase text-muted-foreground/40">Parallel</span>
        </div>

        <div className="flex items-start flex-1">
          {PHASE_1.map((step, i) => (
            <div key={step.key} className="flex items-start flex-1">
              <AgentNode
                icon={step.icon}
                label={step.label}
                isActive={activeAgents.has(step.key)}
                isComplete={completedAgents.has(step.key)}
              />
              {i < PHASE_1.length - 1 && (
                <ConnectingLine filled={completedAgents.has(step.key)} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Phase 2 — appears after Phase 1 completes */}
      {allPhase1Complete && (
        <div className="flex items-start gap-4 animate-fade-up">
          <div className="flex flex-col items-start gap-0.5 min-w-[72px] pt-1">
            <span className="text-[9px] font-black tracking-[0.25em] uppercase text-primary/70">Phase 2</span>
            <span className="text-[9px] tracking-wider uppercase text-muted-foreground/40">Sequential</span>
          </div>

          <div className="flex items-start flex-1">
            {PHASE_2.map((step) => (
              <div key={step.key} className="flex items-start flex-1">
                <AgentNode
                  icon={step.icon}
                  label={step.label}
                  isActive={activeAgents.has(step.key)}
                  isComplete={completedAgents.has(step.key)}
                />
                <ConnectingLine filled={completedAgents.has(step.key)} />
              </div>
            ))}

            {/* Decision node */}
            <div className="flex flex-col items-center gap-3 min-w-[72px] relative z-10">
              <div
                className={cn(
                  "relative flex h-12 w-12 items-center justify-center rounded-2xl transition-all duration-500 border-2 shadow-lg",
                  hasDecision && "bg-emerald-500 text-white border-emerald-500 shadow-[0_0_30px_rgba(16,185,129,0.6)] scale-110",
                  !hasDecision && "bg-muted/30 text-muted-foreground border-border",
                )}
              >
                <Gavel className={cn("h-5 w-5", !hasDecision && "opacity-40")} />
              </div>
              <span
                className={cn(
                  "hidden text-[10px] font-bold tracking-[0.2em] uppercase transition-colors sm:block",
                  hasDecision ? "text-emerald-500" : "text-muted-foreground/60",
                )}
              >
                Decision
              </span>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
