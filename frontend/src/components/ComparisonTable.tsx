import { TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface StockData {
  ticker: string;
  fundamental?: {
    pe_ratio: number;
    revenue_growth: number;
    debt_to_equity: number;
    market_cap: number;
  };
  sentiment?: {
    sentiment_score: number;
  };
  technical?: {
    rsi: number;
    signal: string;
  };
  decision?: {
    action: string;
    confidence: number;
  };
}

interface ComparisonTableProps {
  data: Record<string, StockData>;
  className?: string;
}

interface MetricRow {
  label: string;
  getValue: (stock: StockData) => number | string | null;
  format: (value: number | string | null) => string;
  higherIsBetter?: boolean;
}

const METRICS: MetricRow[] = [
  {
    label: "P/E Ratio",
    getValue: (s) => s.fundamental?.pe_ratio ?? null,
    format: (v) => (v !== null && typeof v === "number" ? v.toFixed(2) : "-"),
    higherIsBetter: false, // Lower P/E is generally better
  },
  {
    label: "Revenue Growth",
    getValue: (s) => s.fundamental?.revenue_growth ?? null,
    format: (v) =>
      v !== null && typeof v === "number" ? `${(v * 100).toFixed(1)}%` : "-",
    higherIsBetter: true,
  },
  {
    label: "Debt/Equity",
    getValue: (s) => s.fundamental?.debt_to_equity ?? null,
    format: (v) => (v !== null && typeof v === "number" ? v.toFixed(2) : "-"),
    higherIsBetter: false,
  },
  {
    label: "Market Cap",
    getValue: (s) => s.fundamental?.market_cap ?? null,
    format: (v) => {
      if (v === null || typeof v !== "number") return "-";
      if (v >= 1e12) return `$${(v / 1e12).toFixed(2)}T`;
      if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`;
      if (v >= 1e6) return `$${(v / 1e6).toFixed(2)}M`;
      return `$${v.toFixed(0)}`;
    },
    higherIsBetter: undefined, // Neutral
  },
  {
    label: "Sentiment Score",
    getValue: (s) => s.sentiment?.sentiment_score ?? null,
    format: (v) => (v !== null && typeof v === "number" ? v.toFixed(0) : "-"),
    higherIsBetter: true,
  },
  {
    label: "RSI",
    getValue: (s) => s.technical?.rsi ?? null,
    format: (v) => (v !== null && typeof v === "number" ? v.toFixed(1) : "-"),
    higherIsBetter: undefined, // Optimal is middle range (30-70)
  },
  {
    label: "Technical Signal",
    getValue: (s) => s.technical?.signal ?? null,
    format: (v) => (v !== null ? String(v).toUpperCase() : "-"),
    higherIsBetter: undefined,
  },
  {
    label: "Recommendation",
    getValue: (s) => s.decision?.action ?? null,
    format: (v) => (v !== null ? String(v).toUpperCase() : "-"),
    higherIsBetter: undefined,
  },
  {
    label: "Confidence",
    getValue: (s) => s.decision?.confidence ?? null,
    format: (v) =>
      v !== null && typeof v === "number" ? `${(v * 100).toFixed(0)}%` : "-",
    higherIsBetter: true,
  },
];

function findBestValue(
  values: (number | string | null)[],
  higherIsBetter?: boolean
): number | null {
  if (higherIsBetter === undefined) return null;

  const numericValues = values
    .map((v, idx) => ({ value: typeof v === "number" ? v : null, idx }))
    .filter((v) => v.value !== null) as { value: number; idx: number }[];

  if (numericValues.length === 0) return null;

  if (higherIsBetter) {
    return numericValues.reduce((best, curr) =>
      curr.value > best.value ? curr : best
    ).idx;
  } else {
    return numericValues.reduce((best, curr) =>
      curr.value < best.value ? curr : best
    ).idx;
  }
}

export function ComparisonTable({ data, className = "" }: ComparisonTableProps) {
  const tickers = Object.keys(data);

  if (tickers.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        No data available
      </div>
    );
  }

  return (
    <div className={cn("overflow-x-auto", className)}>
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b border-white/10">
            <th className="text-left py-3 px-4 text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Metric
            </th>
            {tickers.map((ticker) => (
              <th
                key={ticker}
                className="text-center py-3 px-4 text-sm font-bold font-mono"
              >
                {ticker}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {METRICS.map((metric, metricIdx) => {
            const values = tickers.map((ticker) =>
              metric.getValue(data[ticker])
            );
            const bestIdx = findBestValue(values, metric.higherIsBetter);

            return (
              <tr
                key={metricIdx}
                className="border-b border-white/5 hover:bg-white/[0.02] transition-colors"
              >
                <td className="py-3 px-4 text-sm text-muted-foreground font-medium">
                  {metric.label}
                </td>
                {tickers.map((ticker, tickerIdx) => {
                  const value = values[tickerIdx];
                  const formattedValue = metric.format(value);
                  const isBest = bestIdx === tickerIdx;

                  return (
                    <td
                      key={ticker}
                      className={cn(
                        "py-3 px-4 text-center text-sm font-mono font-medium transition-all",
                        isBest &&
                          "bg-primary/10 text-primary font-bold relative"
                      )}
                    >
                      <div className="flex items-center justify-center gap-1">
                        {formattedValue}
                        {isBest && metric.higherIsBetter !== undefined && (
                          <span className="text-primary">
                            {metric.higherIsBetter ? (
                              <TrendingUp className="w-3 h-3" />
                            ) : (
                              <TrendingDown className="w-3 h-3" />
                            )}
                          </span>
                        )}
                      </div>
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
