import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ArrowLeft,
  Loader2,
  Trophy,
  BarChart3,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { ComparisonResult, Sector } from "@/types/comparison";
import { RelativePerformanceChart } from "@/components/RelativePerformanceChart";
import { ComparisonTable } from "@/components/ComparisonTable";

export function ComparePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [mode, setMode] = useState<"manual" | "sector">("manual");
  const [tickers, setTickers] = useState<string[]>([]);
  const [currentTicker, setCurrentTicker] = useState("");
  const [selectedSector, setSelectedSector] = useState<string>("");
  const [sectors, setSectors] = useState<Sector[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Pre-fill tickers from URL query parameters
  useEffect(() => {
    const singleTicker = searchParams.get('ticker');
    const multipleTickers = searchParams.get('tickers');

    if (multipleTickers) {
      const tickerList = multipleTickers.split(',').map(t => t.trim().toUpperCase()).filter(Boolean);
      if (tickerList.length > 0) {
        setTickers(tickerList.slice(0, 4)); // Max 4 tickers
      }
    } else if (singleTicker) {
      const upperTicker = singleTicker.toUpperCase();
      if (!tickers.includes(upperTicker)) {
        setTickers([upperTicker]);
      }
    }
  }, [searchParams]);

  // Fetch available sectors
  useEffect(() => {
    fetch("/api/compare/sectors")
      .then((res) => res.json())
      .then((data) => setSectors(data.sectors || []))
      .catch(console.error);
  }, []);

  const addTicker = () => {
    const ticker = currentTicker.trim().toUpperCase();
    if (ticker && !tickers.includes(ticker) && tickers.length < 4) {
      setTickers([...tickers, ticker]);
      setCurrentTicker("");
    }
  };

  const removeTicker = (ticker: string) => {
    setTickers(tickers.filter((t) => t !== ticker));
  };

  const runComparison = async () => {
    if (mode === "manual" && tickers.length < 2) {
      setError("Please add at least 2 tickers to compare");
      return;
    }

    if (mode === "sector" && !selectedSector) {
      setError("Please select a sector");
      return;
    }

    setIsLoading(true);
    setError(null);
    setComparison(null);

    try {
      const endpoint =
        mode === "manual" ? "/api/compare/stocks" : "/api/compare/sector";

      const body =
        mode === "manual"
          ? { tickers, market: "US" }
          : { sector: selectedSector, limit: 5, market: "US" };

      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error("Comparison failed");
      }

      const result = await response.json();
      setComparison(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Comparison failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate("/")}
              className="gap-2 mb-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Dashboard
            </Button>
            <h1 className="text-4xl font-black tracking-tight">
              Comparative Analysis
            </h1>
            <p className="text-muted-foreground mt-1">
              Compare multiple stocks side-by-side or analyze an entire sector
            </p>
          </div>
        </div>

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
                  variant={mode === "manual" ? "default" : "outline"}
                  onClick={() => setMode("manual")}
                  className="flex-1"
                >
                  Manual Selection
                </Button>
                <Button
                  variant={mode === "sector" ? "default" : "outline"}
                  onClick={() => setMode("sector")}
                  className="flex-1"
                >
                  Sector Analysis
                </Button>
              </div>

              {mode === "manual" ? (
                <div className="space-y-4">
                  {/* Ticker Input */}
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={currentTicker}
                      onChange={(e) => setCurrentTicker(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && addTicker()}
                      placeholder="Enter ticker (e.g., AAPL)"
                      className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
                      maxLength={10}
                    />
                    <Button
                      onClick={addTicker}
                      disabled={!currentTicker.trim() || tickers.length >= 4}
                    >
                      Add
                    </Button>
                  </div>

                  {/* Ticker Chips */}
                  {tickers.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {tickers.map((ticker) => (
                        <Badge
                          key={ticker}
                          variant="outline"
                          className="gap-2 px-3 py-1 text-sm"
                        >
                          {ticker}
                          <button
                            onClick={() => removeTicker(ticker)}
                            className="hover:text-destructive"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </Badge>
                      ))}
                    </div>
                  )}

                  <p className="text-xs text-muted-foreground">
                    Add 2-4 tickers to compare
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  <Select value={selectedSector} onValueChange={setSelectedSector}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a sector" />
                    </SelectTrigger>
                    <SelectContent>
                      {sectors.map((sector) => (
                        <SelectItem key={sector.key} value={sector.key}>
                          {sector.name} ({sector.ticker_count} stocks)
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    Analyzes top 5 stocks in the selected sector
                  </p>
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
                  isLoading ||
                  (mode === "manual" && tickers.length < 2) ||
                  (mode === "sector" && !selectedSector)
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
                <div className="text-3xl font-bold text-primary mb-2">
                  {comparison.best_pick}
                </div>
                <p className="text-muted-foreground">
                  {comparison.comparison_summary}
                </p>
              </CardContent>
            </Card>

            {/* Price History Chart */}
            {comparison.price_histories &&
              Object.keys(comparison.price_histories).length > 0 && (
                <Card className="glass">
                  <CardHeader>
                    <CardTitle>Price Performance Comparison</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <RelativePerformanceChart
                      data={comparison.price_histories}
                    />
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
                      "p-4 rounded-lg border transition-colors",
                      ranking.rank === 1
                        ? "bg-primary/10 border-primary/30"
                        : "bg-white/5 border-white/10"
                    )}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div
                          className={cn(
                            "flex items-center justify-center w-8 h-8 rounded-full font-bold",
                            ranking.rank === 1
                              ? "bg-yellow-500/20 text-yellow-500"
                              : "bg-white/10 text-muted-foreground"
                          )}
                        >
                          {ranking.rank}
                        </div>
                        <div>
                          <div className="font-mono font-bold text-lg">
                            {ranking.ticker}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            Score: {ranking.score.toFixed(1)}
                          </div>
                        </div>
                      </div>
                      <Badge
                        variant="outline"
                        className={cn(
                          ranking.decision.action === "BUY" &&
                            "bg-success/10 text-success border-success/20",
                          ranking.decision.action === "SELL" &&
                            "bg-destructive/10 text-destructive border-destructive/20",
                          ranking.decision.action === "HOLD" &&
                            "bg-warning/10 text-warning border-warning/20"
                        )}
                      >
                        {ranking.decision.action}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {ranking.rationale}
                    </p>
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
                  <ComparisonTable data={comparison.stock_data} />
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
                    {Object.entries(
                      comparison.relative_strength.relative_performance
                    ).map(([ticker, performance]) => (
                      <div
                        key={ticker}
                        className="bg-white/5 rounded-lg p-4 border border-white/10"
                      >
                        <div className="font-mono font-bold mb-1">{ticker}</div>
                        <div
                          className={cn(
                            "text-2xl font-bold",
                            performance > 0 ? "text-success" : "text-destructive"
                          )}
                        >
                          {performance > 0 ? "+" : ""}
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
                setSelectedSector("");
              }}
              variant="outline"
              className="w-full"
            >
              New Comparison
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
