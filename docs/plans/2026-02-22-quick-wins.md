# Quick Wins Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement 6 remaining quick wins: light mode CSS, keyboard shortcuts modal, loading polish, mobile responsive layout, more technical indicators (MACD/Bollinger/ATR), and international market support.

**Architecture:** Mostly frontend-only changes except QW-5 (technical indicators) and QW-6 (international markets) which also touch backend. All changes are additive — no existing functionality is removed. Tasks are independent and can be committed separately.

**Tech Stack:** React 19 + TypeScript, Tailwind CSS v4, shadcn/ui, FastAPI, Python, yfinance, lightweight-charts

---

## Task 1: Fix Light Mode (QW-2)

Only `:root` dark-theme CSS variables are defined. The `ThemeProvider` toggles `.light` on `<html>` but there's no `.light` block with different colors, so toggling does nothing visually.

**Files:**
- Modify: `frontend/src/index.css`

**Step 1: Add the `.light` CSS block**

In `frontend/src/index.css`, after the closing `}` of the `:root` block (around line 162), add:

```css
/* Light theme */
.light {
  --background: oklch(0.98 0.005 265);
  --foreground: oklch(0.1 0.02 265);

  --card: oklch(1 0 0 / 0.8);
  --card-foreground: oklch(0.1 0.02 265);

  --popover: oklch(0.98 0.005 265 / 0.95);
  --popover-foreground: oklch(0.1 0.02 265);

  --primary: oklch(0.55 0.22 265);
  --primary-foreground: oklch(0.98 0 0);

  --secondary: oklch(0.92 0.02 265);
  --secondary-foreground: oklch(0.2 0.05 265);

  --muted: oklch(0.93 0.01 265);
  --muted-foreground: oklch(0.45 0.03 265);

  --accent: oklch(0.55 0.22 265);
  --accent-foreground: oklch(0.98 0 0);

  --destructive: oklch(0.55 0.2 20);
  --destructive-foreground: oklch(0.98 0 0);

  --border: oklch(0.85 0.02 265);
  --input: oklch(0.92 0.01 265);
  --ring: oklch(0.55 0.22 265);

  --chart-1: oklch(0.55 0.22 265);
  --chart-2: oklch(0.5 0.18 180);
  --chart-3: oklch(0.5 0.15 300);
  --chart-4: oklch(0.6 0.15 80);
  --chart-5: oklch(0.55 0.18 340);

  --success: oklch(0.5 0.18 150);
  --success-foreground: oklch(0.98 0 0);

  --warning: oklch(0.65 0.15 80);
  --warning-foreground: oklch(0.1 0 0);
}
```

**Step 2: Fix the `.glass` utility for light mode**

In `index.css`, find the `.glass` utility and update it:

```css
.glass {
  @apply bg-card backdrop-blur-md border border-border shadow-xl;
}
```

(Change `border-white/10` → `border-border` so it uses the theme variable.)

**Step 3: Fix `TickerInput` autocomplete dropdown background**

The dropdown uses hardcoded `bg-[#0a0a0f]` which is invisible in light mode. In `frontend/src/components/TickerInput.tsx`, find both occurrences of `bg-[#0a0a0f]` and replace with `bg-popover`:

```tsx
// autocomplete dropdown
className="absolute top-full left-0 right-0 mt-2 bg-popover border border-border rounded-xl shadow-2xl overflow-hidden z-50"

// SelectContent
<SelectContent className="bg-popover border-border text-foreground">
```

**Step 4: Verify visually**

Run the frontend, toggle the theme button in the Navbar (Sun/Moon icon). Verify the background goes light, text goes dark, cards become white-ish.

**Step 5: Commit**

```bash
git add frontend/src/index.css frontend/src/components/TickerInput.tsx
git commit -m "feat: add light mode CSS theme variables"
```

---

## Task 2: Keyboard Shortcuts Modal (QW-9)

A `useKeyboardShortcuts` hook and a few shortcuts (Ctrl+K, Ctrl+H, Ctrl+B) exist in `Dashboard.tsx`. Missing: a `?` key that shows a help modal listing all shortcuts.

**Files:**
- Create: `frontend/src/components/ShortcutsModal.tsx`
- Modify: `frontend/src/components/Dashboard.tsx`

**Step 1: Create `ShortcutsModal.tsx`**

