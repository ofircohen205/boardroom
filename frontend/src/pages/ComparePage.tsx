import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAPIClient } from '@/hooks/useAPIClient';
import { useFetch } from '@/hooks/useFetch';
import { useMutation } from '@/hooks/useMutation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Loader2, Trophy, BarChart3, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ComparisonResult } from '@/lib/api/comparison';
import { RelativePerformanceChart } from '@/components/RelativePerformanceChart';
import { ComparisonTable } from '@/components/ComparisonTable';
import PageContainer from '@/components/layout/PageContainer';

export function ComparePage() {
  const apiClient = useAPIClient();
  const [searchParams] = useSearchParams();
  const [mode, setMode] = useState<'manual' | 'sector'>('manual');
  const [tickers, setTickers] = useState<string[]>([]);
  const [currentTicker, setCurrentTicker] = useState('');
  const [selectedSector, setSelectedSector] = useState<string>('');
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);

  // Fetch available sectors
  const { data: sectors } = useFetch(() => apiClient.comparison.getSectors(), {
    dependencies: [apiClient],
  });

  // Compare stocks mutation
  const { mutate: compareStocks, isLoading, error } = useMutation(
    async () => {
      if (mode === 'manual') {
        return apiClient.comparison.compareStocks(tickers, 'US');
      } else {
        return apiClient.comparison.analyzeSector(selectedSector, 5, 'US');
      }
    },
    {
      onSuccess: (result) => {
        setComparison(result);
      },
    }
  );

  // Pre-fill tickers from URL query parameters
  useEffect(() => {
    const singleTicker = searchParams.get('ticker');
    const multipleTickers = searchParams.get('tickers');

    if (multipleTickers) {
      const tickerList = multipleTickers
        .split(',')
        .map((t) => t.trim().toUpperCase())
        .filter(Boolean);
      if (tickerList.length > 0) {
        // Only update if different to avoid cascading renders
        const newTickers = tickerList.slice(0, 4);
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setTickers((prev) => {
          if (JSON.stringify(prev) !== JSON.stringify(newTickers)) {
            return newTickers;
          }
          return prev;
        });
      }
    } else if (singleTicker) {
      const upperTicker = singleTicker.toUpperCase();
      setTickers((prev) => {
        if (!prev.includes(upperTicker)) {
          return [upperTicker];
        }
        return prev;
      });
    }

  }, [searchParams]);

  const addTicker = () => {
    const ticker = currentTicker.trim().toUpperCase();
    if (ticker && !tickers.includes(ticker) && tickers.length < 4) {
      setTickers([...tickers, ticker]);
      setCurrentTicker('');
    }
  };

  const removeTicker = (ticker: string) => {
    setTickers(tickers.filter((t) => t !== ticker));
  };

  const runComparison = () => {
    if (mode === 'manual' && tickers.length < 2) return;
    if (mode === 'sector' && !selectedSector) return;
    compareStocks();
  };

  return (
    <PageContainer
      maxWidth="wide"
      title="Comparative Analysis"
      description="Compare multiple stocks side-by-side or analyze an entire sector"
    >
      <div className="space-y-6">
        {/* Input Section */}
        {!comparison && (
          <Card className="glass border-primary/20">
            <CardHeader>
              <CardTitle>Select Stocks to Compare</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Mode Toggle */}
              <div className="flex gap-2">
                <Button
                  variant={mode === 'manual' ? 'default' : 'outline'}
                  onClick={() => setMode('manual')}
                  className="flex-1"
                >
                  Manual Selection
                </Button>
                <Button
                  variant={mode === 'sector' ? 'default' : 'outline'}
                  onClick={() => setMode('sector')}
                  className="flex-1"
                >
                  Sector Analysis
                </Button>
              </div>

              {mode === 'manual' ? (
                <div className="space-y-4">
                  {/* Ticker Input */}
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={currentTicker}
                      onChange={(e) => setCurrentTicker(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && addTicker()}
                      placeholder="Enter ticker (e.g., AAPL)"
                      className="flex-1 bg-muted/30 border border-border rounded-lg px-4 py-2 text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
                      maxLength={10}
                    />
                    <Button onClick={addTicker} disabled={!currentTicker.trim() || tickers.length >= 4}>
                      Add
                    </Button>
                  </div>

                  {/* Ticker Chips */}
                  {tickers.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {tickers.map((ticker) => (
                        <Badge key={ticker} variant="outline" className="gap-2 px-3 py-1 text-sm">
                          {ticker}
                          <button onClick={() => removeTicker(ticker)} className="hover:text-destructive">
                            <X className="h-3 w-3" />
                          </button>
                        </Badge>
                      ))}
                    </div>
                  )}

                  <p className="text-xs text-muted-foreground">Add 2-4 tickers to compare</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <Select value={selectedSector} onValueChange={setSelectedSector}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a sector" />
                    </SelectTrigger>
                    <SelectContent>
                      {sectors?.map((sector) => (
                        <SelectItem key={sector.key} value={sector.key}>
                          {sector.name} ({sector.ticker_count} stocks)
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">Analyzes top 5 stocks in the selected sector</p>
                </div>
              )}

              {error && (
                <div className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-lg p-3">
                  {error}
                </div>
              )}

              <Button
                onClick={runComparison}
                disabled={
                  isLoading || (mode === 'manual' && tickers.length < 2) || (mode === 'sector' && !selectedSector)
                }
                className="w-full gap-2"
                size="lg"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <BarChart3 className="h-4 w-4" />
                    Run Comparison
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Results Section */}
        {comparison && (
          <div className="space-y-6 animate-fade-up">
            {/* Best Pick Card */}
            <Card className="glass border-primary/50 bg-primary/5">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Trophy className="h-5 w-5 text-yellow-500" />
                  Best Pick
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-primary mb-2">{comparison.best_pick}</div>
                <p className="text-muted-foreground">{comparison.comparison_summary}</p>
              </CardContent>
            </Card>

            {/* Price History Chart */}
            {comparison.price_histories && Object.keys(comparison.price_histories).length > 0 && (
              <Card className="glass">
                <CardHeader>
                  <CardTitle>Price Performance Comparison</CardTitle>
                </CardHeader>
                <CardContent>
                  <RelativePerformanceChart data={comparison.price_histories} />
                </CardContent>
              </Card>
            )}

            {/* Rankings */}
            <Card className="glass">
              <CardHeader>
                <CardTitle>Rankings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {comparison.rankings.map((ranking) => (
                  <div
                    key={ranking.ticker}
                    className={cn(
                      'p-4 rounded-lg border transition-colors',
                      ranking.rank === 1 ? 'bg-primary/10 border-primary/30' : 'bg-muted/30 border-border'
                    )}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div
                          className={cn(
                            'flex items-center justify-center w-8 h-8 rounded-full font-bold',
                            ranking.rank === 1 ? 'bg-yellow-500/20 text-yellow-500' : 'bg-muted/30 text-muted-foreground'
                          )}
                        >
                          {ranking.rank}
                        </div>
                        <div>
                          <div className="font-mono font-bold text-lg">{ranking.ticker}</div>
                          <div className="text-xs text-muted-foreground">Score: {ranking.score.toFixed(1)}</div>
                        </div>
                      </div>
                      <Badge
                        variant="outline"
                        className={cn(
                          ranking.decision.action === 'BUY' && 'bg-success/10 text-success border-success/20',
                          ranking.decision.action === 'SELL' && 'bg-destructive/10 text-destructive border-destructive/20',
                          ranking.decision.action === 'HOLD' && 'bg-warning/10 text-warning border-warning/20'
                        )}
                      >
                        {ranking.decision.action}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{ranking.rationale}</p>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Comparison Table */}
            {comparison.stock_data && (
              <Card className="glass">
                <CardHeader>
                  <CardTitle>Side-by-Side Comparison</CardTitle>
                </CardHeader>
                <CardContent>
                  {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                  <ComparisonTable data={comparison.stock_data as any} />
                </CardContent>
              </Card>
            )}

            {/* Relative Performance */}
            {comparison.relative_strength && (
              <Card className="glass">
                <CardHeader>
                  <CardTitle>Relative Performance</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(comparison.relative_strength.relative_performance).map(([ticker, performance]) => (
                      <div key={ticker} className="bg-muted/30 rounded-lg p-4 border border-border">
                        <div className="font-mono font-bold mb-1">{ticker}</div>
                        <div
                          className={cn('text-2xl font-bold', performance > 0 ? 'text-success' : 'text-destructive')}
                        >
                          {performance > 0 ? '+' : ''}
                          {performance.toFixed(2)}%
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            <Button
              onClick={() => {
                setComparison(null);
                setTickers([]);
                setSelectedSector('');
              }}
              variant="outline"
              className="w-full"
            >
              New Comparison
            </Button>
          </div>
        )}
      </div>
    </PageContainer>
  );
}
