import { useState, useEffect, useRef, useCallback } from "react";
import type { Market } from "@/types";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2, Search, ArrowRight } from "lucide-react";
import { PresetSelector, type AnalysisMode } from "@/components/PresetSelector";

interface Props {
  onAnalyze: (ticker: string, market: Market) => void;
  isLoading: boolean;
  analysisMode: AnalysisMode;
  onModeChange: (mode: AnalysisMode) => void;
}

interface StockSuggestion {
  symbol: string;
  name: string;
  exchange: string;
}

export function TickerInput({ onAnalyze, isLoading, analysisMode, onModeChange }: Props) {
  const [ticker, setTicker] = useState("");
  const [market, setMarket] = useState<Market>("US");
  const [isFocused, setIsFocused] = useState(false);
  const [suggestions, setSuggestions] = useState<StockSuggestion[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [showDropdown, setShowDropdown] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Debounced search
  useEffect(() => {
    if (!ticker.trim() || ticker.length < 1) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(async () => {
      setIsSearching(true);
      try {
        const response = await fetch(
          `/api/stocks/search?q=${encodeURIComponent(ticker)}&market=${market}`,
          { signal: controller.signal }
        );
        if (response.ok) {
          const data = await response.json();
          setSuggestions(data);
          setShowDropdown(data.length > 0);
          setSelectedIndex(-1);
        }
      } catch (e) {
        if (!(e instanceof Error && e.name === "AbortError")) {
          console.error("Search failed:", e);
        }
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => {
      clearTimeout(timeoutId);
      controller.abort();
    };
  }, [ticker, market]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const selectSuggestion = useCallback((suggestion: StockSuggestion) => {
    setTicker(suggestion.symbol);
    setShowDropdown(false);
    setSuggestions([]);
    inputRef.current?.focus();
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showDropdown || suggestions.length === 0) return;

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case "ArrowUp":
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case "Enter":
        if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
          e.preventDefault();
          selectSuggestion(suggestions[selectedIndex]);
        }
        break;
      case "Escape":
        setShowDropdown(false);
        setSelectedIndex(-1);
        break;
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (ticker.trim()) {
      setShowDropdown(false);
      onAnalyze(ticker.trim().toUpperCase(), market);
    }
  };

  return (
    <div className="space-y-4">
      <form
        onSubmit={handleSubmit}
        className={`relative flex items-center gap-4 p-2 pl-4 rounded-2xl transition-all duration-300 border ${
          isFocused
            ? "bg-white/10 border-primary/50 shadow-[0_0_30px_rgba(var(--primary),0.2)]"
            : "bg-white/5 border-border hover:bg-white/10 hover:border-white/20"
        }`}
      >
      <Search
        className={`w-5 h-5 transition-colors ${isFocused ? "text-primary" : "text-muted-foreground"}`}
      />

      <div className="flex-1 relative">
        <input
          ref={inputRef}
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          onFocus={() => {
            setIsFocused(true);
            if (suggestions.length > 0) setShowDropdown(true);
          }}
          onBlur={() => setIsFocused(false)}
          onKeyDown={handleKeyDown}
          placeholder="ENTER TICKER..."
          className="w-full bg-transparent border-none focus:ring-0 text-xl font-mono tracking-wider placeholder:text-muted-foreground/70 text-foreground py-2 uppercase"
          autoComplete="off"
        />

        {/* Autocomplete Dropdown */}
        {showDropdown && (
          <div
            ref={dropdownRef}
            className="absolute top-full left-0 right-0 mt-2 bg-popover border border-border rounded-xl shadow-2xl overflow-hidden z-50"
          >
            {isSearching && suggestions.length === 0 ? (
              <div className="px-4 py-3 text-muted-foreground text-sm flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Searching...
              </div>
            ) : (
              suggestions.map((suggestion, index) => (
                <button
                  key={suggestion.symbol}
                  type="button"
                  onClick={() => selectSuggestion(suggestion)}
                  className={`w-full px-4 py-3 flex items-center gap-3 text-left transition-colors ${
                    index === selectedIndex
                      ? "bg-primary/20 text-primary"
                      : "hover:bg-white/5 text-foreground"
                  }`}
                >
                  <span className="font-mono font-bold text-lg tracking-wider">
                    {suggestion.symbol}
                  </span>
                  <span className="text-muted-foreground text-sm truncate flex-1">
                    {suggestion.name}
                  </span>
                  <span className="text-xs text-muted-foreground/50 uppercase">
                    {suggestion.exchange}
                  </span>
                </button>
              ))
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <div className="h-8 w-px bg-white/10 hidden sm:block" />

        <Select value={market} onValueChange={(v) => setMarket(v as Market)}>
          <SelectTrigger className="w-auto gap-2 bg-transparent border-none focus:ring-0 text-muted-foreground hover:text-foreground transition-colors font-medium">
            <span className="text-xs font-bold text-muted-foreground/50 uppercase tracking-wider">
              Market
            </span>
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-popover border-border text-foreground">
            <SelectItem
              value="US"
              className="focus:bg-primary/20 focus:text-primary cursor-pointer"
            >
              US Market
            </SelectItem>
            <SelectItem
              value="TASE"
              className="focus:bg-primary/20 focus:text-primary cursor-pointer"
            >
              Tel Aviv
            </SelectItem>
          </SelectContent>
        </Select>

        <Button
          type="submit"
          disabled={isLoading || !ticker.trim()}
          size="icon"
          className={`h-12 w-12 rounded-xl transition-all duration-300 ${
            ticker.trim()
              ? "bg-primary text-primary-foreground hover:bg-primary/90 shadow-[0_0_20px_rgba(var(--primary),0.4)]"
              : "bg-white/5 text-muted-foreground hover:bg-white/10"
          }`}
        >
          {isLoading ? (
            <Loader2 className="h-6 w-6 animate-spin" />
          ) : (
            <ArrowRight className="h-6 w-6" />
          )}
        </Button>
      </div>
    </form>

    {/* Analysis Mode Selector */}
    <div className="flex justify-center">
      <PresetSelector
        value={analysisMode}
        onChange={onModeChange}
        disabled={isLoading}
      />
    </div>
  </div>
  );
}
