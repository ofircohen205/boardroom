/**
 * Backtest summary metrics component.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { BacktestResult } from "@/types/backtest";
import {
  ArrowDownIcon,
  ArrowUpIcon,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

interface BacktestSummaryProps {
  result: BacktestResult;
}

export function BacktestSummary({ result }: BacktestSummaryProps) {
  const formatPercent = (value: number) => {
    const formatted = (value * 100).toFixed(2);
    return `${value >= 0 ? "+" : ""}${formatted}%`;
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(value);
  };

  const metrics = [
    {
      title: "Total Return",
      value: formatPercent(result.total_return),
      subtitle: `vs Buy & Hold: ${formatPercent(result.buy_and_hold_return)}`,
      trend: result.total_return > 0 ? "up" : "down",
      highlight: true,
    },
    {
      title: "Annualized Return",
      value: formatPercent(result.annualized_return),
      subtitle: "Yearly equivalent",
      trend: result.annualized_return > 0 ? "up" : "down",
    },
    {
      title: "Sharpe Ratio",
      value: result.sharpe_ratio?.toFixed(2) || "N/A",
      subtitle: "Risk-adjusted return",
      trend: result.sharpe_ratio && result.sharpe_ratio > 1 ? "up" : "neutral",
    },
    {
      title: "Max Drawdown",
      value: formatPercent(result.max_drawdown),
      subtitle: "Largest peak-to-trough decline",
      trend: "down",
    },
    {
      title: "Win Rate",
      value: formatPercent(result.win_rate),
      subtitle: `${result.total_trades} total trades`,
      trend: result.win_rate > 0.5 ? "up" : "down",
    },
    {
      title: "Final Equity",
      value: formatCurrency(result.initial_capital * (1 + result.total_return)),
      subtitle: `Initial: ${formatCurrency(result.initial_capital)}`,
      trend: result.total_return > 0 ? "up" : "down",
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {metrics.map((metric, index) => (
        <Card key={index} className={metric.highlight ? "border-primary" : ""}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{metric.title}</CardTitle>
            {metric.trend === "up" && (
              <TrendingUp className="h-4 w-4 text-green-600 dark:text-green-400" />
            )}
            {metric.trend === "down" && (
              <TrendingDown className="h-4 w-4 text-red-600 dark:text-red-400" />
            )}
          </CardHeader>
          <CardContent>
            <div
              className={`text-2xl font-bold tabular-nums ${
                metric.trend === "up"
                  ? "text-green-600 dark:text-green-400"
                  : metric.trend === "down"
                    ? "text-red-600 dark:text-red-400"
                    : ""
              }`}
            >
              {metric.value}
            </div>
            <p className="text-xs text-muted-foreground mt-1">{metric.subtitle}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
