import { TickerInput } from "./TickerInput";
import { AgentPanel } from "./AgentPanel";
import { DecisionCard } from "./DecisionCard";
import { NewsFeed } from "./NewsFeed";
import { StockChart } from "./StockChart";
import { useWebSocket } from "../hooks/useWebSocket";

export function Dashboard() {
  const { state, analyze } = useWebSocket();

  const isLoading = state.activeAgents.size > 0;

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <header className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Boardroom</h1>
          <TickerInput onAnalyze={analyze} isLoading={isLoading} />
        </header>

        {state.ticker && (
          <>
            <div className="grid grid-cols-4 gap-4">
              <AgentPanel
                agent="fundamental"
                title="Fundamental"
                isActive={state.activeAgents.has("fundamental")}
                isCompleted={state.completedAgents.has("fundamental")}
                data={state.fundamental}
              />
              <AgentPanel
                agent="sentiment"
                title="Sentiment"
                isActive={state.activeAgents.has("sentiment")}
                isCompleted={state.completedAgents.has("sentiment")}
                data={state.sentiment}
              />
              <AgentPanel
                agent="technical"
                title="Technical"
                isActive={state.activeAgents.has("technical")}
                isCompleted={state.completedAgents.has("technical")}
                data={state.technical}
              />
              <AgentPanel
                agent="risk"
                title="Risk Manager"
                isActive={state.activeAgents.has("risk")}
                isCompleted={state.completedAgents.has("risk")}
                data={state.risk}
              />
            </div>

            <DecisionCard
              decision={state.decision}
              vetoed={state.vetoed}
              vetoReason={state.risk?.veto_reason}
            />

            <div className="grid grid-cols-2 gap-4">
              {state.technical?.price_history && (
                <StockChart
                  priceHistory={state.technical.price_history}
                  ticker={state.ticker}
                />
              )}
              {state.sentiment && (
                <NewsFeed
                  newsItems={state.sentiment.news_items}
                  socialMentions={state.sentiment.social_mentions}
                />
              )}
            </div>
          </>
        )}

        {state.error && (
          <div className="p-4 bg-red-100 text-red-700 rounded">{state.error}</div>
        )}
      </div>
    </div>
  );
}
