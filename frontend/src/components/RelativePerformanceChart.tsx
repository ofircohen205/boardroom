import { useEffect, useRef } from "react";
import {
  createChart,
  type IChartApi,
  type ISeriesApi,
  type LineData,
} from "lightweight-charts";

interface PriceHistory {
  time: string;
  close: number;
}

interface RelativePerformanceChartProps {
  data: Record<string, PriceHistory[]>;
  className?: string;
}

const CHART_COLORS = [
  "#3b82f6", // blue
  "#10b981", // green
  "#f59e0b", // amber
  "#ef4444", // red
  "#8b5cf6", // purple
  "#ec4899", // pink
];

export function RelativePerformanceChart({
  data,
  className = "",
}: RelativePerformanceChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<Map<string, ISeriesApi<"Line">>>(new Map());

  useEffect(() => {
    if (!chartContainerRef.current || Object.keys(data).length === 0) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: "transparent" },
        textColor: "#94a3b8",
      },
      grid: {
        vertLines: { color: "rgba(255, 255, 255, 0.05)" },
        horzLines: { color: "rgba(255, 255, 255, 0.05)" },
      },
      rightPriceScale: {
        borderColor: "rgba(255, 255, 255, 0.1)",
      },
      timeScale: {
        borderColor: "rgba(255, 255, 255, 0.1)",
        timeVisible: true,
      },
      crosshair: {
        vertLine: {
          color: "rgba(255, 255, 255, 0.3)",
          labelBackgroundColor: "#1e293b",
        },
        horzLine: {
          color: "rgba(255, 255, 255, 0.3)",
          labelBackgroundColor: "#1e293b",
        },
      },
    });

    chartRef.current = chart;

    // Normalize all series to start at 100
    const normalizedData: Record<string, LineData[]> = {};
    const tickers = Object.keys(data);

    for (const ticker of tickers) {
      const history = data[ticker];
      if (history.length === 0) continue;

      const basePrice = history[0].close;
      normalizedData[ticker] = history.map((point) => ({
        time: new Date(point.time).getTime() / 1000 as any,
        value: (point.close / basePrice) * 100,
      }));
    }

    // Create line series for each ticker
    tickers.forEach((ticker, index) => {
      const color = CHART_COLORS[index % CHART_COLORS.length];
      const lineSeries = chart.addSeries("Line", {
        color,
        lineWidth: 2,
        title: ticker,
        priceLineVisible: false,
        lastValueVisible: true,
      });

      lineSeries.setData(normalizedData[ticker]);
      seriesRef.current.set(ticker, lineSeries);
    });

    // Fit content
    chart.timeScale().fitContent();

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };

    window.addEventListener("resize", handleResize);
    handleResize();

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      seriesRef.current.clear();
    };
  }, [data]);

  return (
    <div className={className}>
      {/* Legend */}
      <div className="flex flex-wrap gap-4 mb-4 px-2">
        {Object.keys(data).map((ticker, index) => (
          <div key={ticker} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{
                backgroundColor: CHART_COLORS[index % CHART_COLORS.length],
              }}
            />
            <span className="text-sm font-mono font-medium">{ticker}</span>
          </div>
        ))}
      </div>

      {/* Chart */}
      <div
        ref={chartContainerRef}
        className="w-full h-[400px] rounded-lg bg-gradient-to-br from-white/[0.02] to-white/[0.01] border border-white/5"
      />

      {/* Note */}
      <div className="mt-2 text-xs text-muted-foreground text-center">
        Normalized to 100 at start of period
      </div>
    </div>
  );
}
