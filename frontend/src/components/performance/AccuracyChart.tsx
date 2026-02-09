import React, { useEffect, useState, useRef } from 'react';
import { createChart, IChartApi, ISeriesApi } from 'lightweight-charts';
import { TimelinePoint } from '@/types/performance';

const AccuracyChart: React.FC = () => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTimeline = async () => {
      try {
        const response = await fetch('/api/performance/timeline');
        if (!response.ok) {
          throw new Error('Failed to fetch performance timeline');
        }
        const data = await response.json();
        setTimeline(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchTimeline();
  }, []);

  useEffect(() => {
    if (loading || error || !chartContainerRef.current || timeline.length === 0) return;

    if (!chartRef.current) {
      chartRef.current = createChart(chartContainerRef.current, {
        width: chartContainerRef.current.clientWidth,
        height: 300,
        layout: {
          backgroundColor: '#1f2937',
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
      seriesRef.current = chartRef.current.addLineSeries({
        color: '#3b82f6',
      });
    }

    const chartData = timeline.map(point => ({
      time: new Date(point.date).getTime() / 1000,
      value: point.accuracy,
    }));

    seriesRef.current?.setData(chartData);
    chartRef.current?.timeScale().fitContent();

  }, [loading, error, timeline]);

  if (loading) {
    return (
      <div className="bg-gray-800 p-4 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Accuracy Over Time</h2>
        <p>Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800 p-4 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Accuracy Over Time</h2>
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 p-4 rounded-lg">
      <h2 className="text-lg font-semibold mb-2">Accuracy Over Time</h2>
      <div ref={chartContainerRef} />
    </div>
  );
};

export default AccuracyChart;