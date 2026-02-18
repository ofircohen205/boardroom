import { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';
import type { IChartApi, ISeriesApi, Time, LineData } from 'lightweight-charts';
import { useAPIClient } from '@/hooks/useAPIClient';
import { useFetch } from '@/hooks/useFetch';
import { AsyncDataDisplay } from '@/components/common';
import { TrendingUp } from 'lucide-react';

const AccuracyChart = () => {
  const apiClient = useAPIClient();
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Line', Time> | null>(null);

  const { data: timeline, isLoading, error } = useFetch(
    () => apiClient.performance.getTimeline(30),
    { dependencies: [apiClient] }
  );

  useEffect(() => {
    if (isLoading || error || !chartContainerRef.current || !timeline || timeline.length === 0) return;

    if (!chartRef.current) {
      chartRef.current = createChart(chartContainerRef.current, {
        width: chartContainerRef.current.clientWidth,
        height: 300,
        layout: {
          background: { color: '#1f2937' },
          textColor: '#d1d5db',
        },
        grid: {
          vertLines: {
            color: '#374151',
          },
          horzLines: {
            color: '#374151',
          },
        },
      });
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      seriesRef.current = chartRef.current.addSeries('Line' as any, {
        color: '#3b82f6',
      });
    }

    const chartData: LineData<Time>[] = timeline.map((point) => ({
      time: Math.floor(new Date(point.date).getTime() / 1000) as unknown as Time,
      value: point.accuracy,
    }));

    seriesRef.current?.setData(chartData);
    chartRef.current?.timeScale().fitContent();
  }, [isLoading, error, timeline]);

  return (
    <div className="bg-gray-800 p-4 rounded-lg">
      <h2 className="text-lg font-semibold mb-2">Accuracy Over Time</h2>

      <AsyncDataDisplay
        isLoading={isLoading}
        error={error}
        data={timeline}
        emptyMessage="No timeline data available yet"
        emptyIcon={TrendingUp}
        loadingMessage="Loading chart..."
      >
        {() => <div ref={chartContainerRef} />}
      </AsyncDataDisplay>
    </div>
  );
};

export default AccuracyChart;
