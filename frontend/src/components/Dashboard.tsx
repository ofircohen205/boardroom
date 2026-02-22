import { useState, useRef } from "react";
import { TickerInput } from "@/components/TickerInput";
import { AgentPanel } from "@/components/AgentPanel";
import { DecisionCard } from "@/components/DecisionCard";
import { NewsFeed } from "@/components/NewsFeed";
import { StockChart } from "@/components/StockChart";
import { AgentPipeline } from "@/components/AgentPipeline";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import { WatchlistSidebar } from "@/components/WatchlistSidebar";
import { AnalysisHistory } from "@/components/AnalysisHistory";
import { ShortcutsModal } from "@/components/ShortcutsModal";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import type { AnalysisMode } from "@/components/PresetSelector";
import {
  AlertCircle,
  BarChart3,
  MessageSquare,
  TrendingUp,
  Shield,
  Zap,
  History,
  Menu,
  GitCompare,
  Keyboard,
} from "lucide-react";
import { cn } from "@/lib/utils";

export function Dashboard() {
  const { state, analyze, retry, connectionStatus } = useWebSocket();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(
    () => typeof window !== "undefined" && window.innerWidth >= 768
  );
  const [showHistory, setShowHistory] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>("standard");
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Keyboard shortcuts
  useKeyboardShortcuts({
    'Ctrl+k': () => searchInputRef.current?.focus(),
    'Ctrl+h': () => setShowHistory((v) => !v),
    'Ctrl+b': () => setSidebarOpen((v) => !v),
    'Escape': () => { setShowHistory(false); setShowShortcuts(false); },
    '?': () => setShowShortcuts(true),
  });

  const isLoading = state.activeAgents.size > 0;
  const hasStarted = state.ticker !== null;

  const handleTickerSelect = (ticker: string) => {
      analyze(ticker, "US", analysisMode);
      setShowHistory(false);
  };

  const handleAnalyze = (ticker: string, market: "US" | "TASE") => {
      analyze(ticker, market, analysisMode);
      setShowHistory(false);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Overlay backdrop on mobile when sidebar is open */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-[60] md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar - overlay on mobile, inline on desktop */}
      <div className={cn(
          "transition-all duration-300 border-r border-white/10 bg-card/10 backdrop-blur-xl",
          "fixed md:relative z-[70] md:z-auto h-full",
          sidebarOpen
            ? "w-80 translate-x-0"
            : "-translate-x-full md:w-0 md:overflow-hidden md:translate-x-0"
      )}>
          <WatchlistSidebar onSelectTicker={handleTickerSelect} />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">

        {/* Minimal Header - just sidebar toggle and history */}
        <header className="h-14 border-b border-white/10 bg-card/30 backdrop-blur-md px-4 flex items-center justify-between z-20 shrink-0">
            <div className="flex items-center gap-4">
                <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(!sidebarOpen)}>
                    <Menu className="w-4 h-4" />
                </Button>
                <div className="flex items-center gap-2">
                    <Zap className="w-5 h-5 text-primary fill-primary" />
                    <span className="font-bold tracking-tight hidden sm:inline-block">Dashboard</span>
                </div>
            </div>

            <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" onClick={() => setShowHistory(!showHistory)} className={cn("gap-2", showHistory && "bg-accent")}>
                    <History className="w-4 h-4"/> <span className="hidden sm:inline">History</span>
                </Button>

                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setShowShortcuts(true)}
                  title="Keyboard shortcuts (?)"
                >
                  <Keyboard className="w-4 h-4" />
                </Button>

                {/* Connection Status Indicator */}
                {connectionStatus === "reconnecting" && (
                  <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-yellow-500/10 border border-yellow-500/20">
                    <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse"></div>
                    <span className="text-xs text-yellow-600 dark:text-yellow-400 font-medium hidden sm:inline">Reconnecting...</span>
                  </div>
                )}
                {connectionStatus === "connecting" && (
                  <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-blue-500/10 border border-blue-500/20">
                    <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div>
                    <span className="text-xs text-blue-600 dark:text-blue-400 font-medium hidden sm:inline">Connecting...</span>
                  </div>
                )}
            </div>
        </header>

        {/* Scrollable Main Area */}
        <main className="flex-1 overflow-auto p-6 relative">

            {showHistory ? (
                 <div className="max-w-5xl mx-auto h-[calc(100vh-140px)]">
                    <AnalysisHistory ticker={state.ticker || undefined} />
                 </div>
            ) : (
                <div className={cn(
                    "min-h-full transition-all duration-700 ease-in-out flex flex-col",
                    hasStarted ? "justify-start" : "justify-center"
                )}>
                    {/* Hero / Search */}
                    <div className={cn(
                        "mx-auto w-full max-w-4xl transition-all duration-700 ease-in-out",
                        hasStarted ? "mb-8" : "mb-0 text-center"
                    )}>
                        {!hasStarted && (
                             <div className="mb-10 space-y-4 px-4">
                                <h1 className="text-5xl sm:text-7xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-br from-white via-white/90 to-white/50 animate-fade-up">
                                    The Boardroom
                                </h1>
                                <p className="text-muted-foreground text-lg max-w-2xl mx-auto leading-relaxed animate-fade-up delay-100">
                                    Orchestrate a team of autonomous AI agents to analyze market data, sentiment, and risk in real-time.
                                </p>
                             </div>
                        )}

                        <div className={cn("transition-all duration-500 delay-200", hasStarted ? "" : "scale-110")}>
                            <TickerInput
                                onAnalyze={handleAnalyze}
                                isLoading={isLoading}
                                analysisMode={analysisMode}
                                onModeChange={setAnalysisMode}
                            />
                        </div>
                    </div>

                    {/* Active Analysis View */}
                    <div className={cn(
                        "transition-all duration-1000 ease-out max-w-7xl mx-auto w-full space-y-8 pb-20",
                        hasStarted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-20 hidden"
                    )}>
                        {/* Pipeline Progress */}
                        <AgentPipeline
                            activeAgents={state.activeAgents}
                            completedAgents={state.completedAgents}
                            hasDecision={state.decision !== null || state.vetoed}
                        />

                        {/* Results Area */}
                        {(state.decision !== null || state.vetoed) && (
                           <div className="space-y-4 animate-fade-up">
                               {/* Quick Actions */}
                               <div className="flex justify-end">
                                   <Button
                                       variant="outline"
                                       size="sm"
                                       onClick={() => navigate(`/compare?ticker=${state.ticker}`)}
                                       className="gap-2"
                                   >
                                       <GitCompare className="w-4 h-4"/>
                                       Compare with others
                                   </Button>
                               </div>

                               <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
                                           ma50={state.technical.ma_50}
                                           ma200={state.technical.ma_200}
                                           rsi={state.technical.rsi}
                                       />
                                   ) : (
                                       <div className="h-full flex items-center justify-center text-muted-foreground/20 text-sm font-mono uppercase tracking-widest">
                                           Market Data Unavailable
                                       </div>
                                   )}
                               </div>
                           </div>
                           </div>
                        )}

                        {/* Agents Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 min-w-0">
                            <AgentPanel
                                agent="fundamental"
                                title="Fundamental"
                                icon={BarChart3}
                                isActive={state.activeAgents.has("fundamental")}
                                isCompleted={state.completedAgents.has("fundamental")}
                                isFailed={state.failedAgents.has("fundamental")}
                                errorMessage={state.failedAgents.get("fundamental")}
                                data={state.fundamental}
                                index={0}
                                onRetry={retry}
                            />
                            <AgentPanel
                                agent="sentiment"
                                title="Sentiment"
                                icon={MessageSquare}
                                isActive={state.activeAgents.has("sentiment")}
                                isCompleted={state.completedAgents.has("sentiment")}
                                isFailed={state.failedAgents.has("sentiment")}
                                errorMessage={state.failedAgents.get("sentiment")}
                                data={state.sentiment}
                                index={1}
                                onRetry={retry}
                            />
                            <AgentPanel
                                agent="technical"
                                title="Technical"
                                icon={TrendingUp}
                                isActive={state.activeAgents.has("technical")}
                                isCompleted={state.completedAgents.has("technical")}
                                isFailed={state.failedAgents.has("technical")}
                                errorMessage={state.failedAgents.get("technical")}
                                data={state.technical}
                                index={2}
                                onRetry={retry}
                            />
                            <AgentPanel
                                agent="risk"
                                title="Risk"
                                icon={Shield}
                                isActive={state.activeAgents.has("risk")}
                                isCompleted={state.completedAgents.has("risk")}
                                isFailed={state.failedAgents.has("risk")}
                                errorMessage={state.failedAgents.get("risk")}
                                data={state.risk}
                                index={3}
                                onRetry={retry}
                            />
                        </div>

                         {/* News Feed */}
                         {state.sentiment && (
                            <div className="glass rounded-xl p-6 mb-8">
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
            )}
        </main>

        {/* Error Alert */}
        {state.error && (
            <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 animate-fade-up">
                <Alert variant="destructive" className="bg-destructive/10 border-destructive/50 text-destructive shadow-2xl backdrop-blur-xl">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription className="font-semibold">{state.error}</AlertDescription>
                </Alert>
            </div>
        )}

        <ShortcutsModal open={showShortcuts} onClose={() => setShowShortcuts(false)} />
      </div>
    </div>
  );
}
