import React, { useEffect, useState } from 'react';
import type { AgentAccuracy } from '@/types/performance';
import { fetchAPI } from '@/lib/api';

const AgentLeaderboard: React.FC = () => {
  const [leaderboard, setLeaderboard] = useState<AgentAccuracy[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        const data = await fetchAPI('/api/performance/agents');
        setLeaderboard(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchLeaderboard();
  }, []);

  if (loading) {
    return (
      <div className="bg-gray-800 p-4 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Agent Leaderboard</h2>
        <p>Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800 p-4 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Agent Leaderboard</h2>
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 p-4 rounded-lg">
      <h2 className="text-lg font-semibold mb-2">Agent Leaderboard</h2>
      <table className="w-full text-sm text-left">
        <thead className="text-xs text-gray-400 uppercase">
          <tr>
            <th scope="col" className="py-2">Agent</th>
            <th scope="col" className="py-2 text-right">Accuracy</th>
          </tr>
        </thead>
        <tbody>
          {leaderboard.map((agent) => (
            <tr key={agent.agent_type} className="border-b border-gray-700">
              <td className="py-2 font-medium">{agent.agent_type}</td>
              <td className="py-2 text-right font-mono">{(agent.accuracy * 100).toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default AgentLeaderboard;
