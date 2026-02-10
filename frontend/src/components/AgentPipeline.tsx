import {
  BarChart3,
  MessageSquare,
  TrendingUp,
  Shield,
  Gavel,
  Check,
  Loader2,
} from "lucide-react";
import type { AgentType } from "@/types";
import { cn } from "@/lib/utils";

interface Props {
  activeAgents: Set<AgentType>;
  completedAgents: Set<AgentType>;
  hasDecision: boolean;
}

const steps = [
  { key: "fundamental" as AgentType, icon: BarChart3, label: "Fundamental" },
  { key: "sentiment" as AgentType, icon: MessageSquare, label: "Sentiment" },
  { key: "technical" as AgentType, icon: TrendingUp, label: "Technical" },
  { key: "risk" as AgentType, icon: Shield, label: "Risk" },
] as const;

export function AgentPipeline({ activeAgents, completedAgents, hasDecision }: Props) {
  return (
    <div className="glass flex items-center justify-between rounded-2xl px-10 py-8 border-white/10 bg-black/40 backdrop-blur-xl">
      {steps.map((step) => {
        const isActive = activeAgents.has(step.key);
        const isComplete = completedAgents.has(step.key);

        return (
          <div key={step.key} className="flex items-center gap-4 flex-1 relative">
            <div className="flex flex-col items-center gap-4 relative z-10 group min-w-[80px]">
              <div
                className={cn(
                  "relative flex h-14 w-14 items-center justify-center rounded-2xl transition-all duration-500 border-2 shadow-lg",
                  isComplete && "bg-primary text-primary-foreground border-primary shadow-[0_0_25px_rgba(var(--primary),0.6)] scale-105",
                  isActive && "bg-primary/20 text-primary border-primary animate-pulse-glow shadow-[0_0_20px_rgba(var(--primary),0.4)]",
                  !isComplete && !isActive && "bg-white/5 text-muted-foreground border-white/10 group-hover:bg-white/10 group-hover:border-white/20 hover:scale-105",
                )}
              >
                {isComplete ? (
                  <Check className="h-7 w-7" />
                ) : isActive ? (
                  <Loader2 className="h-7 w-7 animate-spin" />
                ) : (
                  <step.icon className="h-6 w-6" />
                )}
              </div>
              <span
                className={cn(
                  "hidden text-[10px] font-bold tracking-[0.2em] uppercase transition-colors sm:block",
                  isComplete ? "text-primary text-glow" : isActive ? "text-foreground" : "text-muted-foreground/60",
                )}
              >
                {step.label}
              </span>
            </div>

            {/* Connecting Line */}
            <div className="flex-1 h-[2px] bg-white/10 relative overflow-hidden rounded-full mx-2">
               <div
                  className={cn(
                    "absolute inset-0 transition-all duration-1000 w-full origin-left bg-gradient-to-r from-primary to-primary/50",
                    isComplete || isActive ? "scale-x-100" : "scale-x-0"
                  )}
                />
            </div>
          </div>
        );
      })}

      {/* Final Decision step */}
      <div className="flex flex-col items-center gap-4 relative z-10 min-w-[80px]">
        <div
          className={cn(
            "relative flex h-14 w-14 items-center justify-center rounded-2xl transition-all duration-500 border-2 shadow-lg",
            hasDecision && "bg-emerald-500 text-white border-emerald-500 shadow-[0_0_30px_rgba(16,185,129,0.6)] scale-110",
            !hasDecision && "bg-white/5 text-muted-foreground border-white/10",
          )}
        >
          {hasDecision ? (
            <Gavel className="h-7 w-7" />
          ) : (
            <Gavel className="h-6 w-6 opacity-40" />
          )}
        </div>
        <span
          className={cn(
            "hidden text-[10px] font-bold tracking-[0.2em] uppercase transition-colors sm:block",
            hasDecision ? "text-emerald-500 text-shadow-glow" : "text-muted-foreground/60",
          )}
        >
          Decision
        </span>
      </div>
    </div>
  );
}
