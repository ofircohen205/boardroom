import React, { useEffect, useState } from 'react';
import type { RecentOutcome } from '@/types/performance';
import { fetchAPI } from '@/lib/api';

const RecentOutcomes: React.FC = () => {
  const [outcomes, setOutcomes] = useState<RecentOutcome[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOutcomes = async () => {
      try {
        const data = await fetchAPI('/api/performance/recent');
        setOutcomes(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchOutcomes();
  }, []);

  if (loading) {
    return (
      <div className="bg-gray-800 p-4 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Recent Outcomes</h2>
        <p>Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800 p-4 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Recent Outcomes</h2>
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 p-4 rounded-lg">
      <h2 className="text-lg font-semibold mb-2">Recent Outcomes</h2>
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
              <tr key={outcome.created_at} className="border-b border-gray-700">
                <td className="py-2 font-medium">{outcome.ticker}</td>
                <td className="py-2">{outcome.action_recommended}</td>
                <td className="py-2 font-mono">${outcome.price_at_recommendation.toFixed(2)}</td>
                <td className="py-2 font-mono">
                  {outcome.price_after_7d ? `$${outcome.price_after_7d.toFixed(2)}` : 'N/A'}
                </td>
                <td className="py-2">
                  {outcome.outcome_correct === null
                    ? 'Pending'
                    : outcome.outcome_correct
                    ? 'Correct'
                    : 'Incorrect'}
                </td>
                <td className="py-2">{new Date(outcome.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default RecentOutcomes;
