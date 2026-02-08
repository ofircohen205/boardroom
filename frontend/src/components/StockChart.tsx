import { useEffect, useRef } from "react";
import {
  createChart,
  AreaSeries,
  type IChartApi,
  ColorType,
} from "lightweight-charts";
import type { PricePoint } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp } from "lucide-react";

interface Props {
  priceHistory: PricePoint[];
  ticker: string;
}

export function StockChart({ priceHistory, ticker }: Props) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current || priceHistory.length === 0) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 300,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#a1a1aa", // muted-foreground
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { color: "rgba(255, 255, 255, 0.05)" },
      },
      crosshair: {
        vertLine: {
          color: "rgba(255, 255, 255, 0.2)",
          labelBackgroundColor: "#5b21b6", // primary dark
        },
        horzLine: {
          color: "rgba(255, 255, 255, 0.2)",
          labelBackgroundColor: "#5b21b6",
        },
      },
      rightPriceScale: {
        borderVisible: false,
        scaleMargins: {
          top: 0.2,
          bottom: 0.1,
        },
      },
      timeScale: {
        borderVisible: false,
        timeVisible: true,
      },
      handleScroll: false,
      handleScale: false,
    });

    const areaSeries = chart.addSeries(AreaSeries, {
      lineColor: "#8b5cf6", // bright violet/primary
      lineWidth: 2,
      topColor: "rgba(139, 92, 246, 0.4)", // primary with opacity
      bottomColor: "rgba(139, 92, 246, 0.0)",
      crosshairMarkerBackgroundColor: "#8b5cf6",
      crosshairMarkerBorderColor: "#ffffff",
      crosshairMarkerRadius: 4,
    });

    areaSeries.setData(
      priceHistory.map((p) => ({
        time: p.date.split("T")[0],
        value: p.close,
      }))
    );

    chart.timeScale().fitContent();
    chartRef.current = chart;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        chart.applyOptions({ width: entry.contentRect.width });
      }
    });
    resizeObserver.observe(chartContainerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
    };
  }, [priceHistory]);

  if (priceHistory.length === 0) return null;

  // Compute price change
  const firstPrice = priceHistory[0]?.close;
  const lastPrice = priceHistory[priceHistory.length - 1]?.close;
  const change = firstPrice ? ((lastPrice - firstPrice) / firstPrice) * 100 : 0;
  const isPositive = change >= 0;

  return (
    <Card className="glass animate-fade-up overflow-hidden border-primary/20">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 border-b border-white/5 bg-white/5">
        <CardTitle className="flex items-center gap-2 text-sm font-bold tracking-widest uppercase text-muted-foreground">
          <TrendingUp className="h-4 w-4 text-primary" />
          {ticker} Price Action
        </CardTitle>
        <div className="flex items-baseline gap-3 text-sm">
          <span className="font-mono text-lg font-bold tracking-tight text-foreground">
            ${lastPrice?.toFixed(2)}
          </span>
          <span
            className={`font-mono text-xs font-bold px-1.5 py-0.5 rounded ${
              isPositive 
                ? "bg-emerald-500/20 text-emerald-400" 
                : "bg-rose-500/20 text-rose-400"
            }`}
          >
            {isPositive ? "+" : ""}
            {change.toFixed(2)}%
          </span>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div ref={chartContainerRef} className="w-full" />
      </CardContent>
    </Card>
  );
}