```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";

interface Shortcut {
  keys: string[];
  description: string;
}

const SHORTCUTS: Shortcut[] = [
  { keys: ["Ctrl", "K"], description: "Focus ticker search" },
  { keys: ["Ctrl", "H"], description: "Toggle analysis history" },
  { keys: ["Ctrl", "B"], description: "Toggle watchlist sidebar" },
  { keys: ["Enter"], description: "Run analysis" },
  { keys: ["Escape"], description: "Close history / dismiss" },
  { keys: ["?"], description: "Show this help" },
];

interface Props {
  open: boolean;
  onClose: () => void;
}

export function ShortcutsModal({ open, onClose }: Props) {
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle className="text-sm font-bold uppercase tracking-widest text-muted-foreground">
            Keyboard Shortcuts
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-2 py-2">
          {SHORTCUTS.map((shortcut) => (
            <div key={shortcut.description} className="flex items-center justify-between gap-4">
              <span className="text-sm text-muted-foreground">{shortcut.description}</span>
              <div className="flex items-center gap-1 shrink-0">
                {shortcut.keys.map((key) => (
                  <Badge
                    key={key}
                    variant="outline"
                    className="font-mono text-xs px-1.5 py-0.5 border-border"
                  >
                    {key}
                  </Badge>
                ))}
              </div>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

**Step 2: Wire into `Dashboard.tsx`**

Add import at top:
```tsx
import { ShortcutsModal } from "@/components/ShortcutsModal";
import { Keyboard } from "lucide-react";
```

Add state:
```tsx
const [showShortcuts, setShowShortcuts] = useState(false);
```

Add `?` to the `useKeyboardShortcuts` call:
```tsx
useKeyboardShortcuts({
  'Ctrl+k': () => searchInputRef.current?.focus(),
  'Ctrl+h': () => setShowHistory(!showHistory),
  'Ctrl+b': () => setSidebarOpen(!sidebarOpen),
  'Escape': () => { setShowHistory(false); setShowShortcuts(false); },
  '?': () => setShowShortcuts(true),
});
```

Add a `?` button in the Dashboard header (next to the History button):
```tsx
<Button
  variant="ghost"
  size="icon"
  className="h-8 w-8"
  onClick={() => setShowShortcuts(true)}
  title="Keyboard shortcuts (?)"
>
  <Keyboard className="w-4 h-4" />
</Button>
```

Add the modal at the bottom of the return, just before the closing `</div>`:
```tsx
<ShortcutsModal open={showShortcuts} onClose={() => setShowShortcuts(false)} />
```

**Step 3: Verify**

Run frontend. Press `?` on the dashboard — a modal should appear listing all shortcuts. Press Escape to dismiss.

**Step 4: Commit**

```bash
git add frontend/src/components/ShortcutsModal.tsx frontend/src/components/Dashboard.tsx
git commit -m "feat: add keyboard shortcuts help modal"
```

---

## Task 3: Loading Polish — Agent-Specific Copy (QW-7)

Currently all agents show the same generic shimmer while loading. Add descriptive copy per agent so users know what's happening.

**Files:**
- Modify: `frontend/src/components/AgentPanel.tsx`

**Step 1: Add loading messages to `AgentPanel.tsx`**

Find the `AgentPanel` function. Add a map of per-agent loading messages near the top of the component body (before the return):

```tsx
const LOADING_MESSAGES: Record<string, string[]> = {
  fundamental: [
    "Fetching financials from Yahoo Finance...",
    "Parsing revenue, P/E ratio, and debt metrics...",
    "Running LLM fundamental analysis...",
  ],
  sentiment: [
    "Scanning news headlines and social signals...",
    "Scoring sentiment across sources...",
    "Running LLM sentiment analysis...",
  ],
  technical: [
    "Loading price history...",
    "Computing RSI, MA50, and MA200...",
    "Running LLM technical analysis...",
  ],
  risk: [
    "Assessing portfolio sector exposure...",
    "Calculating Value at Risk (VaR 95%)...",
    "Running risk veto check...",
  ],
  chairperson: [
    "Weighing all agent reports...",
    "Determining final recommendation...",
    "Drafting decision rationale...",
  ],
};
```

Replace the existing shimmer loading block (the `{isActive && !data && ( ... )}` section) with:

```tsx
{isActive && !data && (
  <div className="space-y-3 py-2">
    <div className="space-y-2">
      <div className="h-2 w-3/4 rounded-full bg-white/10 animate-pulse" />
      <div className="h-2 w-1/2 rounded-full bg-white/10 animate-pulse delay-75" />
      <div className="h-2 w-2/3 rounded-full bg-white/10 animate-pulse delay-150" />
    </div>
    <p className="text-[11px] text-muted-foreground/50 font-mono animate-pulse">
      {LOADING_MESSAGES[agent]?.[0] ?? "Analyzing..."}
    </p>
  </div>
)}
```

**Step 2: Verify**

Run an analysis. Each agent card should show its specific loading message while the shimmer plays.

**Step 3: Commit**

```bash
git add frontend/src/components/AgentPanel.tsx
git commit -m "feat: add agent-specific loading copy"
```

---

## Task 4: Mobile Responsive Layout (QW-3)

The 4-agent grid and sidebar work poorly on small screens.

**Files:**
- Modify: `frontend/src/components/Dashboard.tsx`

**Step 1: Fix the sidebar behavior on mobile**

The sidebar currently takes up `w-80` even on mobile, squishing content. Replace the sidebar wrapper `div` with a version that overlays on mobile:

Find:
```tsx
<div className={cn(
    "transition-all duration-300 border-r border-white/10 bg-card/10 backdrop-blur-xl",
    sidebarOpen ? "w-80" : "w-0 overflow-hidden"
)}>
    <WatchlistSidebar onSelectTicker={handleTickerSelect} />
