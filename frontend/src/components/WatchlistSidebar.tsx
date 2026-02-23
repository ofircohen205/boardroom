import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useAPIClient } from '@/hooks/useAPIClient';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2, Trash2, TrendingUp, Plus, GitCompare } from 'lucide-react';
import type { Watchlist } from '@/lib/api/types';

interface WatchlistSidebarProps {
  onSelectTicker: (ticker: string) => void;
}

export function WatchlistSidebar({ onSelectTicker }: WatchlistSidebarProps) {
  const { token } = useAuth();
  const navigate = useNavigate();
  const api = useAPIClient();
  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [newTicker, setNewTicker] = useState('');

  const fetchWatchlists = useCallback(async () => {
    try {
      const data = await api.watchlists.list();
      setWatchlists(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    if (token) fetchWatchlists();
  }, [token, fetchWatchlists]);

  const handleAddItem = async (watchlistId: string) => {
    if (!newTicker) return;
    setAdding(true);
    try {
        await api.watchlists.addItem(watchlistId, { ticker: newTicker, market: 'US' });
        setNewTicker('');
        fetchWatchlists();
    } catch (error) {
        console.error(error);
    } finally {
        setAdding(false);
    }
  };

  const handleDeleteItem = async (watchlistId: string, itemId: string) => {
    try {
        await api.watchlists.removeItem(watchlistId, itemId);
        fetchWatchlists();
    } catch (e) { console.error(e); }
  };

  const handleCompareAll = () => {
    if (defaultWatchlist && defaultWatchlist.items.length >= 2) {
      const tickers = defaultWatchlist.items.map(item => item.ticker).slice(0, 4); // Max 4 tickers
      navigate(`/compare?tickers=${tickers.join(',')}`);
    }
  };

  if (loading) return <div className="w-64 h-full border-r border-border p-4 flex justify-center"><Loader2 className="animate-spin" /></div>;

  const defaultWatchlist = watchlists[0]; // Assuming user has at least one

  if (!defaultWatchlist) return <div className="p-4">No watchlist found</div>;

  return (
    <div className="w-80 border-l border-border h-full bg-card/30 backdrop-blur-xl flex flex-col">
        <div className="p-4 border-b border-border space-y-2">
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
                    <div key={item.id} className="group flex items-center justify-between p-2 rounded-md hover:bg-muted/30 cursor-pointer border border-transparent hover:border-border transition-all" onClick={() => onSelectTicker(item.ticker)}>
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
