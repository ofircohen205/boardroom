import { useState, useEffect, useCallback } from 'react';
import { useAPIClient } from '@/hooks/useAPIClient';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, History, CheckCircle, XCircle, ArrowUpCircle, ArrowDownCircle, MinusCircle } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface AnalysisSession {
  id: string;
  ticker: string;
  market: string;
  created_at: string;
  decision: string | null;
  confidence: number | null;
  outcome_correct: boolean | null;
}

export function AnalysisHistory({ ticker }: { ticker?: string }) {
  const api = useAPIClient();
  const [history, setHistory] = useState<AnalysisSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [limit, setLimit] = useState(10);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    try {
      // The current API doesn't support ticker filtering directly in getHistory,
      // but if the endpoint supports it we might need to pass it, or we can filter client-side
      // if ticker is provided. Looking at analysis.ts, getHistory only takes limit.
      // Wait, let's check if we can pass ticker as query param.
      // Let's modify the apiClient analysis method later if needed, or use api.get directly.
      let endpoint = `/api/analyses?limit=${limit}`;
      if (ticker) endpoint += `&ticker=${ticker}`;

      const resData = await api.get<AnalysisSession[]>(endpoint);
      setHistory(resData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [api, ticker, limit]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const getDecisionIcon = (decision: string | null) => {
      switch (decision) {
          case 'buy': return <ArrowUpCircle className="w-4 h-4 text-green-500" />;
          case 'sell': return <ArrowDownCircle className="w-4 h-4 text-red-500" />;
          case 'hold': return <MinusCircle className="w-4 h-4 text-yellow-500" />;
          default: return <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />;
      }
  };

  const getOutcomeIcon = (outcome: boolean | null) => {
    if (outcome === null) {
      return <span className="text-xs text-muted-foreground">Pending</span>;
    }
    return outcome ? <CheckCircle className="w-4 h-4 text-green-500" /> : <XCircle className="w-4 h-4 text-red-500" />;
  };

  return (
    <Card className="h-full bg-card/30 backdrop-blur-xl border-border flex flex-col">
        <CardHeader className="py-2 border-b border-border flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-medium flex items-center gap-2"><History className="w-4 h-4"/> Recent Analyses</CardTitle>
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase text-muted-foreground font-semibold tracking-wider">Limit</span>
              <Select value={limit.toString()} onValueChange={(v: string) => setLimit(parseInt(v))}>
                <SelectTrigger className="h-7 w-[60px] text-xs bg-background/50 border-border">
                  <SelectValue placeholder="Limit" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="5">5</SelectItem>
                  <SelectItem value="10">10</SelectItem>
                  <SelectItem value="20">20</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                </SelectContent>
              </Select>
            </div>
        </CardHeader>
        <CardContent className="p-0 flex-1 overflow-hidden">
            <ScrollArea className="h-full">
                {loading ? (
                    <div className="flex justify-center p-4"><Loader2 className="animate-spin text-muted-foreground"/></div>
                ) : history.length === 0 ? (
                    <div className="text-center text-sm text-muted-foreground p-4">No history found</div>
                ) : (
                    <div className="divide-y divide-border">
                        {history.map(s => (
                            <div key={s.id} className="p-3 hover:bg-muted/30 transition-colors flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div>{getDecisionIcon(s.decision)}</div>
                                    <div>
                                        <div className="font-medium text-sm flex items-center gap-2">
                                            {s.ticker} <span className="text-xs text-muted-foreground font-normal">{new Date(s.created_at).toLocaleDateString()}</span>
                                        </div>
                                        <div className="text-xs text-muted-foreground mt-0.5">
                                            {s.decision ? `Decision: ${s.decision.toUpperCase()}` : 'In Progress'}
                                        </div>
                                    </div>
                                </div>
                                <div>
                                    {getOutcomeIcon(s.outcome_correct)}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </ScrollArea>
        </CardContent>
    </Card>
  );
}
