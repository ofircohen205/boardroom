import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAPIClient } from '@/hooks/useAPIClient';
import { useFetch } from '@/hooks/useFetch';
import { useMutation } from '@/hooks/useMutation';
import { AsyncDataDisplay, StatusBadge } from '@/components/common';
import { Plus, Trash2, Power, RotateCcw, Bell } from 'lucide-react';
import PageContainer from '@/components/layout/PageContainer';
import type { CreateAlertInput } from '@/lib/api/types';

export default function AlertsPage() {
  const apiClient = useAPIClient();
  const [showCreateForm, setShowCreateForm] = useState(false);

  // Form state
  const [ticker, setTicker] = useState('');
  const [market, setMarket] = useState('US');
  const [condition, setCondition] = useState('above');
  const [targetValue, setTargetValue] = useState('');

  // Fetch alerts
  const { data: alerts, isLoading, error, refetch } = useFetch(
    () => apiClient.alerts.list(false),
    { dependencies: [apiClient] }
  );

  // Create alert mutation
  const { mutate: createAlert, isLoading: isCreating, error: createError } = useMutation(
    (data: CreateAlertInput) => apiClient.alerts.create(data),
    {
      onSuccess: () => {
        // Reset form
        setTicker('');
        setTargetValue('');
        setShowCreateForm(false);
        refetch();
      },
    }
  );

  // Delete alert mutation
  const { mutate: deleteAlert } = useMutation(
    (id: string) => apiClient.alerts.delete(id),
    {
      onSuccess: () => refetch(),
    }
  );

  // Toggle alert mutation
  const { mutate: toggleAlert } = useMutation(
    ({ id, active }: { id: string; active: boolean }) => apiClient.alerts.toggle(id, active),
    {
      onSuccess: () => refetch(),
    }
  );

  // Reset alert mutation
  const { mutate: resetAlert } = useMutation(
    (id: string) => apiClient.alerts.reset(id),
    {
      onSuccess: () => refetch(),
    }
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createAlert({
      ticker: ticker.toUpperCase(),
      market,
      condition,
      target_value: parseFloat(targetValue),
    });
  };

  const getConditionLabel = (condition: string) => {
    switch (condition) {
      case 'above':
        return 'Price Above';
      case 'below':
        return 'Price Below';
      case 'change_pct':
        return 'Change %';
      default:
        return condition;
    }
  };

  return (
    <PageContainer
      maxWidth="narrow"
      title="Price Alerts"
      headerAction={
        <Button onClick={() => setShowCreateForm(!showCreateForm)} className="gap-2">
          <Plus className="w-4 h-4" />
          New Alert
        </Button>
      }
    >
      <div className="space-y-6">
        {/* Create Alert Form */}
        {showCreateForm && (
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4">Create New Alert</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
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
                    <option value="US">🇺🇸 US Market</option>
                    <option value="TASE">🇮🇱 Tel Aviv</option>
                    <option value="LSE">🇬🇧 London</option>
                    <option value="TSE">🇯🇵 Tokyo</option>
                    <option value="HKEX">🇭🇰 Hong Kong</option>
                    <option value="XETRA">🇩🇪 Frankfurt</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="condition">Condition</Label>
                  <select
                    id="condition"
                    value={condition}
                    onChange={(e) => setCondition(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    <option value="above">Price Above</option>
                    <option value="below">Price Below</option>
                    <option value="change_pct">Change %</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="targetValue">
                    {condition === 'change_pct' ? 'Percentage (%)' : 'Target Price ($)'}
                  </Label>
                  <Input
                    id="targetValue"
                    type="number"
                    step="0.01"
                    value={targetValue}
                    onChange={(e) => setTargetValue(e.target.value)}
                    placeholder={condition === 'change_pct' ? '5' : '150.00'}
                    required
                  />
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
                  {isCreating ? 'Creating...' : 'Create Alert'}
                </Button>
              </div>
            </form>
          </Card>
        )}

        {/* Alerts List */}
        <AsyncDataDisplay
          isLoading={isLoading}
          error={error}
          data={alerts}
          emptyMessage="No alerts yet. Create your first alert to get started!"
          emptyIcon={Bell}
          onRetry={refetch}
        >
          {(alerts) => (
            <div className="space-y-3">
              {alerts.map((alert) => (
                <Card key={alert.id} className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-lg">
                          {alert.ticker} ({alert.market})
                        </h3>
                        {alert.triggered && (
                          <StatusBadge type="alert" status="triggered" size="sm" />
                        )}
                        {!alert.active && (
                          <StatusBadge type="alert" status="paused" size="sm" />
                        )}
                      </div>

                      <p className="text-sm text-muted-foreground">
                        {getConditionLabel(alert.condition)}:{' '}
                        <span className="font-medium text-foreground">
                          {alert.condition === 'change_pct'
                            ? `${alert.target_value}%`
                            : `$${alert.target_value}`}
                        </span>
                      </p>

                      {alert.triggered_at && (
                        <p className="text-xs text-muted-foreground">
                          Triggered at: {new Date(alert.triggered_at).toLocaleString()}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {alert.triggered && (
                        <Button
                          variant="outline"
                          size="icon"
                          onClick={() => resetAlert(alert.id)}
                          title="Reset Alert"
                        >
                          <RotateCcw className="w-4 h-4" />
                        </Button>
                      )}

                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => toggleAlert({ id: alert.id, active: !alert.active })}
                        title={alert.active ? 'Pause Alert' : 'Activate Alert'}
                        className={alert.active ? '' : 'opacity-50'}
                      >
                        <Power className="w-4 h-4" />
                      </Button>

                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => deleteAlert(alert.id)}
                        title="Delete Alert"
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
            <strong>Note:</strong> Alerts are checked every 5 minutes during market hours (9:30 AM - 4:00 PM ET,
            Mon-Fri). After triggering, alerts have a 1-hour cooldown period to prevent spam. You can have up to 50
            active alerts.
          </p>
        </Card>
      </div>
    </PageContainer>
  );
}
