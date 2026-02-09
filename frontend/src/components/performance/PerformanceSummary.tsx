import React, { useEffect, useState } from 'react';
import { PerformanceSummary as PerformanceSummaryType } from '@/types/performance';

const PerformanceSummary: React.FC = () => {
  const [summary, setSummary] = useState<PerformanceSummaryType | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const response = await fetch('/api/performance/summary');
        if (!response.ok) {
          throw new Error('Failed to fetch performance summary');
        }
        const data = await response.json();
        setSummary(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, []);

  if (loading) {
    return (
      <div className="bg-gray-800 p-4 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Performance Summary</h2>
        <p>Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800 p-4 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Performance Summary</h2>
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  if (!summary) {
    return null;
  }

  return (
    <div className="bg-gray-800 p-4 rounded-lg">
      <h2 className="text-lg font-semibold mb-2">Performance Summary</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <p className="text-sm text-gray-400">Total Analyses</p>
          <p className="text-2xl font-bold">{summary.total_analyses}</p>
        </div>
        <div>
          <p className="text-sm text-gray-400">Tracked Outcomes</p>
          <p className="text-2xl font-bold">{summary.tracked_outcomes}</p>
        </div>
        <div>
          <p className="text-sm text-gray-400">7-Day Accuracy</p>
          <p className="text-2xl font-bold">{(summary.accuracy_7d * 100).toFixed(1)}%</p>
        </div>
        <div>
          <p className="text-sm text-gray-400">30-Day Accuracy</p>
          <p className="text-2xl font-bold">{(summary.accuracy_30d * 100).toFixed(1)}%</p>
        </div>
      </div>
    </div>
  );
};

export default PerformanceSummary;