</div>
```

Replace with:
```tsx
{/* Overlay backdrop on mobile */}
{sidebarOpen && (
  <div
    className="fixed inset-0 bg-black/50 z-30 md:hidden"
    onClick={() => setSidebarOpen(false)}
  />
)}

{/* Sidebar - overlay on mobile, inline on desktop */}
<div className={cn(
    "transition-all duration-300 border-r border-white/10 bg-card/10 backdrop-blur-xl",
    "fixed md:relative z-40 md:z-auto h-full",
    sidebarOpen ? "w-80 translate-x-0" : "w-80 -translate-x-full md:w-0 md:overflow-hidden md:translate-x-0"
)}>
    <WatchlistSidebar onSelectTicker={handleTickerSelect} />
</div>
```

**Step 2: Fix the agent grid breakpoints**

Find:
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
```

This is already correct! Verify it renders as 1-col on small screens. If `AgentPanel` content overflows, add `min-w-0` to the grid:

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 min-w-0">
```

**Step 3: Fix the hero title on small screens**

Find the `text-5xl sm:text-7xl` heading. This is fine. But add `px-4` guard on the hero section wrapper if missing:

Find:
```tsx
<div className="mb-10 space-y-4">
```

Change to:
```tsx
<div className="mb-10 space-y-4 px-4">
```

**Step 4: Verify on mobile viewport**

In browser DevTools, set viewport to 390px (iPhone 14). Verify:
- The menu button opens the sidebar as an overlay (not inline)
- The overlay backdrop dismisses it on tap
- The 4 agent cards stack vertically (1-col)
- The hero title is readable and doesn't overflow

**Step 5: Commit**

```bash
git add frontend/src/components/Dashboard.tsx
git commit -m "feat: improve mobile responsive layout (overlay sidebar, grid breakpoints)"
```

---

## Task 5: More Technical Indicators — MACD, Bollinger Bands, ATR (QW-5)

Add MACD, Bollinger Bands, and ATR calculations to the backend, include them in `TechnicalReport`, and display them in the frontend.

### 5a: Backend — Add calculations

**Files:**
- Modify: `backend/shared/ai/tools/technical_indicators.py`

**Step 1: Add MACD calculation**

Append to `technical_indicators.py`:

```python
def calculate_macd(
    prices: list[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict[str, float]:
    """Returns MACD line, signal line, and histogram values."""
    if len(prices) < slow + signal:
        return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}

    def _ema(data: list[float], period: int) -> list[float]:
        k = 2 / (period + 1)
        ema = [data[0]]
        for price in data[1:]:
            ema.append(price * k + ema[-1] * (1 - k))
        return ema

    ema_fast = _ema(prices, fast)
    ema_slow = _ema(prices, slow)

    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    macd_signal = _ema(macd_line[slow - 1:], signal)
    histogram = macd_line[-1] - macd_signal[-1]

    return {
        "macd": round(macd_line[-1], 4),
        "signal": round(macd_signal[-1], 4),
        "histogram": round(histogram, 4),
    }


def calculate_bollinger_bands(
    prices: list[float], period: int = 20, std_dev: float = 2.0
) -> dict[str, float]:
    """Returns upper band, middle band (SMA), lower band, and band width %."""
    if len(prices) < period:
        price = prices[-1] if prices else 0.0
        return {"upper": price, "middle": price, "lower": price, "width_pct": 0.0}

    window = prices[-period:]
    middle = sum(window) / period
    variance = sum((p - middle) ** 2 for p in window) / period
    std = variance ** 0.5
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    width_pct = ((upper - lower) / middle * 100) if middle else 0.0

    return {
        "upper": round(upper, 4),
        "middle": round(middle, 4),
        "lower": round(lower, 4),
        "width_pct": round(width_pct, 2),
    }


def calculate_atr(
    price_history: list[dict], period: int = 14
) -> float:
    """Average True Range — measures volatility. Expects dicts with high/low/close keys."""
    if len(price_history) < 2:
        return 0.0

    true_ranges = []
    for i in range(1, len(price_history)):
        high = price_history[i]["high"]
        low = price_history[i]["low"]
        prev_close = price_history[i - 1]["close"]
        true_range = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(true_range)

    recent = true_ranges[-period:]
    return round(sum(recent) / len(recent), 4)
```

**Step 2: Write unit tests for the new calculations**

Create test cases in `tests/unit/test_tools.py` (or find the existing file):

```python
from backend.shared.ai.tools.technical_indicators import (
    calculate_macd,
    calculate_bollinger_bands,
    calculate_atr,
)


def test_calculate_macd_returns_all_keys():
    prices = list(range(1, 50))  # 49 prices
    result = calculate_macd(prices)
    assert "macd" in result
    assert "signal" in result
    assert "histogram" in result


def test_calculate_macd_insufficient_data_returns_zeros():
    result = calculate_macd([100.0, 101.0])
    assert result == {"macd": 0.0, "signal": 0.0, "histogram": 0.0}


def test_calculate_bollinger_bands_returns_all_keys():
    prices = [100.0 + i for i in range(25)]
    result = calculate_bollinger_bands(prices)
    assert "upper" in result and "lower" in result and "middle" in result
    assert result["upper"] > result["middle"] > result["lower"]


def test_calculate_bollinger_bands_insufficient_data():
    result = calculate_bollinger_bands([100.0])
    assert result["upper"] == result["middle"] == result["lower"] == 100.0


def test_calculate_atr_returns_float():
    history = [
        {"high": 105.0, "low": 98.0, "close": 102.0},
        {"high": 107.0, "low": 100.0, "close": 104.0},
        {"high": 103.0, "low": 97.0, "close": 100.0},
    ]
    result = calculate_atr(history)
    assert isinstance(result, float)
    assert result > 0


def test_calculate_atr_insufficient_data():
    result = calculate_atr([{"high": 100.0, "low": 98.0, "close": 99.0}])
    assert result == 0.0
```

**Step 3: Run the tests**

```bash
uv run pytest tests/unit/test_tools.py -k "macd or bollinger or atr" -v
```

Expected: All 6 tests PASS.

**Step 4: Extend `TechnicalReport` in `agent_state.py`**

Add 3 optional fields to `TechnicalReport`:

```python
class TechnicalReport(TypedDict):
    current_price: float
    ma_50: float
    ma_200: float
    rsi: float
    trend: Trend
    price_history: list[dict]
    summary: str
    # New indicators
    macd: Optional[float]
    macd_signal: Optional[float]
    macd_histogram: Optional[float]
    bollinger_upper: Optional[float]
    bollinger_lower: Optional[float]
    bollinger_width_pct: Optional[float]
    atr: Optional[float]
```

**Step 5: Update `technical.py` agent to compute and include new indicators**

```python
from backend.shared.ai.tools.technical_indicators import (
    calculate_ma,
    calculate_rsi,
    calculate_trend,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_atr,
)

async def analyze(self, ticker: str, market: Market) -> TechnicalReport:
    stock_data = await self.market_data.get_stock_data(ticker, market)

    prices = [p["close"] for p in stock_data["price_history"]]
    current_price = stock_data["current_price"]

    ma_50 = calculate_ma(prices, 50) if len(prices) >= 50 else calculate_ma(prices, len(prices))
    ma_200 = calculate_ma(prices, 200) if len(prices) >= 200 else calculate_ma(prices, len(prices))
    rsi = calculate_rsi(prices)
    trend = calculate_trend(current_price, ma_50, ma_200)
    macd_data = calculate_macd(prices)
    bb_data = calculate_bollinger_bands(prices)
    atr = calculate_atr(stock_data["price_history"])

    prompt = f"""Provide a brief technical analysis for {ticker}:
- Current Price: ${current_price:.2f}
- 50-day MA: ${ma_50:.2f}
- 200-day MA: ${ma_200:.2f}
- RSI: {rsi:.1f}
- MACD: {macd_data['macd']:.4f} (Signal: {macd_data['signal']:.4f}, Histogram: {macd_data['histogram']:.4f})
- Bollinger Bands: Upper ${bb_data['upper']:.2f} / Lower ${bb_data['lower']:.2f} (Width: {bb_data['width_pct']:.1f}%)
- ATR (14): {atr:.2f}
- Trend: {trend.value}

Summarize the technical outlook in 2-3 sentences."""

    summary = await self.llm.complete([{"role": "user", "content": prompt}])

    return TechnicalReport(
        current_price=current_price,
        ma_50=ma_50,
        ma_200=ma_200,
        rsi=rsi,
        trend=trend,
        price_history=stock_data["price_history"],
        summary=summary,
        macd=macd_data["macd"],
        macd_signal=macd_data["signal"],
        macd_histogram=macd_data["histogram"],
        bollinger_upper=bb_data["upper"],
        bollinger_lower=bb_data["lower"],
        bollinger_width_pct=bb_data["width_pct"],
        atr=atr,
    )
```

**Step 6: Run existing tests to verify nothing is broken**

```bash
uv run pytest tests/unit/ -v
```

Expected: All existing tests still pass.

**Step 7: Commit backend changes**

```bash
git add backend/shared/ai/tools/technical_indicators.py \
        backend/shared/ai/state/agent_state.py \
        backend/shared/ai/agents/technical.py \
        tests/unit/test_tools.py
git commit -m "feat: add MACD, Bollinger Bands, and ATR to technical indicators"
```

### 5b: Frontend — Display new indicators

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/components/AgentPanel.tsx`
- Modify: `frontend/src/components/StockChart.tsx`

**Step 8: Extend `TechnicalReport` TypeScript type**

In `frontend/src/types/index.ts`, add optional fields to `TechnicalReport`:

```typescript
export interface TechnicalReport {
  current_price: number;
  ma_50: number;
  ma_200: number;
  rsi: number;
  trend: Trend;
  price_history: PricePoint[];
  summary: string;
  // New indicators
  macd?: number;
  macd_signal?: number;
  macd_histogram?: number;
  bollinger_upper?: number;
  bollinger_lower?: number;
  bollinger_width_pct?: number;
  atr?: number;
}
```

**Step 9: Show new metrics in `AgentPanel.tsx`**

In the `technical` agent metrics section in `AgentPanel.tsx`, add a second row below the existing metrics grid. Find the block ending with the trend `Badge` and add after the closing `</>` of the `{agent === "technical" && (...)}` block but inside the same parent `div`:

```tsx
{agent === "technical" && data.bollinger_width_pct !== undefined && (
  <div className="grid grid-cols-3 gap-2 p-3 rounded-lg bg-black/20 border border-white/10 backdrop-blur-sm mt-2">
    <Metric
      label="MACD"
      value={data.macd?.toFixed(3) ?? "N/A"}
      positive={data.macd_histogram > 0}
      negative={data.macd_histogram < 0}
    />
    <Metric
      label="BB Width"
      value={data.bollinger_width_pct ? `${data.bollinger_width_pct.toFixed(1)}%` : "N/A"}
      warning={data.bollinger_width_pct > 10}
    />
    <Metric
      label="ATR"
      value={data.atr?.toFixed(2) ?? "N/A"}
    />
  </div>
)}
```

**Step 10: Add Bollinger Band overlay lines to `StockChart.tsx`**

Update `StockChart`'s `Props` interface to accept optional `bollingerUpper` and `bollingerLower`:

```tsx
interface Props {
  priceHistory: PricePoint[];
  ticker: string;
  ma50?: number;
  ma200?: number;
  rsi?: number;
  bollingerUpper?: number;
  bollingerLower?: number;
}
```

In the `useEffect` that builds the chart, after the MA200 overlay block, add:

```tsx
// Bollinger Upper Band overlay
if (bollingerUpper && bollingerUpper > 0) {
  const bbUpperSeries = chart.addSeries(LineSeries, {
    color: "#a78bfa50",
    lineWidth: 1,
    lineStyle: 2, // dashed
    crosshairMarkerVisible: false,
    lastValueVisible: false,
    priceLineVisible: false,
  });
  bbUpperSeries.setData(
    priceHistory.map((p) => ({ time: p.date.split("T")[0], value: bollingerUpper }))
  );
}

// Bollinger Lower Band overlay
if (bollingerLower && bollingerLower > 0) {
  const bbLowerSeries = chart.addSeries(LineSeries, {
    color: "#a78bfa50",
    lineWidth: 1,
    lineStyle: 2, // dashed
    crosshairMarkerVisible: false,
    lastValueVisible: false,
    priceLineVisible: false,
  });
  bbLowerSeries.setData(
    priceHistory.map((p) => ({ time: p.date.split("T")[0], value: bollingerLower }))
  );
}
```

Update the `useEffect` dependency array to include `bollingerUpper` and `bollingerLower`.

Add Bollinger to the legend section:

```tsx
{(ma50 || ma200 || bollingerUpper) && (
  <div className="px-4 py-2 border-t border-white/5 flex flex-wrap gap-4 text-[10px] font-mono">
    {ma50 && ma50 > 0 && (
      <div className="flex items-center gap-1.5">
        <div className="h-[2px] w-3 bg-[#fbbf24]" />
        <span className="text-muted-foreground">MA50: ${ma50.toFixed(2)}</span>
      </div>
    )}
    {ma200 && ma200 > 0 && (
      <div className="flex items-center gap-1.5">
        <div className="h-[2px] w-3 bg-[#3b82f6]" />
        <span className="text-muted-foreground">MA200: ${ma200.toFixed(2)}</span>
      </div>
    )}
    {bollingerUpper && bollingerUpper > 0 && (
      <div className="flex items-center gap-1.5">
        <div className="h-[2px] w-3 bg-[#a78bfa] border-dashed" />
        <span className="text-muted-foreground">BB Bands</span>
      </div>
    )}
  </div>
)}
```

**Step 11: Pass new props from `Dashboard.tsx`**

In `Dashboard.tsx`, update the `<StockChart>` call to pass the new props:

```tsx
<StockChart
  priceHistory={state.technical.price_history}
  ticker={state.ticker!}
  ma50={state.technical.ma_50}
  ma200={state.technical.ma_200}
  rsi={state.technical.rsi}
  bollingerUpper={state.technical.bollinger_upper}
  bollingerLower={state.technical.bollinger_lower}
/>
```

**Step 12: Run a full analysis and verify**

Start the backend and frontend. Run an analysis. Verify:
- Technical agent panel shows a second row with MACD, BB Width, ATR values
- Chart shows dashed purple Bollinger Band lines when Bollinger data is available

**Step 13: Commit frontend changes**

```bash
git add frontend/src/types/index.ts \
        frontend/src/components/AgentPanel.tsx \
        frontend/src/components/StockChart.tsx \
        frontend/src/components/Dashboard.tsx
git commit -m "feat: display MACD, Bollinger Bands, and ATR in technical panel and chart"
```

---

## Task 6: International Markets — LSE, TSE, HKEX, Xetra (QW-6)

### 6a: Backend

**Files:**
- Modify: `backend/shared/ai/state/enums.py`
- Modify: `backend/shared/ai/tools/market_data.py`
- Modify: `backend/shared/ai/tools/stock_search.py`

**Step 1: Extend the `Market` enum**

In `backend/shared/ai/state/enums.py`:

```python
class Market(str, Enum):
    US = "US"
    TASE = "TASE"
    LSE = "LSE"      # London Stock Exchange
    TSE = "TSE"      # Tokyo Stock Exchange
    HKEX = "HKEX"   # Hong Kong Exchange
    XETRA = "XETRA" # Frankfurt / Deutsche Börse
```

**Step 2: Add Yahoo Finance ticker suffix mapping in `market_data.py`**

Find the `_format_ticker` method in `YahooFinanceClient`:

```python
def _format_ticker(self, ticker: str, market: Market) -> str:
    suffixes = {
        Market.TASE: ".TA",
        Market.LSE: ".L",
        Market.TSE: ".T",
        Market.HKEX: ".HK",
        Market.XETRA: ".DE",
    }
    suffix = suffixes.get(market, "")
    return f"{ticker}{suffix}" if suffix else ticker
```

**Step 3: Update `stock_search.py` to handle new markets**

Add popular stock dictionaries for the new markets and update `search_stocks`:

```python
POPULAR_LSE_STOCKS = {
    "SHEL": ("Shell plc", "LSE"),
    "AZN": ("AstraZeneca plc", "LSE"),
    "HSBA": ("HSBC Holdings plc", "LSE"),
    "BP": ("BP plc", "LSE"),
    "ULVR": ("Unilever plc", "LSE"),
    "LLOY": ("Lloyds Banking Group plc", "LSE"),
    "VOD": ("Vodafone Group plc", "LSE"),
    "RIO": ("Rio Tinto plc", "LSE"),
    "GSK": ("GSK plc", "LSE"),
    "BARC": ("Barclays plc", "LSE"),
}

POPULAR_TSE_STOCKS = {
    "7203": ("Toyota Motor Corporation", "TSE"),
    "6758": ("Sony Group Corporation", "TSE"),
    "9984": ("SoftBank Group Corp.", "TSE"),
    "6861": ("Keyence Corporation", "TSE"),
    "8306": ("Mitsubishi UFJ Financial Group", "TSE"),
    "4063": ("Shin-Etsu Chemical Co.", "TSE"),
    "6954": ("Fanuc Corporation", "TSE"),
    "9432": ("Nippon Telegraph and Telephone", "TSE"),
}

POPULAR_HKEX_STOCKS = {
    "700": ("Tencent Holdings Ltd.", "HKEX"),
    "9988": ("Alibaba Group Holding Ltd.", "HKEX"),
    "5": ("HSBC Holdings plc", "HKEX"),
    "941": ("China Mobile Ltd.", "HKEX"),
    "1299": ("AIA Group Ltd.", "HKEX"),
    "388": ("Hong Kong Exchanges and Clearing", "HKEX"),
    "2318": ("Ping An Insurance", "HKEX"),
    "1": ("CK Hutchison Holdings", "HKEX"),
}

POPULAR_XETRA_STOCKS = {
    "SAP": ("SAP SE", "XETRA"),
    "SIE": ("Siemens AG", "XETRA"),
    "ALV": ("Allianz SE", "XETRA"),
    "MUV2": ("Munich Re", "XETRA"),
    "DTE": ("Deutsche Telekom AG", "XETRA"),
    "BAYN": ("Bayer AG", "XETRA"),
    "BMW": ("Bayerische Motoren Werke AG", "XETRA"),
    "MBG": ("Mercedes-Benz Group AG", "XETRA"),
    "VOW3": ("Volkswagen AG", "XETRA"),
    "DBK": ("Deutsche Bank AG", "XETRA"),
}

MARKET_POPULAR_STOCKS = {
    Market.US: POPULAR_US_STOCKS,
    Market.TASE: POPULAR_TASE_STOCKS,
    Market.LSE: POPULAR_LSE_STOCKS,
    Market.TSE: POPULAR_TSE_STOCKS,
    Market.HKEX: POPULAR_HKEX_STOCKS,
    Market.XETRA: POPULAR_XETRA_STOCKS,
}
```

Update `search_stocks` to use the mapping and the correct ticker suffix:

```python
async def search_stocks(
    query: str, market: Market, limit: int = 8
) -> list[StockSuggestion]:
    if not query or len(query) < 1:
        return []

    MARKET_SUFFIXES = {
        Market.TASE: ".TA",
        Market.LSE: ".L",
        Market.TSE: ".T",
        Market.HKEX: ".HK",
        Market.XETRA: ".DE",
    }

    query_upper = query.upper().strip()
    results: list[StockSuggestion] = []

    popular_stocks = MARKET_POPULAR_STOCKS.get(market, POPULAR_US_STOCKS)

    for symbol, (name, exchange) in popular_stocks.items():
        if query_upper in symbol or query_upper.lower() in name.lower():
            results.append(
                StockSuggestion(symbol=symbol, name=name, exchange=exchange, market=market)
            )
            if len(results) >= limit:
                return results

    if len(results) < limit and len(query_upper) >= 1:
        try:
            suffix = MARKET_SUFFIXES.get(market, "")
            ticker_symbol = f"{query_upper}{suffix}" if suffix else query_upper

            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info

            if (info and info.get("shortName")) or info.get("longName"):
                name = info.get("shortName") or info.get("longName") or query_upper
                exchange = info.get("exchange") or market.value

                if not any(r.symbol == query_upper for r in results):
                    results.append(
                        StockSuggestion(
                            symbol=query_upper,
                            name=name,
                            exchange=exchange,
                            market=market,
                        )
                    )
        except Exception:
            pass

    return results[:limit]
```

Remove the now-unused old `POPULAR_US_STOCKS`, `POPULAR_TASE_STOCKS` references that are now in the dict. Keep them as-is (they're referenced by `MARKET_POPULAR_STOCKS`).

**Step 4: Run existing tests**

```bash
uv run pytest tests/unit/ -v
```

Expected: All pass.

**Step 5: Commit backend**

```bash
git add backend/shared/ai/state/enums.py \
        backend/shared/ai/tools/market_data.py \
        backend/shared/ai/tools/stock_search.py
git commit -m "feat: add LSE, TSE, HKEX, Xetra international market support"
```

### 6b: Frontend

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/components/TickerInput.tsx`

**Step 6: Extend the `Market` type**

In `frontend/src/types/index.ts`:

```typescript
export type Market = "US" | "TASE" | "LSE" | "TSE" | "HKEX" | "XETRA";
```

**Step 7: Update the market `Select` in `TickerInput.tsx`**

Replace the two `<SelectItem>` lines with all 6 markets:

```tsx
<SelectContent className="bg-popover border-border text-foreground">
  <SelectItem value="US" className="focus:bg-primary/20 focus:text-primary cursor-pointer">
    🇺🇸 US Market
  </SelectItem>
  <SelectItem value="TASE" className="focus:bg-primary/20 focus:text-primary cursor-pointer">
    🇮🇱 Tel Aviv
  </SelectItem>
  <SelectItem value="LSE" className="focus:bg-primary/20 focus:text-primary cursor-pointer">
    🇬🇧 London
  </SelectItem>
  <SelectItem value="TSE" className="focus:bg-primary/20 focus:text-primary cursor-pointer">
    🇯🇵 Tokyo
  </SelectItem>
  <SelectItem value="HKEX" className="focus:bg-primary/20 focus:text-primary cursor-pointer">
    🇭🇰 Hong Kong
  </SelectItem>
  <SelectItem value="XETRA" className="focus:bg-primary/20 focus:text-primary cursor-pointer">
    🇩🇪 Frankfurt
  </SelectItem>
</SelectContent>
```

**Step 8: Verify**

Start frontend. The market selector now shows 6 options with flag emojis. Selecting "London" and typing "SHEL" should auto-suggest Shell plc.

**Step 9: Commit frontend**

```bash
git add frontend/src/types/index.ts frontend/src/components/TickerInput.tsx
git commit -m "feat: add international markets to ticker input (LSE, TSE, HKEX, Xetra)"
```

---

## Summary

| Task | Files Changed | Commit |
|------|--------------|--------|
| 1: Light mode CSS | `index.css`, `TickerInput.tsx` | `feat: add light mode CSS theme variables` |
| 2: Shortcuts modal | `ShortcutsModal.tsx` (new), `Dashboard.tsx` | `feat: add keyboard shortcuts help modal` |
| 3: Loading polish | `AgentPanel.tsx` | `feat: add agent-specific loading copy` |
| 4: Mobile responsive | `Dashboard.tsx` | `feat: improve mobile responsive layout` |
| 5a: New indicators (backend) | `technical_indicators.py`, `agent_state.py`, `technical.py`, `test_tools.py` | `feat: add MACD, Bollinger Bands, and ATR to technical indicators` |
| 5b: New indicators (frontend) | `types/index.ts`, `AgentPanel.tsx`, `StockChart.tsx`, `Dashboard.tsx` | `feat: display MACD, Bollinger Bands, and ATR in technical panel and chart` |
| 6a: Int'l markets (backend) | `enums.py`, `market_data.py`, `stock_search.py` | `feat: add LSE, TSE, HKEX, Xetra international market support` |
| 6b: Int'l markets (frontend) | `types/index.ts`, `TickerInput.tsx` | `feat: add international markets to ticker input` |
