/**
 * Strategy form component for creating/editing strategies.
 */

import { AgentWeightSliders } from "@/components/strategies/AgentWeightSliders";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { Strategy, StrategyConfig, StrategyCreate } from "@/types/strategy";
import { useState } from "react";

interface StrategyFormProps {
  strategy?: Strategy;
  onSubmit: (data: StrategyCreate) => void;
  onCancel?: () => void;
  isLoading?: boolean;
}

export function StrategyForm({
  strategy,
  onSubmit,
  onCancel,
  isLoading = false,
}: StrategyFormProps) {
  const [name, setName] = useState(strategy?.name || "");
  const [description, setDescription] = useState(strategy?.description || "");
  const [config, setConfig] = useState<StrategyConfig>(
    strategy?.config || {
      weights: { fundamental: 0.33, technical: 0.34, sentiment: 0.33 },
      thresholds: { buy: 70, sell: 30 },
      risk_params: { max_position_size: 0.5 },
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ name, description: description || undefined, config });
  };

  const isValid =
    name.trim().length > 0 &&
    config.weights.fundamental + config.weights.technical + config.weights.sentiment >= 0.99 &&
    config.weights.fundamental + config.weights.technical + config.weights.sentiment <= 1.01;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Info */}
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="strategy-name">Strategy Name *</Label>
          <Input
            id="strategy-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Balanced Growth Strategy"
            maxLength={100}
            required
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="strategy-description">Description</Label>
          <Textarea
            id="strategy-description"
            value={description}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setDescription(e.target.value)}
            placeholder="Optional description of your strategy..."
            maxLength={500}
            rows={3}
          />
        </div>
      </div>

      {/* Agent Weights */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold">Agent Weights</h3>
          <p className="text-sm text-muted-foreground">
            Configure how much weight each agent has in the final decision
          </p>
        </div>
        <AgentWeightSliders
          weights={config.weights}
          onChange={(weights) => setConfig({ ...config, weights })}
        />
      </div>

      {/* Decision Thresholds */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold">Decision Thresholds</h3>
          <p className="text-sm text-muted-foreground">
            Score thresholds for BUY and SELL decisions (0-100)
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="buy-threshold">Buy Threshold</Label>
            <Input
              id="buy-threshold"
              type="number"
              min={0}
              max={100}
              step={1}
              value={config.thresholds.buy}
              onChange={(e) =>
                setConfig({
                  ...config,
                  thresholds: { ...config.thresholds, buy: Number(e.target.value) },
                })
              }
            />
            <p className="text-xs text-muted-foreground">
              Minimum score to trigger BUY
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="sell-threshold">Sell Threshold</Label>
            <Input
              id="sell-threshold"
              type="number"
              min={0}
              max={100}
              step={1}
              value={config.thresholds.sell}
              onChange={(e) =>
                setConfig({
                  ...config,
                  thresholds: { ...config.thresholds, sell: Number(e.target.value) },
                })
              }
            />
            <p className="text-xs text-muted-foreground">
              Maximum score to trigger SELL
            </p>
          </div>
        </div>
      </div>

      {/* Risk Parameters */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold">Risk Management</h3>
          <p className="text-sm text-muted-foreground">
            Optional risk parameters for position sizing and stop losses
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="space-y-2">
            <Label htmlFor="position-size">Max Position Size</Label>
            <Input
              id="position-size"
              type="number"
              min={0}
              max={1}
              step={0.1}
              value={config.risk_params.max_position_size}
              onChange={(e) =>
                setConfig({
                  ...config,
                  risk_params: {
                    ...config.risk_params,
                    max_position_size: Number(e.target.value),
                  },
                })
              }
            />
            <p className="text-xs text-muted-foreground">
              % of capital (0.5 = 50%)
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="stop-loss">Stop Loss %</Label>
            <Input
              id="stop-loss"
              type="number"
              min={0}
              max={1}
              step={0.01}
              value={config.risk_params.stop_loss || ""}
              onChange={(e) =>
                setConfig({
                  ...config,
                  risk_params: {
                    ...config.risk_params,
                    stop_loss: e.target.value ? Number(e.target.value) : undefined,
                  },
                })
              }
              placeholder="Optional"
            />
            <p className="text-xs text-muted-foreground">
              e.g., 0.1 = 10%
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="take-profit">Take Profit %</Label>
            <Input
              id="take-profit"
              type="number"
              min={0}
              step={0.01}
              value={config.risk_params.take_profit || ""}
              onChange={(e) =>
                setConfig({
                  ...config,
                  risk_params: {
                    ...config.risk_params,
                    take_profit: e.target.value ? Number(e.target.value) : undefined,
                  },
                })
              }
              placeholder="Optional"
            />
            <p className="text-xs text-muted-foreground">
              e.g., 0.2 = 20%
            </p>
          </div>
        </div>
      </div>

      {/* Form Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button type="submit" disabled={!isValid || isLoading}>
          {isLoading ? "Saving..." : strategy ? "Update Strategy" : "Create Strategy"}
        </Button>
      </div>
    </form>
  );
}
