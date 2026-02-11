/**
 * Agent weight sliders component.
 * Allows users to set weights for fundamental, technical, and sentiment agents.
 * Weights must sum to 1.0.
 */

import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import type { StrategyWeights } from "@/types/strategy";
import { useEffect, useState } from "react";

interface AgentWeightSlidersProps {
  weights: StrategyWeights;
  onChange: (weights: StrategyWeights) => void;
}

export function AgentWeightSliders({
  weights,
  onChange,
}: AgentWeightSlidersProps) {
  const [localWeights, setLocalWeights] = useState(weights);

  useEffect(() => {
    setLocalWeights(weights);
  }, [weights]);

  const handleWeightChange = (agent: keyof StrategyWeights, value: number) => {
    const newWeight = value / 100; // Convert from 0-100 to 0-1

    // Calculate remaining weight to distribute
    const otherAgents = (
      Object.keys(localWeights) as Array<keyof StrategyWeights>
    ).filter((a) => a !== agent);
    const otherWeightsSum = otherAgents.reduce(
      (sum, a) => sum + localWeights[a],
      0
    );

    if (newWeight >= 1.0) {
      // If this agent takes all weight, set others to 0
      const updatedWeights: StrategyWeights = {
        fundamental: agent === "fundamental" ? 1.0 : 0,
        technical: agent === "technical" ? 1.0 : 0,
        sentiment: agent === "sentiment" ? 1.0 : 0,
      };
      setLocalWeights(updatedWeights);
      onChange(updatedWeights);
      return;
    }

    // Distribute remaining weight proportionally among other agents
    const remaining = 1.0 - newWeight;
    const updatedWeights = { ...localWeights, [agent]: newWeight };

    if (otherWeightsSum > 0) {
      otherAgents.forEach((otherAgent) => {
        const proportion = localWeights[otherAgent] / otherWeightsSum;
        updatedWeights[otherAgent] = remaining * proportion;
      });
    } else {
      // If other agents had 0 weight, distribute evenly
      const evenSplit = remaining / otherAgents.length;
      otherAgents.forEach((otherAgent) => {
        updatedWeights[otherAgent] = evenSplit;
      });
    }

    setLocalWeights(updatedWeights);
    onChange(updatedWeights);
  };

  const handleAdjustmentEnd = () => {
    setIsAdjusting(null);
  };

  const formatPercentage = (value: number) => `${(value * 100).toFixed(0)}%`;

  const sum =
    localWeights.fundamental + localWeights.technical + localWeights.sentiment;
  const isValid = sum >= 0.99 && sum <= 1.01;

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="fundamental-weight">Fundamental Analysis</Label>
          <span className="text-sm font-medium tabular-nums">
            {formatPercentage(localWeights.fundamental)}
          </span>
        </div>
        <Slider
          id="fundamental-weight"
          min={0}
          max={100}
          step={1}
          value={[localWeights.fundamental * 100]}
          onValueChange={([value]) => handleWeightChange("fundamental", value)}
          onValueCommit={handleAdjustmentEnd}
          className="cursor-pointer"
        />
        <p className="text-xs text-muted-foreground">
          Weight for fundamental analysis (revenue, earnings, valuation)
        </p>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="technical-weight">Technical Analysis</Label>
          <span className="text-sm font-medium tabular-nums">
            {formatPercentage(localWeights.technical)}
          </span>
        </div>
        <Slider
          id="technical-weight"
          min={0}
          max={100}
          step={1}
          value={[localWeights.technical * 100]}
          onValueChange={([value]) => handleWeightChange("technical", value)}
          onValueCommit={handleAdjustmentEnd}
          className="cursor-pointer"
        />
        <p className="text-xs text-muted-foreground">
          Weight for technical analysis (moving averages, RSI, trends)
        </p>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="sentiment-weight">Sentiment Analysis</Label>
          <span className="text-sm font-medium tabular-nums">
            {formatPercentage(localWeights.sentiment)}
          </span>
        </div>
        <Slider
          id="sentiment-weight"
          min={0}
          max={100}
          step={1}
          value={[localWeights.sentiment * 100]}
          onValueChange={([value]) => handleWeightChange("sentiment", value)}
          onValueCommit={handleAdjustmentEnd}
          className="cursor-pointer"
        />
        <p className="text-xs text-muted-foreground">
          Weight for sentiment analysis (price momentum, market sentiment)
        </p>
      </div>

      <div className="rounded-lg border p-3 bg-muted/50">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Total Weight:</span>
          <span
            className={`text-sm font-bold tabular-nums ${
              isValid ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
            }`}
          >
            {formatPercentage(sum)}
          </span>
        </div>
        {!isValid && (
          <p className="mt-1 text-xs text-red-600 dark:text-red-400">
            Weights must sum to 100%
          </p>
        )}
      </div>
    </div>
  );
}
