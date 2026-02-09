import React from 'react';
import PerformanceSummary from '../components/performance/PerformanceSummary';
import AccuracyChart from '../components/performance/AccuracyChart';
import AgentLeaderboard from '../components/performance/AgentLeaderboard';
import RecentOutcomes from '../components/performance/RecentOutcomes';

const PerformancePage: React.FC = () => {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Performance Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-3">
          <PerformanceSummary />
        </div>
        <div className="lg:col-span-2">
          <AccuracyChart />
        </div>
        <div>
          <AgentLeaderboard />
        </div>
        <div className="lg:col-span-3">
          <RecentOutcomes />
        </div>
      </div>
    </div>
  );
};

export default PerformancePage;