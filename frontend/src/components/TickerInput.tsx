import { useState } from "react";
import type { Market } from "../types";

interface Props {
  onAnalyze: (ticker: string, market: Market) => void;
  isLoading: boolean;
}

export function TickerInput({ onAnalyze, isLoading }: Props) {
  const [ticker, setTicker] = useState("");
  const [market, setMarket] = useState<Market>("US");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (ticker.trim()) {
      onAnalyze(ticker.trim().toUpperCase(), market);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        value={ticker}
        onChange={(e) => setTicker(e.target.value)}
        placeholder="Enter ticker (e.g., AAPL, TEVA)"
        className="w-48 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <select
        value={market}
        onChange={(e) => setMarket(e.target.value as Market)}
        className="px-3 py-2 border rounded-md"
      >
        <option value="US">US</option>
        <option value="TASE">TASE</option>
      </select>
      <button
        type="submit"
        disabled={isLoading || !ticker.trim()}
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? "Analyzing..." : "Analyze"}
      </button>
    </form>
  );
}
