/**
 * Paper trading page for virtual trading practice.
 */

import PageContainer from "@/components/layout/PageContainer";
import { Button } from "@/components/ui/button";
import { API_BASE_URL } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { PaperAccount, PaperAccountCreate, PaperTradeRequest } from "@/types/paper";
import type { Strategy } from "@/types/strategy";
import { ArrowDownIcon, ArrowUpIcon, Plus, TrendingUp, Wallet } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

export function PaperTradingPage() {
  const [accounts, setAccounts] = useState<PaperAccount[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<PaperAccount | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isTradeDialogOpen, setIsTradeDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const fetchAccounts = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API_BASE_URL}/api/paper/accounts`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setAccounts(data);
        if (data.length > 0 && !selectedAccount) {
          setSelectedAccount(data[0]);
        }
      }
    } catch (error) {
      console.error("Failed to fetch accounts:", error);
    } finally {
      setIsLoading(false);
    }
  }, [selectedAccount]);

  const fetchStrategies = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API_BASE_URL}/api/strategies`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setStrategies(data);
      }
    } catch (error) {
      console.error("Failed to fetch strategies:", error);
    }
  }, []);

  useEffect(() => {
    fetchAccounts();
    fetchStrategies();
  }, [fetchAccounts, fetchStrategies]);

  const fetchAccountDetails = useCallback(async (accountId: string) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(
        `${API_BASE_URL}/api/paper/accounts/${accountId}?include_positions=true`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (response.ok) {
        const data = await response.json();
        setSelectedAccount(data);
        // Update in list
        setAccounts((prev) =>
          prev.map((acc) => (acc.id === accountId ? data : acc))
        );
      }
    } catch (error) {
      console.error("Failed to fetch account details:", error);
    }
  }, []);

  useEffect(() => {
    if (selectedAccount) {
      fetchAccountDetails(selectedAccount.id);
    }
  }, [selectedAccount, fetchAccountDetails]);

  const handleCreateAccount = async (data: PaperAccountCreate) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${API_BASE_URL}/api/paper/accounts`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      });
      if (response.ok) {
        await fetchAccounts();
        setIsCreateDialogOpen(false);
      }
    } catch (error) {
      console.error("Failed to create account:", error);
    }
  };

  const handleExecuteTrade = async (data: PaperTradeRequest) => {
    if (!selectedAccount) return;

    try {
      const token = localStorage.getItem("token");
      const response = await fetch(
        `${API_BASE_URL}/api/paper/accounts/${selectedAccount.id}/trades`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(data),
        }
      );
      if (response.ok) {
        await fetchAccountDetails(selectedAccount.id);
        setIsTradeDialogOpen(false);
      }
    } catch (error) {
      console.error("Failed to execute trade:", error);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(value);
  };

  const formatPercent = (value: number) => {
    const formatted = (value * 100).toFixed(2);
    return `${value >= 0 ? "+" : ""}${formatted}%`;
  };

  if (isLoading) {
    return (
      <PageContainer>
        <div className="text-center py-12">
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Paper Trading</h1>
            <p className="text-muted-foreground">
              Practice trading with virtual money
            </p>
          </div>
          <Button onClick={() => setIsCreateDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Account
          </Button>
        </div>

        {accounts.length === 0 ? (
          <Card>
            <CardContent className="py-12">
              <div className="text-center space-y-4">
                <Wallet className="mx-auto h-12 w-12 text-muted-foreground" />
                <div>
                  <h3 className="font-semibold text-lg">No paper accounts yet</h3>
                  <p className="text-sm text-muted-foreground">
                    Create your first paper trading account to start practicing
                  </p>
                </div>
                <Button onClick={() => setIsCreateDialogOpen(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Account
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Account Selector */}
            <Card>
              <CardHeader>
                <CardTitle>Select Account</CardTitle>
              </CardHeader>
              <CardContent>
                <Select
                  value={selectedAccount?.id || ""}
                  onValueChange={(value) => {
                    const account = accounts.find((a) => a.id === value);
                    if (account) setSelectedAccount(account);
                  }}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {accounts.map((account) => (
                      <SelectItem key={account.id} value={account.id}>
                        {account.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </CardContent>
            </Card>

            {selectedAccount && (
              <>
                {/* Account Overview */}
                <div className="grid gap-4 md:grid-cols-4">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium">
                        Total Value
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold tabular-nums">
                        {formatCurrency(selectedAccount.total_value || selectedAccount.current_balance)}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium">Cash</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold tabular-nums">
                        {formatCurrency(selectedAccount.current_balance)}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium">P&L</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div
                        className={`text-2xl font-bold tabular-nums ${
                          (selectedAccount.total_pnl || 0) >= 0
                            ? "text-green-600 dark:text-green-400"
                            : "text-red-600 dark:text-red-400"
                        }`}
                      >
                        {formatCurrency(selectedAccount.total_pnl || 0)}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium">Return</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div
                        className={`text-2xl font-bold tabular-nums ${
                          (selectedAccount.total_pnl_pct || 0) >= 0
                            ? "text-green-600 dark:text-green-400"
                            : "text-red-600 dark:text-red-400"
                        }`}
                      >
                        {formatPercent(selectedAccount.total_pnl_pct || 0)}
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Positions */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle>Positions</CardTitle>
                        <CardDescription>Current open positions</CardDescription>
                      </div>
                      <Button onClick={() => setIsTradeDialogOpen(true)}>
                        <TrendingUp className="mr-2 h-4 w-4" />
                        Execute Trade
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {selectedAccount.positions && selectedAccount.positions.length > 0 ? (
                      <div className="rounded-md border">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Ticker</TableHead>
                              <TableHead className="text-right">Quantity</TableHead>
                              <TableHead className="text-right">Avg Entry</TableHead>
                              <TableHead className="text-right">Current</TableHead>
                              <TableHead className="text-right">Value</TableHead>
                              <TableHead className="text-right">P&L</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {selectedAccount.positions.map((position) => (
                              <TableRow key={position.id}>
                                <TableCell className="font-medium">
                                  {position.ticker}
                                </TableCell>
                                <TableCell className="text-right tabular-nums">
                                  {position.quantity}
                                </TableCell>
                                <TableCell className="text-right tabular-nums">
                                  {formatCurrency(position.average_entry_price)}
                                </TableCell>
                                <TableCell className="text-right tabular-nums">
                                  {position.current_price
                                    ? formatCurrency(position.current_price)
                                    : "—"}
                                </TableCell>
                                <TableCell className="text-right tabular-nums">
                                  {position.market_value
                                    ? formatCurrency(position.market_value)
                                    : "—"}
                                </TableCell>
                                <TableCell className="text-right tabular-nums">
                                  <span
                                    className={
                                      (position.unrealized_pnl || 0) >= 0
                                        ? "text-green-600 dark:text-green-400"
                                        : "text-red-600 dark:text-red-400"
                                    }
                                  >
                                    {position.unrealized_pnl
                                      ? `${formatCurrency(position.unrealized_pnl)} (${formatPercent(position.unrealized_pnl_pct || 0)})`
                                      : "—"}
                                  </span>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-muted-foreground">
                        No open positions
                      </div>
                    )}
                  </CardContent>
                </Card>
              </>
            )}
          </>
        )}

        {/* Create Account Dialog */}
        <CreateAccountDialog
          open={isCreateDialogOpen}
          onOpenChange={setIsCreateDialogOpen}
          strategies={strategies}
          onSubmit={handleCreateAccount}
        />

        {/* Execute Trade Dialog */}
        {selectedAccount && (
          <ExecuteTradeDialog
            open={isTradeDialogOpen}
            onOpenChange={setIsTradeDialogOpen}
            onSubmit={handleExecuteTrade}
          />
        )}
      </div>
    </PageContainer>
  );
}

// Create Account Dialog Component
function CreateAccountDialog({
  open,
  onOpenChange,
  strategies,
  onSubmit,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  strategies: Strategy[];
  onSubmit: (data: PaperAccountCreate) => void;
}) {
  const [name, setName] = useState("");
  const [strategyId, setStrategyId] = useState("");
  const [initialBalance, setInitialBalance] = useState(10000);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ name, strategy_id: strategyId, initial_balance: initialBalance });
    setName("");
    setStrategyId("");
    setInitialBalance(10000);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Paper Account</DialogTitle>
          <DialogDescription>
            Set up a new virtual trading account
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="account-name">Account Name</Label>
            <Input
              id="account-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My Paper Account"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="strategy">Strategy</Label>
            <Select value={strategyId} onValueChange={setStrategyId} required>
              <SelectTrigger id="strategy">
                <SelectValue placeholder="Select a strategy" />
              </SelectTrigger>
              <SelectContent>
                {strategies.map((strategy) => (
                  <SelectItem key={strategy.id} value={strategy.id}>
                    {strategy.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="initial-balance">Initial Balance</Label>
            <Input
              id="initial-balance"
              type="number"
              min={100}
              step={100}
              value={initialBalance}
              onChange={(e) => setInitialBalance(Number(e.target.value))}
              required
            />
          </div>

          <div className="flex justify-end gap-3">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit">Create Account</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// Execute Trade Dialog Component
function ExecuteTradeDialog({
  open,
  onOpenChange,
  onSubmit,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: PaperTradeRequest) => void;
}) {
  const [ticker, setTicker] = useState("");
  const [tradeType, setTradeType] = useState<"BUY" | "SELL">("BUY");
  const [quantity, setQuantity] = useState(10);
  const [price, setPrice] = useState<number | undefined>();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      ticker: ticker.toUpperCase(),
      trade_type: tradeType,
      quantity,
      price,
    });
    setTicker("");
    setQuantity(10);
    setPrice(undefined);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Execute Paper Trade</DialogTitle>
          <DialogDescription>
            Buy or sell shares in your paper account
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="ticker">Ticker</Label>
            <Input
              id="ticker"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              placeholder="AAPL"
              maxLength={10}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="trade-type">Type</Label>
            <Select
              value={tradeType}
              onValueChange={(value: "BUY" | "SELL") => setTradeType(value)}
            >
              <SelectTrigger id="trade-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="BUY">
                  <div className="flex items-center gap-2">
                    <ArrowUpIcon className="h-4 w-4 text-green-600" />
                    <span>BUY</span>
                  </div>
                </SelectItem>
                <SelectItem value="SELL">
                  <div className="flex items-center gap-2">
                    <ArrowDownIcon className="h-4 w-4 text-red-600" />
                    <span>SELL</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="quantity">Quantity</Label>
            <Input
              id="quantity"
              type="number"
              min={1}
              value={quantity}
              onChange={(e) => setQuantity(Number(e.target.value))}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="price">Price (optional)</Label>
            <Input
              id="price"
              type="number"
              min={0.01}
              step={0.01}
              value={price || ""}
              onChange={(e) =>
                setPrice(e.target.value ? Number(e.target.value) : undefined)
              }
              placeholder="Uses current market price if empty"
            />
          </div>

          <div className="flex justify-end gap-3">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit">Execute Trade</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
