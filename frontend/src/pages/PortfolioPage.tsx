import { useState } from 'react';
import { useAPIClient } from '@/contexts/APIContext';
import { useFetch } from '@/hooks/useFetch';
import { useMutation } from '@/hooks/useMutation';
import { AsyncDataDisplay } from '@/components/common';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Loader2, Plus, Trash2, PieChart, TrendingUp, Briefcase } from 'lucide-react';
import PageContainer from '@/components/layout/PageContainer';
import type { AddPositionInput } from '@/lib/api/types';

export default function PortfolioPage() {
  const apiClient = useAPIClient();
  const [newTicker, setNewTicker] = useState('');
  const [newQty, setNewQty] = useState('');
  const [newPrice, setNewPrice] = useState('');

  // Fetch portfolios
  const { data: portfolios, isLoading, error, refetch } = useFetch(
    () => apiClient.portfolios.list(),
    { dependencies: [apiClient] }
  );

  // Add position mutation
  const { mutate: addPosition, isLoading: isAdding } = useMutation(
    ({ portfolioId, data }: { portfolioId: string; data: AddPositionInput }) =>
      apiClient.portfolios.addPosition(portfolioId, data),
    {
      onSuccess: () => {
        setNewTicker('');
        setNewQty('');
        setNewPrice('');
        refetch();
      },
    }
  );

  // Delete position mutation
  const { mutate: deletePosition } = useMutation(
    ({ portfolioId, positionId }: { portfolioId: string; positionId: string }) =>
      apiClient.portfolios.deletePosition(portfolioId, positionId),
    {
      onSuccess: () => refetch(),
    }
  );

  const handleAddPosition = (portfolioId: string) => {
    if (!newTicker || !newQty || !newPrice) return;

    addPosition({
      portfolioId,
      data: {
        ticker: newTicker,
        quantity: parseFloat(newQty),
        entry_price: parseFloat(newPrice),
        market: 'US', // Default for now
      },
    });
  };

  return (
    <PageContainer maxWidth="wide" title="Portfolio">
      <AsyncDataDisplay
        isLoading={isLoading}
        error={error}
        data={portfolios}
        isEmpty={(data) => data.length === 0}
        emptyMessage="No portfolios found."
        emptyIcon={Briefcase}
        onRetry={refetch}
      >
        {(portfolios) => {
          const activePortfolio = portfolios[0]; // Just showing first for now

          return (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Portfolio Stats Card */}
              <Card className="md:col-span-3 bg-card/50 backdrop-blur border-white/10">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <PieChart className="w-5 h-5" /> Portfolio Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 rounded-lg bg-background/50">
                      <div className="text-sm text-muted-foreground">Total Positions</div>
                      <div className="text-2xl font-bold">{activePortfolio.positions.length}</div>
                    </div>
                    <div className="p-4 rounded-lg bg-background/50">
                      <div className="text-sm text-muted-foreground">Total Value (Est)</div>
                      <div className="text-2xl font-bold">$0.00</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Add Position Form */}
              <Card className="bg-card/50 backdrop-blur border-white/10 h-fit">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Plus className="w-4 h-4" /> Add Position
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Ticker</Label>
                    <Input
                      value={newTicker}
                      onChange={(e) => setNewTicker(e.target.value.toUpperCase())}
                      placeholder="AAPL"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Quantity</Label>
                      <Input
                        type="number"
                        value={newQty}
                        onChange={(e) => setNewQty(e.target.value)}
                        placeholder="10"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Avg Price</Label>
                      <Input
                        type="number"
                        value={newPrice}
                        onChange={(e) => setNewPrice(e.target.value)}
                        placeholder="150.00"
                      />
                    </div>
                  </div>
                  <Button
                    className="w-full"
                    disabled={isAdding || !newTicker || !newQty || !newPrice}
                    onClick={() => handleAddPosition(activePortfolio.id)}
                  >
                    {isAdding && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Add Position
                  </Button>
                </CardContent>
              </Card>

              {/* Positions List */}
              <Card className="md:col-span-2 bg-card/50 backdrop-blur border-white/10">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <TrendingUp className="w-4 h-4" /> Holdings
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {activePortfolio.positions.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">No positions added yet.</div>
                  ) : (
                    <div className="space-y-2">
                      {activePortfolio.positions.map((pos) => (
                        <div
                          key={pos.id}
                          className="flex items-center justify-between p-3 rounded-md bg-background/40 hover:bg-background/60 transition-colors border border-white/5"
                        >
                          <div className="flex items-center gap-3">
                            <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center font-bold text-xs text-primary">
                              {pos.ticker.substring(0, 2)}
                            </div>
                            <div>
                              <div className="font-semibold">{pos.ticker}</div>
                              <div className="text-xs text-muted-foreground">
                                {pos.quantity} shares @ ${pos.avg_entry_price}
                              </div>
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-destructive hover:text-destructive/80"
                            onClick={() =>
                              deletePosition({ portfolioId: activePortfolio.id, positionId: pos.id })
                            }
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          );
        }}
      </AsyncDataDisplay>
    </PageContainer>
  );
}
