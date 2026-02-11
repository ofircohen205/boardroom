/**
 * Strategies page for managing trading strategies.
 */

import { PageContainer } from "@/components/layout/PageContainer";
import { StrategyForm } from "@/components/strategies/StrategyForm";
import { Button } from "@/components/ui/button";
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
import type { Strategy, StrategyCreate } from "@/types/strategy";
import { Plus, Settings, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

export function StrategiesPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingStrategy, setEditingStrategy] = useState<Strategy | undefined>();

  useEffect(() => {
    fetchStrategies();
  }, []);

  const fetchStrategies = async () => {
    try {
      setIsLoading(true);
      const token = localStorage.getItem("token");
      const response = await fetch("http://localhost:8000/api/strategies", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStrategies(data);
      }
    } catch (error) {
      console.error("Failed to fetch strategies:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = async (data: StrategyCreate) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch("http://localhost:8000/api/strategies", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      });

      if (response.ok) {
        await fetchStrategies();
        setIsDialogOpen(false);
      }
    } catch (error) {
      console.error("Failed to create strategy:", error);
    }
  };

  const handleUpdate = async (strategyId: string, data: StrategyCreate) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(
        `http://localhost:8000/api/strategies/${strategyId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(data),
        }
      );

      if (response.ok) {
        await fetchStrategies();
        setIsDialogOpen(false);
        setEditingStrategy(undefined);
      }
    } catch (error) {
      console.error("Failed to update strategy:", error);
    }
  };

  const handleDelete = async (strategyId: string) => {
    if (!confirm("Are you sure you want to delete this strategy?")) {
      return;
    }

    try {
      const token = localStorage.getItem("token");
      const response = await fetch(
        `http://localhost:8000/api/strategies/${strategyId}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        await fetchStrategies();
      }
    } catch (error) {
      console.error("Failed to delete strategy:", error);
    }
  };

  const openCreateDialog = () => {
    setEditingStrategy(undefined);
    setIsDialogOpen(true);
  };

  const openEditDialog = (strategy: Strategy) => {
    setEditingStrategy(strategy);
    setIsDialogOpen(true);
  };

  return (
    <PageContainer>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Trading Strategies</h1>
            <p className="text-muted-foreground">
              Configure custom agent weights and risk parameters
            </p>
          </div>
          <Button onClick={openCreateDialog}>
            <Plus className="mr-2 h-4 w-4" />
            New Strategy
          </Button>
        </div>

        {/* Strategies List */}
        {isLoading ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground">Loading strategies...</p>
          </div>
        ) : strategies.length === 0 ? (
          <Card>
            <CardContent className="py-12">
              <div className="text-center space-y-4">
                <Settings className="mx-auto h-12 w-12 text-muted-foreground" />
                <div>
                  <h3 className="font-semibold text-lg">No strategies yet</h3>
                  <p className="text-sm text-muted-foreground">
                    Create your first strategy to start backtesting and paper trading
                  </p>
                </div>
                <Button onClick={openCreateDialog}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Strategy
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {strategies.map((strategy) => (
              <Card key={strategy.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle>{strategy.name}</CardTitle>
                      {strategy.description && (
                        <CardDescription className="mt-1.5">
                          {strategy.description}
                        </CardDescription>
                      )}
                    </div>
                    {!strategy.is_active && (
                      <span className="text-xs bg-muted px-2 py-1 rounded">
                        Inactive
                      </span>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Agent Weights */}
                  <div className="space-y-2">
                    <p className="text-sm font-medium">Agent Weights</p>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Fundamental:</span>
                        <span className="font-medium tabular-nums">
                          {(strategy.config.weights.fundamental * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Technical:</span>
                        <span className="font-medium tabular-nums">
                          {(strategy.config.weights.technical * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Sentiment:</span>
                        <span className="font-medium tabular-nums">
                          {(strategy.config.weights.sentiment * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Thresholds */}
                  <div className="space-y-2">
                    <p className="text-sm font-medium">Thresholds</p>
                    <div className="flex gap-4 text-sm">
                      <div className="flex items-center gap-1">
                        <span className="text-muted-foreground">Buy:</span>
                        <span className="font-medium tabular-nums">
                          {strategy.config.thresholds.buy}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-muted-foreground">Sell:</span>
                        <span className="font-medium tabular-nums">
                          {strategy.config.thresholds.sell}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 pt-2">
                    <Button
                      size="sm"
                      variant="outline"
                      className="flex-1"
                      onClick={() => openEditDialog(strategy)}
                    >
                      <Settings className="mr-2 h-4 w-4" />
                      Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDelete(strategy.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Create/Edit Dialog */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingStrategy ? "Edit Strategy" : "Create New Strategy"}
              </DialogTitle>
              <DialogDescription>
                Configure agent weights and risk parameters for your trading strategy
              </DialogDescription>
            </DialogHeader>
            <StrategyForm
              strategy={editingStrategy}
              onSubmit={(data) =>
                editingStrategy
                  ? handleUpdate(editingStrategy.id, data)
                  : handleCreate(data)
              }
              onCancel={() => {
                setIsDialogOpen(false);
                setEditingStrategy(undefined);
              }}
            />
          </DialogContent>
        </Dialog>
      </div>
    </PageContainer>
  );
}
