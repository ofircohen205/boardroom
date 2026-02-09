# Phase 3: Comparative Analysis

## Goal

Enable users to compare multiple stocks side-by-side, analyze entire sectors, and get relative strength insights. Currently the system only analyzes one stock at a time — this phase expands to multi-stock workflows.

## Why This Matters

- Investment decisions are rarely about one stock in isolation
- "Should I buy AAPL or MSFT?" is a more common question than "Should I buy AAPL?"
- Sector analysis provides macro context that individual analysis misses
- No dependency on Phase 1 — can be built independently

## Features

### 3.1 Multi-Stock Analysis

Run the analysis pipeline on 2-4 stocks simultaneously and present results side by side.

**Backend:**
- New endpoint: `POST /api/analyze/compare`
  ```json
  {
    "tickers": ["AAPL", "MSFT", "GOOGL"],
    "market": "US"
  }
  ```
- Extend `BoardroomGraph` with a `run_comparison()` method in `backend/graph/workflow.py`:
  - Run all analyst agents for each ticker in parallel (leveraging existing `asyncio.gather` pattern)
  - Run risk assessment for each
  - Add a new **Comparison Step** after individual analyses complete:
    - Feeds all individual results to the Chairperson with a "compare and rank" prompt
    - Returns ranked list with relative strengths/weaknesses
- New WebSocket message type: `WSMessageType.COMPARISON_RESULT`
- State extension:
  ```python
  class ComparisonResult(TypedDict):
      rankings: list[dict]  # [{ticker, rank, score, rationale}]
      best_pick: str
      comparison_summary: str
  ```

**Streaming:**
- New WebSocket command: `{"type": "compare", "tickers": ["AAPL", "MSFT"]}`
- Stream individual agent completions as they finish (per ticker)
- Final comparison result streamed at the end

### 3.2 Sector Analysis

Analyze all major stocks in a given sector.

**Backend:**
- Sector-to-stocks mapping:
  - Option A: Static mapping in `backend/tools/sector_data.py` for major sectors (Tech, Healthcare, Finance, Energy, etc.) with top 5-10 stocks each
  - Option B: Dynamic lookup via Yahoo Finance sector endpoints
- New endpoint: `POST /api/analyze/sector`
  ```json
  {
    "sector": "Technology",
    "limit": 5
  }
  ```
- Runs comparison analysis on top N stocks in the sector
- Additional sector-level metrics:
  - Average P/E for sector
  - Sector sentiment aggregate
  - Sector momentum (% of stocks bullish vs bearish)

### 3.3 Relative Strength Comparison

Quantitative comparison metrics between stocks.

**Backend — new module `backend/tools/relative_strength.py`:**
- Correlation analysis: How correlated are the stocks' price movements?
- Relative performance: Normalize prices to a common start date, show who outperformed
- Risk-adjusted returns: Sharpe ratio comparison
- Valuation comparison: P/E, P/S, EV/EBITDA side by side

**Output structure:**
```python
class RelativeStrength(TypedDict):
    correlation_matrix: dict[str, dict[str, float]]
    relative_performance: dict[str, float]  # % return over period
    sharpe_ratios: dict[str, float]
    valuation_comparison: dict[str, dict[str, float]]
```

### 3.4 Frontend: Comparison View

**New page: `/compare`**

**Components:**
- `ComparisonInput` — multi-ticker input (chips-style, add up to 4 tickers)
- `ComparisonGrid` — side-by-side cards showing each stock's analysis
  - Reuse existing `AgentPanel` component with slight layout adaptation
  - Highlight winner/loser for each metric (green/red)
- `RankingCard` — shows the Chairperson's ranked comparison result
  - #1 pick highlighted prominently
  - Rationale for ranking
- `RelativePerformanceChart` — overlaid line chart showing normalized price history for all compared stocks (lightweight-charts supports multiple series)
- `ComparisonTable` — tabular view of all metrics for quick scanning:
  ```
  Metric        | AAPL   | MSFT   | GOOGL
  P/E Ratio     | 28.5   | 34.2   | 22.1  ← best
  Revenue Growth| +8.2%  | +12.1% ← best | +6.3%
  RSI           | 55     | 62     | 48
  Sentiment     | 0.72   | 0.65   | 0.81  ← best
  ```
- `SectorOverview` — sector analysis results with sector-level aggregate metrics

**Dashboard integration:**
- Add "Compare" button next to ticker input
- After analyzing a stock, show "Compare with..." quick action
- Watchlist: "Compare all" button to compare watchlist items

## File Changes Summary

| Action | Path | Description |
|--------|------|-------------|
| Modify | `backend/graph/workflow.py` | Add `run_comparison()`, `run_streaming_comparison()` |
| Modify | `backend/state/agent_state.py` | Add `ComparisonResult`, `RelativeStrength` types |
| Modify | `backend/state/enums.py` | Add `WSMessageType.COMPARISON_RESULT` |
| Modify | `backend/agents/chairperson.py` | Add comparison prompt/method |
| Create | `backend/tools/relative_strength.py` | Correlation, relative performance calc |
| Create | `backend/tools/sector_data.py` | Sector-to-stocks mapping |
| Modify | `backend/api/websocket.py` | Handle `compare` command |
| Modify | `backend/api/routes.py` | Add compare, sector endpoints |
| Create | `frontend/src/pages/ComparePage.tsx` | Comparison page |
| Create | `frontend/src/components/ComparisonInput.tsx` | Multi-ticker input |
| Create | `frontend/src/components/ComparisonGrid.tsx` | Side-by-side results |
| Create | `frontend/src/components/ComparisonTable.tsx` | Tabular comparison |
| Create | `frontend/src/components/RankingCard.tsx` | Ranked results |
| Create | `frontend/src/components/RelativePerformanceChart.tsx` | Multi-line chart |
| Modify | `frontend/src/components/Dashboard.tsx` | Add compare button |
| Modify | `frontend/src/hooks/useWebSocket.ts` | Handle comparison messages |

## Dependencies

- No new Python packages required (uses existing market data tools)
- Frontend: May want `react-router-dom` if not already present for page routing

## Testing

- `tests/test_comparison.py` — multi-stock workflow, ranking logic
- `tests/test_relative_strength.py` — correlation, Sharpe ratio calculations
- `tests/test_sector_analysis.py` — sector mapping, aggregate metrics
- Test with 2, 3, 4 stocks to verify parallel execution scales

## Performance Considerations

- 4 stocks × 3 agents = 12 parallel LLM calls — monitor rate limits
- Cache individual stock analyses so re-comparing doesn't re-run everything
- Consider a "quick compare" mode that only runs technical analysis (fastest, cheapest)
