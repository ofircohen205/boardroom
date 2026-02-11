/**
 * Backtest configuration form component.
 */

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { BacktestConfig } from "@/types/backtest";
import type { Strategy } from "@/types/strategy";
import { useState } from "react";

interface BacktestFormProps {
  strategies: Strategy[];
  onSubmit: (config: BacktestConfig) => void;
  isLoading?: boolean;
}

export function BacktestForm({ strategies, onSubmit, isLoading = false }: BacktestFormProps) {
  const [config, setConfig] = useState<BacktestConfig>({
    ticker: "",
    strategy_id: "",
    start_date: "2023-01-01",
    end_date: "2023-12-31",
    initial_capital: 10000,
    check_frequency: "daily",
    position_size_pct: 0.5,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(config);
  };

  const isValid =
    config.ticker.trim().length > 0 &&
    config.strategy_id.length > 0 &&
    config.start_date.length > 0 &&
    config.end_date.length > 0 &&
    config.initial_capital > 0;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        {/* Ticker */}
        <div className="space-y-2">
          <Label htmlFor="ticker">Stock Ticker *</Label>
          <Input
            id="ticker"
            value={config.ticker}
            onChange={(e) =>
              setConfig({ ...config, ticker: e.target.value.toUpperCase() })
            }
            placeholder="e.g., AAPL"
            maxLength={10}
            required
          />
        </div>

        {/* Strategy */}
        <div className="space-y-2">
          <Label htmlFor="strategy">Strategy *</Label>
          <Select
            value={config.strategy_id}
            onValueChange={(value) => setConfig({ ...config, strategy_id: value })}
          >
            <SelectTrigger id="strategy">
              <SelectValue placeholder="Select a strategy" />
            </SelectTrigger>
            <SelectContent>
              {strategies.map((strategy) => (
                <SelectItem key={strategy.id} value={strategy.id}>
                  {strategy.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Start Date */}
        <div className="space-y-2">
          <Label htmlFor="start-date">Start Date *</Label>
          <Input
            id="start-date"
            type="date"
            value={config.start_date}
            onChange={(e) => setConfig({ ...config, start_date: e.target.value })}
            required
          />
        </div>

        {/* End Date */}
        <div className="space-y-2">
          <Label htmlFor="end-date">End Date *</Label>
          <Input
            id="end-date"
            type="date"
            value={config.end_date}
            onChange={(e) => setConfig({ ...config, end_date: e.target.value })}
            required
          />
        </div>

        {/* Initial Capital */}
        <div className="space-y-2">
          <Label htmlFor="initial-capital">Initial Capital ($)</Label>
          <Input
            id="initial-capital"
            type="number"
            min={100}
            step={100}
            value={config.initial_capital}
            onChange={(e) =>
              setConfig({ ...config, initial_capital: Number(e.target.value) })
            }
            required
          />
        </div>

        {/* Frequency */}
        <div className="space-y-2">
          <Label htmlFor="frequency">Check Frequency</Label>
          <Select
            value={config.check_frequency}
            onValueChange={(value: "daily" | "weekly") =>
              setConfig({ ...config, check_frequency: value })
            }
          >
            <SelectTrigger id="frequency">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="daily">Daily</SelectItem>
              <SelectItem value="weekly">Weekly</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Position Size */}
        <div className="space-y-2">
          <Label htmlFor="position-size">Position Size (%)</Label>
          <Input
            id="position-size"
            type="number"
            min={0.1}
            max={1}
            step={0.1}
            value={config.position_size_pct}
            onChange={(e) =>
              setConfig({ ...config, position_size_pct: Number(e.target.value) })
            }
            required
          />
          <p className="text-xs text-muted-foreground">
            Percentage of capital to use per trade (0.5 = 50%)
          </p>
        </div>

        {/* Stop Loss */}
        <div className="space-y-2">
          <Label htmlFor="stop-loss">Stop Loss (%)</Label>
          <Input
            id="stop-loss"
            type="number"
            min={0}
            max={1}
            step={0.01}
            value={config.stop_loss_pct || ""}
            onChange={(e) =>
              setConfig({
                ...config,
                stop_loss_pct: e.target.value ? Number(e.target.value) : undefined,
              })
            }
            placeholder="Optional (e.g., 0.1 for 10%)"
          />
        </div>

        {/* Take Profit */}
        <div className="space-y-2">
          <Label htmlFor="take-profit">Take Profit (%)</Label>
          <Input
            id="take-profit"
            type="number"
            min={0}
            step={0.01}
            value={config.take_profit_pct || ""}
            onChange={(e) =>
              setConfig({
                ...config,
                take_profit_pct: e.target.value ? Number(e.target.value) : undefined,
              })
            }
            placeholder="Optional (e.g., 0.2 for 20%)"
          />
        </div>
      </div>

      <Button type="submit" disabled={!isValid || isLoading} className="w-full">
        {isLoading ? "Running Backtest..." : "Run Backtest"}
      </Button>
    </form>
  );
}
