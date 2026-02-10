import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { API_BASE_URL } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Loader2, Plus, Trash2, PieChart, TrendingUp } from 'lucide-react';
import PageContainer from '@/components/layout/PageContainer';

interface Position {
  id: string;
  ticker: string;
  quantity: number;
  avg_entry_price: number;
  market: string;
}

interface Portfolio {
  id: string;
  name: string;
  positions: Position[];
}

export default function PortfolioPage() {
  const { token, logout } = useAuth();
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [loading, setLoading] = useState(true);
  const [newTicker, setNewTicker] = useState('');
  const [newQty, setNewQty] = useState('');
  const [newPrice, setNewPrice] = useState('');
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    fetchPortfolios();
  }, [token]);

  const fetchPortfolios = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/portfolios`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.status === 401) logout();
      if (res.ok) {
        const data = await res.json();
        setPortfolios(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleAddPosition = async (portfolioId: string) => {
    if (!newTicker || !newQty || !newPrice) return;
    setAdding(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/portfolios/${portfolioId}/positions`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ticker: newTicker,
          quantity: parseFloat(newQty),
          entry_price: parseFloat(newPrice),
          market: 'US' // Default for now
        })
      });
      if (res.ok) {
        setNewTicker('');
        setNewQty('');
        setNewPrice('');
        fetchPortfolios();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setAdding(false);
    }
  };

  const handleDeletePosition = async (portfolioId: string, positionId: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/portfolios/${portfolioId}/positions/${positionId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) fetchPortfolios();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
     return <div className="flex justify-center p-8"><Loader2 className="animate-spin text-primary" /></div>;
  }

  // Handle case where user has no portfolio (create default)
  if (portfolios.length === 0) {
      // In reality we created one on register.
      return <div className="p-8 text-center">No portfolios found.</div>;
  }

  const activePortfolio = portfolios[0]; // Just showing first for now

  return (
    <PageContainer maxWidth="wide" title={activePortfolio.name}>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Portfolio Stats Card (Placeholder) */}
        <Card className="md:col-span-3 bg-card/50 backdrop-blur border-white/10">
            <CardHeader>
                <CardTitle className="flex items-center gap-2"><PieChart/> Portfolio Summary</CardTitle>
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
            <CardTitle className="text-lg flex items-center gap-2"><Plus className="w-4 h-4"/> Add Position</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Ticker</Label>
              <Input value={newTicker} onChange={e => setNewTicker(e.target.value.toUpperCase())} placeholder="AAPL" />
            </div>
            <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                <Label>Quantity</Label>
                <Input type="number" value={newQty} onChange={e => setNewQty(e.target.value)} placeholder="10" />
                </div>
                <div className="space-y-2">
                <Label>Avg Price</Label>
                <Input type="number" value={newPrice} onChange={e => setNewPrice(e.target.value)} placeholder="150.00" />
                </div>
            </div>
            <Button className="w-full" disabled={adding} onClick={() => handleAddPosition(activePortfolio.id)}>
                {adding && <Loader2 className="mr-2 h-4 w-4 animate-spin"/>}
                Add Position
            </Button>
          </CardContent>
        </Card>

        {/* Positions List */}
        <Card className="md:col-span-2 bg-card/50 backdrop-blur border-white/10">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2"><TrendingUp className="w-4 h-4"/> Holdings</CardTitle>
          </CardHeader>
          <CardContent>
            {activePortfolio.positions.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">No positions added yet.</div>
            ) : (
                <div className="space-y-2">
                    {activePortfolio.positions.map(pos => (
                        <div key={pos.id} className="flex items-center justify-between p-3 rounded-md bg-background/40 hover:bg-background/60 transition-colors border border-white/5">
                            <div className="flex items-center gap-3">
                                <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center font-bold text-xs text-primary">
                                    {pos.ticker.substring(0,2)}
                                </div>
                                <div>
                                    <div className="font-semibold">{pos.ticker}</div>
                                    <div className="text-xs text-muted-foreground">{pos.quantity} shares @ ${pos.avg_entry_price}</div>
                                </div>
                            </div>
                            <Button variant="ghost" size="icon" className="text-destructive hover:text-destructive/80" onClick={() => handleDeletePosition(activePortfolio.id, pos.id)}>
                                <Trash2 className="w-4 h-4"/>
                            </Button>
                        </div>
                    ))}
                </div>
            )}
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  );
}
