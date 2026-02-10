import { useState, useEffect } from 'react';
// import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/contexts/AuthContext';
import { API_BASE_URL } from '@/lib/api';
import { Plus, Trash2, Power, RotateCcw, Bell } from 'lucide-react';
import PageContainer from '@/components/layout/PageContainer';

interface Alert {
  id: string;
  ticker: string;
  market: string;
  condition: string;
  target_value: number;
  triggered: boolean;
  triggered_at: string | null;
  active: boolean;
  created_at: string;
}

export default function AlertsPage() {
  const { token } = useAuth();
  // const navigate = useNavigate();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [ticker, setTicker] = useState('');
  const [market, setMarket] = useState('US');
  const [condition, setCondition] = useState('above');
  const [targetValue, setTargetValue] = useState('');

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    if (!token) return;

    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/alerts?active_only=false`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAlerts(data);
      } else {
        setError('Failed to load alerts');
      }
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
      setError('Failed to load alerts');
    } finally {
      setIsLoading(false);
    }
  };

  const createAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/alerts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          ticker: ticker.toUpperCase(),
          market,
          condition,
          target_value: parseFloat(targetValue),
        }),
      });

      if (response.ok) {
        // Reset form
        setTicker('');
        setTargetValue('');
        setShowCreateForm(false);
        // Refresh alerts
        fetchAlerts();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to create alert');
      }
    } catch (err) {
      console.error('Failed to create alert:', err);
      setError('Failed to create alert');
    }
  };

  const deleteAlert = async (alertId: string) => {
    if (!token) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/alerts/${alertId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        setAlerts((prev) => prev.filter((a) => a.id !== alertId));
      }
    } catch (err) {
      console.error('Failed to delete alert:', err);
    }
  };

  const toggleAlert = async (alertId: string, currentActive: boolean) => {
    if (!token) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/alerts/${alertId}/toggle`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ active: !currentActive }),
      });

      if (response.ok) {
        const updatedAlert = await response.json();
        setAlerts((prev) => prev.map((a) => (a.id === alertId ? updatedAlert : a)));
      }
    } catch (err) {
      console.error('Failed to toggle alert:', err);
    }
  };

  const resetAlert = async (alertId: string) => {
    if (!token) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/alerts/${alertId}/reset`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const updatedAlert = await response.json();
        setAlerts((prev) => prev.map((a) => (a.id === alertId ? updatedAlert : a)));
      }
    } catch (err) {
      console.error('Failed to reset alert:', err);
    }
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
            <form onSubmit={createAlert} className="space-y-4">
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
                    <option value="US">US</option>
                    <option value="TASE">TASE</option>
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

              {error && (
                <div className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded p-3">
                  {error}
                </div>
              )}

              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setShowCreateForm(false)}>
                  Cancel
                </Button>
                <Button type="submit">Create Alert</Button>
              </div>
            </form>
          </Card>
        )}

        {/* Alerts List */}
        {isLoading ? (
          <div className="text-center py-12 text-muted-foreground">Loading alerts...</div>
        ) : alerts.length === 0 ? (
          <div className="text-center py-12">
            <Bell className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">No alerts yet. Create your first alert to get started!</p>
          </div>
        ) : (
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
                        <Badge variant="default" className="bg-yellow-500">
                          Triggered
                        </Badge>
                      )}
                      {!alert.active && <Badge variant="secondary">Paused</Badge>}
                    </div>

                    <p className="text-sm text-muted-foreground">
                      {getConditionLabel(alert.condition)}:{' '}
                      <span className="font-medium text-foreground">
                        {alert.condition === 'change_pct' ? `${alert.target_value}%` : `$${alert.target_value}`}
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
                      onClick={() => toggleAlert(alert.id, alert.active)}
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
