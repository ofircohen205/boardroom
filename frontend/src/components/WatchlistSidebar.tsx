import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2, Trash2, TrendingUp, Plus, GitCompare } from 'lucide-react';

interface WatchlistItem {
  id: string;
  ticker: string;
  market: string;
}

interface Watchlist {
  id: string;
  name: string;
  items: WatchlistItem[];
}

interface WatchlistSidebarProps {
  onSelectTicker: (ticker: string) => void;
}

export function WatchlistSidebar({ onSelectTicker }: WatchlistSidebarProps) {
  const { token, logout } = useAuth();
  const navigate = useNavigate();
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [newTicker, setNewTicker] = useState('');

  const fetchWatchlists = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/watchlists`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.status === 401) logout();
      if (res.ok) {
        const data = await res.json();
        setWatchlists(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [token, logout]);

  useEffect(() => {
    if (token) fetchWatchlists();
  }, [token, fetchWatchlists]);

  const handleAddItem = async (watchlistId: string) => {
    if (!newTicker) return;
    setAdding(true);
    try {
        const res = await fetch(`${API_BASE_URL}/api/watchlists/${watchlistId}/items`, {
            method: 'POST',
            headers: {
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ticker: newTicker, market: 'US' })
        });
        if (res.ok) {
            setNewTicker('');
            fetchWatchlists();
        }
    } catch (error) {
        console.error(error);
    } finally {
        setAdding(false);
    }
  };

  const handleDeleteItem = async (watchlistId: string, itemId: string) => {
    try {
        const res = await fetch(`${API_BASE_URL}/api/watchlists/${watchlistId}/items/${itemId}`, {
            method: 'DELETE',
            headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) fetchWatchlists();
    } catch (e) { console.error(e); }
  };

  const handleCompareAll = () => {
    if (defaultWatchlist && defaultWatchlist.items.length >= 2) {
      const tickers = defaultWatchlist.items.map(item => item.ticker).slice(0, 4); // Max 4 tickers
      navigate(`/compare?tickers=${tickers.join(',')}`);
    }
  };

  if (loading) return <div className="w-64 h-full border-r border-white/10 p-4 flex justify-center"><Loader2 className="animate-spin" /></div>;

  const defaultWatchlist = watchlists[0]; // Assuming user has at least one

  if (!defaultWatchlist) return <div className="p-4">No watchlist found</div>;

  return (
    <div className="w-80 border-l border-white/10 h-full bg-card/30 backdrop-blur-xl flex flex-col">
        <div className="p-4 border-b border-white/10 space-y-2">
            <div className="flex items-center justify-between">
                <h2 className="font-semibold flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-primary"/> Watchlist
                </h2>
                {defaultWatchlist && defaultWatchlist.items.length >= 2 && (
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleCompareAll}
                        className="gap-1 text-xs"
                        title="Compare all watchlist items"
                    >
                        <GitCompare className="w-3 h-3"/> Compare
                    </Button>
                )}
            </div>
        </div>

        <div className="p-4 space-y-4 flex-1 overflow-auto">
            <div className="flex gap-2">
                <Input
                    placeholder="Add Ticker..."
                    value={newTicker}
                    onChange={e => setNewTicker(e.target.value.toUpperCase())}
                    className="h-8"
                />
                <Button size="sm" onClick={() => handleAddItem(defaultWatchlist.id)} disabled={adding}>
                    {adding ? <Loader2 className="w-4 h-4 animate-spin"/> : <Plus className="w-4 h-4"/>}
                </Button>
            </div>

            <div className="space-y-1">
                {defaultWatchlist.items.map(item => (
                    <div key={item.id} className="group flex items-center justify-between p-2 rounded-md hover:bg-background/50 cursor-pointer border border-transparent hover:border-white/5 transition-all" onClick={() => onSelectTicker(item.ticker)}>
                        <div className="font-medium bg-primary/10 text-primary px-2 py-0.5 rounded text-sm">{item.ticker}</div>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6 opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-opacity"
                            onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteItem(defaultWatchlist.id, item.id);
                            }}
                        >
                            <Trash2 className="w-3 h-3"/>
                        </Button>
                    </div>
                ))}
                {defaultWatchlist.items.length === 0 && (
                    <div className="text-sm text-muted-foreground text-center py-4">List is empty</div>
                )}
            </div>
        </div>
    </div>
  );
}
