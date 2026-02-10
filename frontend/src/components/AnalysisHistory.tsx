import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { API_BASE_URL } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, History, CheckCircle, XCircle, ArrowUpCircle, ArrowDownCircle, MinusCircle } from 'lucide-react';

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
  const { token } = useAuth();
  const [history, setHistory] = useState<AnalysisSession[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    try {
      let url = `${API_BASE_URL}/api/analyses?limit=10`;
      if (ticker) url += `&ticker=${ticker}`;
      
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [token, ticker]);

  useEffect(() => {
    if (token) fetchHistory();
  }, [token, fetchHistory]);

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
    <Card className="h-full bg-card/30 backdrop-blur-xl border-white/10 flex flex-col">
        <CardHeader className="py-3 border-b border-white/10">
            <CardTitle className="text-sm font-medium flex items-center gap-2"><History className="w-4 h-4"/> Recent Analyses</CardTitle>
        </CardHeader>
        <CardContent className="p-0 flex-1 overflow-hidden">
            <ScrollArea className="h-full">
                {loading ? (
                    <div className="flex justify-center p-4"><Loader2 className="animate-spin text-muted-foreground"/></div>
                ) : history.length === 0 ? (
                    <div className="text-center text-sm text-muted-foreground p-4">No history found</div>
                ) : (
                    <div className="divide-y divide-white/5">
                        {history.map(s => (
                            <div key={s.id} className="p-3 hover:bg-white/5 transition-colors flex items-center justify-between">
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