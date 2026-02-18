import { useAPIClient } from '@/hooks/useAPIClient';
import { useFetch } from '@/hooks/useFetch';
import { AsyncDataDisplay } from '@/components/common';
import { Trophy } from 'lucide-react';

const AgentLeaderboard = () => {
  const apiClient = useAPIClient();

  const { data: leaderboard, isLoading, error } = useFetch(
    () => apiClient.performance.getAgentStats(),
    { dependencies: [apiClient] }
  );

  return (
    <div className="bg-gray-800 p-4 rounded-lg">
      <h2 className="text-lg font-semibold mb-2">Agent Leaderboard</h2>

      <AsyncDataDisplay
        isLoading={isLoading}
        error={error}
        data={leaderboard}
        emptyMessage="No agent data available yet"
        emptyIcon={Trophy}
        loadingMessage="Loading leaderboard..."
      >
        {(leaderboard) => (
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-400 uppercase">
              <tr>
                <th scope="col" className="py-2">Agent</th>
                <th scope="col" className="py-2 text-right">Accuracy</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.map((agent) => (
                <tr key={agent.agent_name} className="border-b border-gray-700">
                  <td className="py-2 font-medium capitalize">{agent.agent_name}</td>
                  <td className="py-2 text-right font-mono">{(agent.accuracy * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </AsyncDataDisplay>
    </div>
  );
};

export default AgentLeaderboard;
