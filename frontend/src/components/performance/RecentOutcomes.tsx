import { useAPIClient } from '@/hooks/useAPIClient';
import { useFetch } from '@/hooks/useFetch';
import { AsyncDataDisplay } from '@/components/common';
import { Activity } from 'lucide-react';

const RecentOutcomes = () => {
  const apiClient = useAPIClient();

  const { data: outcomes, isLoading, error } = useFetch(
    () => apiClient.performance.getOutcomes(20),
    { dependencies: [apiClient] }
  );

  return (
    <div className="bg-gray-800 p-4 rounded-lg">
      <h2 className="text-lg font-semibold mb-2">Recent Outcomes</h2>

      <AsyncDataDisplay
        isLoading={isLoading}
        error={error}
        data={outcomes}
        emptyMessage="No recent outcomes available yet"
        emptyIcon={Activity}
        loadingMessage="Loading outcomes..."
      >
        {(outcomes) => (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-gray-400 uppercase">
                <tr>
                  <th scope="col" className="py-2">Ticker</th>
                  <th scope="col" className="py-2">Recommendation</th>
                  <th scope="col" className="py-2">Price at Rec.</th>
                  <th scope="col" className="py-2">Price after 7d</th>
                  <th scope="col" className="py-2">Outcome</th>
                  <th scope="col" className="py-2">Date</th>
                </tr>
              </thead>
              <tbody>
                {outcomes.map((outcome) => (
                  <tr key={outcome.id} className="border-b border-gray-700">
                    <td className="py-2 font-medium">{outcome.ticker}</td>
                    <td className="py-2 capitalize">{outcome.action}</td>
                    <td className="py-2 font-mono">${outcome.recommendation_price.toFixed(2)}</td>
                    <td className="py-2 font-mono">
                      {outcome.outcome_price ? `$${outcome.outcome_price.toFixed(2)}` : 'N/A'}
                    </td>
                    <td className="py-2">
                      {outcome.is_correct === null
                        ? 'Pending'
                        : outcome.is_correct
                        ? 'Correct'
                        : 'Incorrect'}
                    </td>
                    <td className="py-2">{new Date(outcome.decided_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </AsyncDataDisplay>
    </div>
  );
};

export default RecentOutcomes;
