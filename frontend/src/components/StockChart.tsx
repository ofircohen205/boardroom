import { useEffect, useRef, useState } from "react";
import {
  createChart,
  AreaSeries,
  CandlestickSeries,
  LineSeries,
  HistogramSeries,
  type IChartApi,
  type ISeriesApi,
  ColorType,
} from "lightweight-charts";
import type { PricePoint } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TrendingUp, CandlestickChart, AreaChart } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  priceHistory: PricePoint[];
  ticker: string;
  ma50?: number;
  ma200?: number;
  rsi?: number;
}

type ChartType = "area" | "candlestick";

export function StockChart({ priceHistory, ticker, ma50, ma200, rsi }: Props) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const volumeChartRef = useRef<HTMLDivElement>(null);
  const rsiChartRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const volumeChartInstanceRef = useRef<IChartApi | null>(null);
  const rsiChartInstanceRef = useRef<IChartApi | null>(null);
  const [chartType, setChartType] = useState<ChartType>("candlestick");

  useEffect(() => {
    if (!chartContainerRef.current || priceHistory.length === 0) return;

    // Main chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 300,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#a1a1aa",
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
          labelBackgroundColor: "#5b21b6",
        },
        horzLine: {
          color: "rgba(255, 255, 255, 0.2)",
          labelBackgroundColor: "#5b21b6",
        },
      },
      rightPriceScale: {
        borderVisible: false,
        scaleMargins: {
          top: 0.1,
          bottom: 0.2,
        },
      },
      timeScale: {
        borderVisible: false,
        timeVisible: true,
      },
      handleScroll: true,
      handleScale: true,
    });

    let priceSeries: ISeriesApi<"Area"> | ISeriesApi<"Candlestick">;

    if (chartType === "candlestick") {
      priceSeries = chart.addSeries(CandlestickSeries, {
        upColor: "#10b981",
        downColor: "#ef4444",
        borderUpColor: "#10b981",
        borderDownColor: "#ef4444",
        wickUpColor: "#10b981",
        wickDownColor: "#ef4444",
      });

      priceSeries.setData(
        priceHistory.map((p) => ({
          time: p.date.split("T")[0],
          open: p.open,
          high: p.high,
          low: p.low,
          close: p.close,
        }))
      );
    } else {
      priceSeries = chart.addSeries(AreaSeries, {
        lineColor: "#8b5cf6",
        lineWidth: 2,
        topColor: "rgba(139, 92, 246, 0.4)",
        bottomColor: "rgba(139, 92, 246, 0.0)",
        crosshairMarkerBackgroundColor: "#8b5cf6",
        crosshairMarkerBorderColor: "#ffffff",
        crosshairMarkerRadius: 4,
      });

      priceSeries.setData(
        priceHistory.map((p) => ({
          time: p.date.split("T")[0],
          value: p.close,
        }))
      );
    }

    // MA50 overlay
    if (ma50 && ma50 > 0) {
      const ma50Series = chart.addSeries(LineSeries, {
        color: "#fbbf24",
        lineWidth: 1,
        crosshairMarkerVisible: false,
        lastValueVisible: false,
        priceLineVisible: false,
      });
      ma50Series.setData(
        priceHistory.map((p) => ({
          time: p.date.split("T")[0],
          value: ma50,
        }))
      );
    }

    // MA200 overlay
    if (ma200 && ma200 > 0) {
      const ma200Series = chart.addSeries(LineSeries, {
        color: "#3b82f6",
        lineWidth: 1,
        crosshairMarkerVisible: false,
        lastValueVisible: false,
        priceLineVisible: false,
      });
      ma200Series.setData(
        priceHistory.map((p) => ({
          time: p.date.split("T")[0],
          value: ma200,
        }))
      );
    }

    chart.timeScale().fitContent();
    chartRef.current = chart;

    // Volume chart
    if (volumeChartRef.current) {
      const volumeChart = createChart(volumeChartRef.current, {
        width: volumeChartRef.current.clientWidth,
        height: 80,
        layout: {
          background: { type: ColorType.Solid, color: "transparent" },
          textColor: "#a1a1aa",
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 10,
        },
        grid: {
          vertLines: { visible: false },
          horzLines: { visible: false },
        },
        crosshair: {
          vertLine: {
            visible: false,
          },
          horzLine: {
            visible: false,
          },
        },
        rightPriceScale: {
          borderVisible: false,
          scaleMargins: {
            top: 0.1,
            bottom: 0.1,
          },
        },
        timeScale: {
          borderVisible: false,
          visible: false,
        },
        handleScroll: false,
        handleScale: false,
      });

      const volumeSeries = volumeChart.addSeries(HistogramSeries, {
        color: "#8b5cf6",
        priceFormat: {
          type: "volume",
        },
      });

      volumeSeries.setData(
        priceHistory.map((p) => ({
          time: p.date.split("T")[0],
          value: p.volume,
          color: p.close >= p.open ? "#10b98180" : "#ef444480",
        }))
      );

      volumeChart.timeScale().fitContent();
      volumeChartInstanceRef.current = volumeChart;

      // Sync time scales
      chart.timeScale().subscribeVisibleTimeRangeChange((timeRange) => {
        if (timeRange) {
          volumeChart.timeScale().setVisibleRange(timeRange);
        }
      });
    }

    // RSI chart
    if (rsiChartRef.current && rsi !== undefined) {
      const rsiChart = createChart(rsiChartRef.current, {
        width: rsiChartRef.current.clientWidth,
        height: 80,
        layout: {
          background: { type: ColorType.Solid, color: "transparent" },
          textColor: "#a1a1aa",
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 10,
        },
        grid: {
          vertLines: { visible: false },
          horzLines: { color: "rgba(255, 255, 255, 0.05)" },
        },
        crosshair: {
          vertLine: {
            visible: false,
          },
          horzLine: {
            visible: false,
          },
        },
        rightPriceScale: {
          borderVisible: false,
          scaleMargins: {
            top: 0.1,
            bottom: 0.1,
          },
        },
        timeScale: {
          borderVisible: false,
          visible: false,
        },
        handleScroll: false,
        handleScale: false,
      });

      const rsiSeries = rsiChart.addSeries(LineSeries, {
        color: "#8b5cf6",
        lineWidth: 2,
      });

      // Use current RSI for all points (simplified - in production would calculate RSI for each point)
      rsiSeries.setData(
        priceHistory.map((p) => ({
          time: p.date.split("T")[0],
          value: rsi,
        }))
      );

      // Add overbought/oversold lines
      const overboughtLine = rsiChart.addSeries(LineSeries, {
        color: "#ef444460",
        lineWidth: 1,
        lineStyle: 2, // dashed
        lastValueVisible: false,
        priceLineVisible: false,
      });
      overboughtLine.setData(
        priceHistory.map((p) => ({
          time: p.date.split("T")[0],
          value: 70,
        }))
      );

      const oversoldLine = rsiChart.addSeries(LineSeries, {
        color: "#10b98160",
        lineWidth: 1,
        lineStyle: 2,
        lastValueVisible: false,
        priceLineVisible: false,
      });
      oversoldLine.setData(
        priceHistory.map((p) => ({
          time: p.date.split("T")[0],
          value: 30,
        }))
      );

      rsiChart.timeScale().fitContent();
      rsiChartInstanceRef.current = rsiChart;

      // Sync time scales
      chart.timeScale().subscribeVisibleTimeRangeChange((timeRange) => {
        if (timeRange) {
          rsiChart.timeScale().setVisibleRange(timeRange);
        }
      });
    }

    // Resize observer
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const width = entry.contentRect.width;
        chart.applyOptions({ width });
        volumeChartInstanceRef.current?.applyOptions({ width });
        rsiChartInstanceRef.current?.applyOptions({ width });
      }
    });
    resizeObserver.observe(chartContainerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      volumeChartInstanceRef.current?.remove();
      rsiChartInstanceRef.current?.remove();
    };
  }, [priceHistory, chartType, ma50, ma200, rsi]);

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
        <div className="flex items-center gap-3">
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
          <div className="flex gap-1 border-l border-white/10 pl-3">
            <Button
              variant="ghost"
              size="icon"
              className={cn(
                "h-7 w-7",
                chartType === "candlestick" && "bg-primary/20 text-primary"
              )}
              onClick={() => setChartType("candlestick")}
              title="Candlestick Chart"
            >
              <CandlestickChart className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className={cn(
                "h-7 w-7",
                chartType === "area" && "bg-primary/20 text-primary"
              )}
              onClick={() => setChartType("area")}
              title="Area Chart"
            >
              <AreaChart className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0 space-y-0">
        {/* Main price chart */}
        <div ref={chartContainerRef} className="w-full" />

        {/* Volume chart */}
        <div className="border-t border-white/5 bg-white/[0.02]">
          <div className="px-3 py-1">
            <p className="text-[9px] uppercase tracking-widest text-muted-foreground font-bold">
              Volume
            </p>
          </div>
          <div ref={volumeChartRef} className="w-full" />
        </div>

        {/* RSI chart */}
        {rsi !== undefined && (
          <div className="border-t border-white/5 bg-white/[0.02]">
            <div className="px-3 py-1 flex items-center justify-between">
              <p className="text-[9px] uppercase tracking-widest text-muted-foreground font-bold">
                RSI
              </p>
              <span
                className={cn(
                  "text-[10px] font-mono font-bold",
                  rsi > 70 && "text-destructive",
                  rsi < 30 && "text-success",
                  rsi >= 30 && rsi <= 70 && "text-muted-foreground"
                )}
              >
                {rsi.toFixed(1)}
              </span>
            </div>
            <div ref={rsiChartRef} className="w-full" />
          </div>
        )}

        {/* Legend */}
        {(ma50 || ma200) && (
          <div className="px-4 py-2 border-t border-white/5 flex gap-4 text-[10px] font-mono">
            {ma50 && ma50 > 0 && (
              <div className="flex items-center gap-1.5">
                <div className="h-[2px] w-3 bg-[#fbbf24]" />
                <span className="text-muted-foreground">MA50: ${ma50.toFixed(2)}</span>
              </div>
            )}
            {ma200 && ma200 > 0 && (
              <div className="flex items-center gap-1.5">
                <div className="h-[2px] w-3 bg-[#3b82f6]" />
                <span className="text-muted-foreground">MA200: ${ma200.toFixed(2)}</span>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
