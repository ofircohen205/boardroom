import { TickerInput } from "@/components/TickerInput";
import { AgentPanel } from "@/components/AgentPanel";
import { DecisionCard } from "@/components/DecisionCard";
import { NewsFeed } from "@/components/NewsFeed";
import { StockChart } from "@/components/StockChart";
import { AgentPipeline } from "@/components/AgentPipeline";
import { useWebSocket } from "@/hooks/useWebSocket";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  AlertCircle,
  BarChart3,
  MessageSquare,
  TrendingUp,
  Shield,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

export function Dashboard() {
  const { state, analyze } = useWebSocket();

  const isLoading = state.activeAgents.size > 0;
  const hasStarted = state.ticker !== null;

  return (
    <div className={cn(
      "min-h-screen transition-all duration-700 ease-in-out flex flex-col",
      hasStarted ? "justify-start pt-8" : "justify-center"
    )}>
      
      <div className="mx-auto w-full max-w-7xl px-6 relative z-10 text-center sm:text-left">
        {/* Header / Hero Section */}
        <header className={cn(
          "transition-all duration-700 ease-in-out flex flex-col gap-6",
          hasStarted 
            ? "flex-row items-center justify-between mb-8 opacity-100 translate-y-0" 
            : "items-center mb-12 scale-100"
        )}>
          <div className={cn("transition-all duration-700", hasStarted ? "" : "flex flex-col items-center")}>
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.3em] text-primary mb-3">
              <Zap className="w-3 h-3 fill-primary" />
              <span>AI Command Center</span>
            </div>
            <h1 className={cn(
              "font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-br from-white via-white/90 to-white/50",
              hasStarted ? "text-3xl" : "text-5xl sm:text-7xl mb-4"
            )}>
              The Boardroom
            </h1>
            {!hasStarted && (
               <p className="text-lg text-muted-foreground max-w-lg mx-auto leading-relaxed text-center">
                Orchestrate a team of autonomous AI agents to analyze market data, sentiment, and risk in real-time.
              </p>
            )}
          </div>
          
          <div className={cn(
             "transition-all duration-700 delay-100",
             !hasStarted && "w-full max-w-3xl scale-110 mt-8"
          )}>
            <TickerInput onAnalyze={analyze} isLoading={isLoading} />
          </div>
        </header>

        {/* Active Dashboard Content */}
        <div className={cn(
          "transition-all duration-1000 ease-out",
          hasStarted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-20 hidden"
        )}>
           <div className="space-y-8 pb-20">
            {/* Agent Progress Pipeline */}
            <div className="mb-8">
               <AgentPipeline
                activeAgents={state.activeAgents}
                completedAgents={state.completedAgents}
                hasDecision={state.decision !== null || state.vetoed}
              />
            </div>

            {/* Verdict & Figure Section - Only visible when finished */}
            {(state.decision !== null || state.vetoed) && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 animate-fade-up">
                  <div className="h-full">
                    <DecisionCard
                      decision={state.decision}
                      vetoed={state.vetoed}
                      vetoReason={state.risk?.veto_reason}
                    />
                  </div>
                  <div className="h-full glass rounded-3xl overflow-hidden p-1 min-h-[300px] border-white/5">
                    {state.technical?.price_history ? (
                        <StockChart
                          priceHistory={state.technical.price_history}
                          ticker={state.ticker!}
                        />
                    ) : (
                      <div className="h-full flex items-center justify-center text-muted-foreground/20 text-sm font-mono uppercase tracking-widest">
                        Market Data Unavailable
                      </div>
                    )}
                  </div>
              </div>
            )}

            {/* Agents Grid Section */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <AgentPanel
                  agent="fundamental"
                  title="Fundamental"
                  icon={BarChart3}
                  isActive={state.activeAgents.has("fundamental")}
                  isCompleted={state.completedAgents.has("fundamental")}
                  data={state.fundamental}
                  index={0}
                />
                <AgentPanel
                  agent="sentiment"
                  title="Sentiment"
                  icon={MessageSquare}
                  isActive={state.activeAgents.has("sentiment")}
                  isCompleted={state.completedAgents.has("sentiment")}
                  data={state.sentiment}
                  index={1}
                />
                <AgentPanel
                  agent="technical"
                  title="Technical"
                  icon={TrendingUp}
                  isActive={state.activeAgents.has("technical")}
                  isCompleted={state.completedAgents.has("technical")}
                  data={state.technical}
                  index={2}
                />
                <AgentPanel
                  agent="risk"
                  title="Risk"
                  icon={Shield}
                  isActive={state.activeAgents.has("risk")}
                  isCompleted={state.completedAgents.has("risk")}
                  data={state.risk}
                  index={3}
                />
            </div>

            {/* Bottom Row: News Feed (Full Width) */}
            {state.sentiment && (
              <div className="glass rounded-xl p-6">
                <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground mb-4 flex items-center gap-2">
                  <MessageSquare className="w-4 h-4" />
                  Market Intelligence
                </h3>
                <NewsFeed
                  newsItems={state.sentiment.news_items}
                  socialMentions={state.sentiment.social_mentions}
                />
              </div>
            )}
           </div>
        </div>

        {/* Error State */}
        {state.error && (
          <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 animate-fade-up">
            <Alert variant="destructive" className="bg-destructive/10 border-destructive/50 text-destructive shadow-2xl backdrop-blur-xl">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="font-semibold">{state.error}</AlertDescription>
            </Alert>
          </div>
        )}
      </div>
    </div>
  );
}
