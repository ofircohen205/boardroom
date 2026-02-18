import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAPIClient } from '@/hooks/useAPIClient';
import { useFetch } from '@/hooks/useFetch';
import { useMutation } from '@/hooks/useMutation';
import { AsyncDataDisplay, StatusBadge } from '@/components/common';
import { Plus, Trash2, Power, Calendar, Clock } from 'lucide-react';
import PageContainer from '@/components/layout/PageContainer';
import type { CreateScheduleInput } from '@/lib/api/types';

export default function SchedulesPage() {
  const apiClient = useAPIClient();
  const [showCreateForm, setShowCreateForm] = useState(false);

  // Form state
  const [ticker, setTicker] = useState('');
  const [market, setMarket] = useState('US');
  const [frequency, setFrequency] = useState('daily');

  // Fetch schedules
  const { data: schedules, isLoading, error, refetch } = useFetch(
    () => apiClient.schedules.list(),
    { dependencies: [apiClient] }
  );

  // Create schedule mutation
  const { mutate: createSchedule, isLoading: isCreating, error: createError } = useMutation(
    (data: CreateScheduleInput) => apiClient.schedules.create(data),
    {
      onSuccess: () => {
        setTicker('');
        setShowCreateForm(false);
        refetch();
      },
    }
  );

  // Delete schedule mutation
  const { mutate: deleteSchedule } = useMutation(
    (id: string) => apiClient.schedules.delete(id),
    {
      onSuccess: () => refetch(),
    }
  );

  // Toggle schedule mutation
  const { mutate: toggleSchedule } = useMutation(
    ({ id, active }: { id: string; active: boolean }) => apiClient.schedules.toggle(id, active),
    {
      onSuccess: () => refetch(),
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createSchedule({
      ticker: ticker.toUpperCase(),
      market,
      frequency,
      time: '08:00', // Default time (8 AM ET)
    });
  };

  const getFrequencyLabel = (frequency: string) => {
    switch (frequency) {
      case 'daily':
        return 'Daily (8 AM ET)';
      case 'weekly':
        return 'Weekly (Mon 8 AM ET)';
      case 'on_change':
        return 'Hourly (Market Hours)';
      default:
        return frequency;
    }
  };

  const formatNextRun = (nextRun: string | null) => {
    if (!nextRun) return 'Not scheduled';

    const date = new Date(nextRun);
    const now = new Date();
    const diffMs = date.getTime() - now.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 0) return 'Pending';
    if (diffMins < 60) return `in ${diffMins} min`;
    if (diffHours < 24) return `in ${diffHours}h`;
    if (diffDays === 1) return 'Tomorrow';

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  const formatLastRun = (lastRun: string | null) => {
    if (!lastRun) return 'Never';

    const date = new Date(lastRun);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return 'Yesterday';

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <PageContainer
      maxWidth="narrow"
      title="Scheduled Analyses"
      headerAction={
        <Button onClick={() => setShowCreateForm(!showCreateForm)} className="gap-2">
          <Plus className="w-4 h-4" />
          New Schedule
        </Button>
      }
    >
      <div className="space-y-6">
        {/* Create Schedule Form */}
        {showCreateForm && (
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4">Create New Schedule</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="ticker">Ticker Symbol</Label>
                  <Input
                    id="ticker"
                    value={ticker}
                    onChange={(e) => setTicker(e.target.value)}
                    placeholder="AAPL"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="market">Market</Label>
                  <select
                    id="market"
                    value={market}
                    onChange={(e) => setMarket(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="US">US</option>
                    <option value="TASE">TASE</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="frequency">Frequency</Label>
                  <select
                    id="frequency"
                    value={frequency}
                    onChange={(e) => setFrequency(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="daily">Daily (8 AM ET)</option>
                    <option value="weekly">Weekly (Mon 8 AM ET)</option>
                    <option value="on_change">Hourly (Market Hours)</option>
                  </select>
                </div>
              </div>

              {createError && (
                <div className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded p-3">
                  {createError}
                </div>
              )}

              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setShowCreateForm(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={isCreating}>
                  {isCreating ? 'Creating...' : 'Create Schedule'}
                </Button>
              </div>
            </form>
          </Card>
        )}

        {/* Schedules List */}
        <AsyncDataDisplay
          isLoading={isLoading}
          error={error}
          data={schedules}
          emptyMessage="No scheduled analyses yet. Create your first schedule to automate stock analysis!"
          emptyIcon={Calendar}
          onRetry={refetch}
        >
          {(schedules) => (
            <div className="space-y-3">
              {schedules.map((schedule) => (
                <Card key={schedule.id} className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-lg">
                          {schedule.ticker} ({schedule.market})
                        </h3>
                        <StatusBadge
                          type="schedule"
                          status={schedule.active ? 'active' : 'paused'}
                          size="sm"
                        />
                      </div>

                      <p className="text-sm text-muted-foreground">
                        Frequency:{' '}
                        <span className="font-medium text-foreground">
                          {getFrequencyLabel(schedule.frequency)}
                        </span>
                      </p>

                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          <span>
                            Next run:{' '}
                            <span className="font-medium text-foreground">
                              {formatNextRun(schedule.next_run)}
                            </span>
                          </span>
                        </div>
                        <div>
                          Last run: <span className="font-medium">{formatLastRun(schedule.last_run)}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => toggleSchedule({ id: schedule.id, active: !schedule.active })}
                        title={schedule.active ? 'Pause Schedule' : 'Activate Schedule'}
                        className={schedule.active ? '' : 'opacity-50'}
                      >
                        <Power className="w-4 h-4" />
                      </Button>

                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => deleteSchedule(schedule.id)}
                        title="Delete Schedule"
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </AsyncDataDisplay>

        {/* Info Card */}
        <Card className="p-4 bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
          <p className="text-sm text-blue-900 dark:text-blue-100">
            <strong>Note:</strong> Scheduled analyses run automatically at your chosen frequency. Daily schedules run
            at 8 AM ET before market open (Mon-Fri). Weekly schedules run on Monday at 8 AM ET. Hourly schedules run
            every hour during market hours (10 AM - 4 PM ET). You'll receive notifications when analyses complete. You
            can have up to 50 active schedules.
          </p>
        </Card>
      </div>
    </PageContainer>
  );
}
