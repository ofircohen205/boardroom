import React from 'react';
import PageContainer from '@/components/layout/PageContainer';
import PerformanceSummary from '../components/performance/PerformanceSummary';
import AccuracyChart from '../components/performance/AccuracyChart';
import AgentLeaderboard from '../components/performance/AgentLeaderboard';
import RecentOutcomes from '../components/performance/RecentOutcomes';

const PerformancePage: React.FC = () => {
  return (
    <PageContainer
      maxWidth="wide"
      title="Performance Dashboard"
      description="Track the accuracy and performance of your AI agents"
    >
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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
    </PageContainer>
  );
};

export default PerformancePage;
