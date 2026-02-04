import { useEffect, useRef } from "react";
import { createChart, LineSeries, type IChartApi } from "lightweight-charts";
import type { PricePoint } from "../types";

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
      layout: { textColor: "#333" },
      grid: { vertLines: { color: "#eee" }, horzLines: { color: "#eee" } },
    });

    const lineSeries = chart.addSeries(LineSeries, { color: "#2563eb" });
    lineSeries.setData(
      priceHistory.map((p) => ({
        time: p.date.split("T")[0],
        value: p.close,
      }))
    );

    chartRef.current = chart;

    return () => {
      chart.remove();
    };
  }, [priceHistory]);

  if (priceHistory.length === 0) return null;

  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <h3 className="font-semibold mb-2">{ticker} Price Chart</h3>
      <div ref={chartContainerRef} />
    </div>
  );
}
