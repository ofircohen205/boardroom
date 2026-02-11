/**
 * Backtest page for running and viewing backtests.
 */

import { BacktestForm } from "@/components/backtest/BacktestForm";
import { BacktestSummary } from "@/components/backtest/BacktestSummary";
import { TradeLog } from "@/components/backtest/TradeLog";
import { PageContainer } from "@/components/layout/PageContainer";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import type { BacktestConfig, BacktestProgress, BacktestResult } from "@/types/backtest";
import type { Strategy } from "@/types/strategy";
import { AlertCircle, BarChart3, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

export function BacktestPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [isLoadingStrategies, setIsLoadingStrategies] = useState(true);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [progress, setProgress] = useState<BacktestProgress>({
    status: "idle",
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStrategies();
  }, []);

  const fetchStrategies = async () => {
    try {
      setIsLoadingStrategies(true);
      const token = localStorage.getItem("token");
      const response = await fetch("http://localhost:8000/api/strategies", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStrategies(data);
      }
    } catch (error) {
      console.error("Failed to fetch strategies:", error);
    } finally {
      setIsLoadingStrategies(false);
    }
  };

  const runBacktest = (config: BacktestConfig) => {
    setResult(null);
    setError(null);
    setProgress({ status: "fetching_data", message: "Connecting..." });

    const token = localStorage.getItem("token");
    const websocket = new WebSocket(
      `ws://localhost:8000/ws/backtest?token=${token}`
    );

    websocket.onopen = () => {
      console.log("WebSocket connected");
      websocket.send(JSON.stringify(config));
    };

    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log("WebSocket message:", message);

      switch (message.type) {
        case "backtest_started":
          setProgress({
            status: "fetching_data",
            message: `Starting backtest for ${message.data.ticker}...`,
          });
          break;

        case "backtest_progress":
          setProgress({
            status: message.data.status || "running_backtest",
            message: message.data.message,
            progress_pct: message.data.progress_pct,
          });
          break;

        case "backtest_completed":
          setResult(message.data);
          setProgress({ status: "completed" });
          websocket.close();
          break;

        case "backtest_error":
          setError(message.data.error);
          setProgress({ status: "error" });
          websocket.close();
          break;
      }
    };

    websocket.onerror = (error) => {
      console.error("WebSocket error:", error);
      setError("Connection error. Please try again.");
      setProgress({ status: "error" });
    };

    websocket.onclose = () => {
      console.log("WebSocket closed");
    };
  };

  return (
    <PageContainer>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">Backtest</h1>
          <p className="text-muted-foreground">
            Test your trading strategies on historical data
          </p>
        </div>

        {/* Configuration Form */}
        <Card>
          <CardHeader>
            <CardTitle>Backtest Configuration</CardTitle>
            <CardDescription>
              Configure your backtest parameters and run historical simulations
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingStrategies ? (
              <div className="text-center py-8">
                <Loader2 className="mx-auto h-8 w-8 animate-spin text-muted-foreground" />
                <p className="mt-2 text-sm text-muted-foreground">
                  Loading strategies...
                </p>
              </div>
            ) : strategies.length === 0 ? (
              <div className="text-center py-8">
                <BarChart3 className="mx-auto h-12 w-12 text-muted-foreground" />
                <p className="mt-2 text-sm text-muted-foreground">
                  No strategies found. Create a strategy first to run backtests.
                </p>
              </div>
            ) : (
              <BacktestForm
                strategies={strategies}
                onSubmit={runBacktest}
                isLoading={progress.status !== "idle" && progress.status !== "completed" && progress.status !== "error"}
              />
            )}
          </CardContent>
        </Card>

        {/* Progress */}
        {(progress.status === "fetching_data" || progress.status === "running_backtest") && (
          <Card>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <p className="text-sm font-medium">{progress.message}</p>
                </div>
                {progress.progress_pct !== undefined && (
                  <Progress value={progress.progress_pct} className="w-full" />
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Error */}
        {error && (
          <Card className="border-red-600 dark:border-red-400">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
                <div>
                  <p className="font-medium text-red-600 dark:text-red-400">
                    Backtest Error
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">{error}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-6">
            {/* Summary Metrics */}
            <div>
              <h2 className="text-2xl font-bold mb-4">Results</h2>
              <BacktestSummary result={result} />
            </div>

            {/* Trade Log */}
            <Card>
              <CardHeader>
                <CardTitle>Trade Log</CardTitle>
                <CardDescription>
                  All trades executed during the backtest
                </CardDescription>
              </CardHeader>
              <CardContent>
                <TradeLog trades={result.trades} />
              </CardContent>
            </Card>

            {/* Execution Time */}
            {result.execution_time_seconds && (
              <p className="text-sm text-muted-foreground text-center">
                Backtest completed in {result.execution_time_seconds.toFixed(2)} seconds
              </p>
            )}
          </div>
        )}
      </div>
    </PageContainer>
  );
}
