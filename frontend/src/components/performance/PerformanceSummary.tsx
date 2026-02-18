import { useAPIClient } from '@/hooks/useAPIClient';
import { useFetch } from '@/hooks/useFetch';
import { AsyncDataDisplay } from '@/components/common';
import { BarChart3 } from 'lucide-react';

const PerformanceSummary = () => {
  const apiClient = useAPIClient();

  const { data: summary, isLoading, error } = useFetch(
    () => apiClient.performance.getSummary(),
    { dependencies: [apiClient] }
  );

  return (
    <div className="bg-card p-4 rounded-lg">
      <h2 className="text-lg font-semibold mb-2">Performance Summary</h2>

      <AsyncDataDisplay
        isLoading={isLoading}
        error={error}
        data={summary}
        isEmpty={() => false}
        emptyMessage="No performance data available"
        emptyIcon={BarChart3}
        loadingMessage="Loading summary..."
      >
        {(summary) => (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Total Analyses</p>
              <p className="text-2xl font-bold">{summary.total_analyses}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Tracked Outcomes</p>
              <p className="text-2xl font-bold">{summary.tracked_outcomes}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">7-Day Accuracy</p>
              <p className="text-2xl font-bold">{(summary.accuracy_7d * 100).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">30-Day Accuracy</p>
              <p className="text-2xl font-bold">{(summary.accuracy_30d * 100).toFixed(1)}%</p>
            </div>
          </div>
        )}
      </AsyncDataDisplay>
    </div>
  );
};

export default PerformanceSummary;
