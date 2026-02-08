import { Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import type { AgentType } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface Props {
  agent: AgentType;
  title: string;
  icon: React.ElementType;
  isActive: boolean;
  isCompleted: boolean;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any;
  index: number;
}

export function AgentPanel({
  agent,
  title,
  icon: Icon,
  isActive,
  isCompleted,
  data,
  index,
}: Props) {
  return (
    <Card
      className={cn(
        "glass transition-all duration-500 overflow-hidden relative group border-white/10",
        isActive && "border-primary/50 shadow-[0_0_40px_-10px] shadow-primary/30 bg-primary/5",
        isCompleted && "border-primary/30 bg-primary/5",
        !isActive && !isCompleted && !data && "opacity-40 grayscale hover:grayscale-0 hover:opacity-80 hover:bg-white/5",
      )}
      style={{ animationDelay: `${index * 100}ms` }}
    >
      {/* Active Indicator Line */}
      {isActive && (
        <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-primary to-transparent animate-shimmer" />
      )}

      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3 relative z-10">
        <CardTitle className="flex items-center gap-3 text-sm font-medium tracking-wide">
          <div
            className={cn(
              "flex h-9 w-9 items-center justify-center rounded-lg transition-colors border shadow-inner",
              isActive && "bg-primary/20 text-primary border-primary/30 animate-pulse-glow",
              isCompleted && "bg-primary/10 text-primary border-primary/20",
              !isActive && !isCompleted && "bg-white/5 text-muted-foreground border-white/10",
            )}
          >
            <Icon className="h-4 w-4" />
          </div>
          <span className={cn("transition-colors font-semibold", isActive ? "text-foreground" : "text-muted-foreground")}>
            {title}
          </span>
        </CardTitle>
        <div className="flex items-center gap-2">
          {isActive && (
            <Badge variant="outline" className="gap-1.5 border-primary/30 text-primary bg-primary/10 text-[10px] px-2 py-0.5 animate-pulse font-medium">
              <Loader2 className="h-3 w-3 animate-spin" />
              ANALYZING
            </Badge>
          )}
          {isCompleted && (
            <div className="rounded-full bg-success/20 p-1 ring-1 ring-success/30">
              <CheckCircle2 className="h-3.5 w-3.5 text-success" />
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="relative z-10">
        {/* Shimmer loading state */}
        {isActive && !data && (
          <div className="space-y-4 py-3">
            <div className="h-2 w-3/4 rounded-full bg-white/10 animate-pulse" />
            <div className="h-2 w-1/2 rounded-full bg-white/10 animate-pulse delay-75" />
            <div className="h-2 w-2/3 rounded-full bg-white/10 animate-pulse delay-150" />
          </div>
        )}

        {/* Data display */}
        {data && (
          <div className="animate-fade-up space-y-4">
            {/* Key metrics row */}
            <div className="grid grid-cols-3 gap-2 p-3 rounded-lg bg-black/20 border border-white/10 backdrop-blur-sm">
              {agent === "fundamental" && (
                <>
                  <Metric label="P/E Ratio" value={data.pe_ratio?.toFixed(1) ?? "N/A"} />
                  <Metric
                    label="Growth"
                    value={`${data.revenue_growth > 0 ? "+" : ""}${(data.revenue_growth * 100)?.toFixed(1)}%`}
                    positive={data.revenue_growth > 0}
                  />
                  <Metric label="Debt/Eq" value={data.debt_to_equity?.toFixed(2)} />
                </>
              )}
              {agent === "sentiment" && (
                <>
                  <Metric
                    label="Sentiment"
                    value={data.overall_sentiment?.toFixed(2)}
                    positive={data.overall_sentiment > 0.15}
                    negative={data.overall_sentiment < -0.15}
                    large
                  />
                  <div className="col-span-2 flex items-center justify-end">
                    <Badge
                      variant="outline"
                      className={cn(
                        "text-[10px] border-transparent font-medium",
                        data.overall_sentiment > 0
                          ? "bg-success/15 text-success border-success/20"
                          : "bg-destructive/15 text-destructive border-destructive/20",
                      )}
                    >
                      {data.overall_sentiment > 0 ? "Positive Outlook" : "Negative Outlook"}
                    </Badge>
                  </div>
                </>
              )}
              {agent === "technical" && (
                <>
                  <Metric label="Price" value={`$${data.current_price?.toFixed(2)}`} large />
                  <Metric
                    label="RSI"
                    value={data.rsi?.toFixed(1)}
                    warning={data.rsi > 70 || data.rsi < 30}
                  />
                  <div className="flex items-center justify-center">
                    <Badge
                      variant="outline"
                      className={cn(
                        "text-[10px] uppercase tracking-wider border-transparent font-medium",
                        data.trend === "bullish" && "bg-success/15 text-success border-success/20",
                        data.trend === "bearish" && "bg-destructive/15 text-destructive border-destructive/20",
                        data.trend === "neutral" && "bg-warning/15 text-warning border-warning/20",
                      )}
                    >
                      {data.trend}
                    </Badge>
                  </div>
                </>
              )}
              {agent === "risk" && (
                <>
                  <Metric
                    label="VaR (95%)"
                    value={data.var_95 ? `${(data.var_95 * 100).toFixed(1)}%` : "N/A"}
                  />
                   <div className="col-span-2 flex items-center justify-end">
                    <Badge
                      variant="outline"
                      className={cn(
                        "text-[10px] font-semibold border-transparent gap-1.5 px-2",
                        data.veto
                          ? "bg-destructive/15 text-destructive border-destructive/20"
                          : "bg-success/15 text-success border-success/20",
                      )}
                    >
                      {data.veto ? <AlertCircle className="w-3.5 h-3.5" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                      {data.veto ? "VETOED" : "APPROVED"}
                    </Badge>
                  </div>
                </>
              )}
            </div>

            {/* Summary - the AI analysis text */}
            {data.summary && (
              <div className="bg-white/5 rounded-lg p-3 border border-white/10 group-hover:bg-white/10 transition-colors">
                <p className="text-sm leading-relaxed text-gray-300 font-mono">
                  <span className="text-primary/70 mr-2">{">"}</span>
                  {data.summary}
                </p>
              </div>
            )}
            {agent === "risk" && data.veto_reason && (
              <div className="bg-destructive/10 rounded-lg p-3 border border-destructive/20">
                <p className="text-sm leading-relaxed text-destructive-foreground font-mono">
                  <span className="font-bold mr-2">[ALERT]</span>
                  {data.veto_reason}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Idle state */}
        {!isActive && !data && (
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground/30">
            <div className="w-10 h-10 rounded-full border border-dashed border-current flex items-center justify-center mb-2">
              <span className="text-xs font-mono">{index + 1}</span>
            </div>
            <p className="text-[10px] uppercase tracking-widest font-medium">Standing By</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function Metric({
  label,
  value,
  positive,
  negative,
  warning,
  large,
}: {
  label: string;
  value: string;
  positive?: boolean;
  negative?: boolean;
  warning?: boolean;
  large?: boolean;
}) {
  return (
    <div className="flex flex-col items-center justify-center text-center p-1.5">
      <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-1">
        {label}
      </p>
      <p
        className={cn(
          "font-mono font-medium tabular-nums tracking-tighter",
          large ? "text-xl" : "text-base",
          positive && "text-success",
          negative && "text-destructive",
          warning && "text-warning",
          !positive && !negative && !warning && "text-foreground",
        )}
      >
        {value}
      </p>
    </div>
  );
}
