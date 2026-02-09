# Phase 3: Comparative Analysis - Implementation Complete

## Overview
Phase 3 enables users to compare multiple stocks side-by-side, analyze entire sectors, and visualize relative performance. This expands The Boardroom from single-stock analysis to multi-stock comparative workflows.

## ✅ Completed Features

### 1. Multi-Stock Comparison

**Backend Implementation:**
- ✅ `POST /api/compare/stocks` endpoint
- ✅ `run_comparison_streaming()` in `BoardroomGraph`
- ✅ Parallel execution of all agents for multiple tickers
- ✅ AI-powered ranking by Chairperson agent
- ✅ Comprehensive comparison result with best pick

**Key Features:**
- Compare 2-4 stocks simultaneously
- Run all analyst agents (Fundamental, Sentiment, Technical) in parallel
- Generate AI-powered rankings with scores and rationale
- Stream results in real-time as each agent completes

### 2. Sector Analysis

**Backend Implementation:**
- ✅ `POST /api/compare/sector` endpoint
- ✅ `GET /api/compare/sectors` endpoint to list available sectors
- ✅ Sector-to-stocks mapping in `backend/tools/sector_data.py`
- ✅ Support for 8 major sectors:
  - Technology
  - Financial Services
  - Healthcare
  - Energy
  - Consumer Goods
  - Industrial
  - Telecommunications
  - Real Estate

**Key Features:**
- Analyze top N stocks in any sector (default 5, max 8)
- Sector-level aggregate insights
- Easy sector selection from predefined list

### 3. Relative Strength Analysis

**Backend Implementation (`backend/tools/relative_strength.py`):**
- ✅ **Correlation Matrix**: Shows how stock price movements correlate
- ✅ **Relative Performance**: % returns over the analysis period
- ✅ **Valuation Comparison**: Side-by-side P/E, revenue growth, debt/equity, market cap

**Key Metrics:**
```python
RelativeStrength:
  - correlation_matrix: dict[ticker, dict[ticker, correlation_coefficient]]
  - relative_performance: dict[ticker, percentage_return]
  - valuation_comparison: dict[ticker, dict[metric, value]]
```

### 4. Frontend Components

**New Page: `/compare`**

**Core Components:**

1. **Comparison Input**
   - Manual mode: Add 2-4 tickers via chip-style input
   - Sector mode: Select from 8 predefined sectors
   - Validation and error handling
   - Responsive design

2. **Best Pick Card**
   - Prominently displays AI-selected best stock
   - Shows comparison summary with rationale
   - Visual trophy icon for emphasis

3. **Price Performance Chart** ✨ NEW
   - Multi-line chart using lightweight-charts
   - All stocks normalized to 100 at start
   - Color-coded lines with legend
   - Interactive time scale and crosshair
   - Visual comparison of price movements

4. **Side-by-Side Comparison Table** ✨ NEW
   - Tabular view of all key metrics
   - Highlights best value for each metric
   - Includes fundamental, sentiment, technical, and decision data
   - Visual indicators (🔺 for higher is better, 🔻 for lower is better)
   - Responsive layout

5. **Rankings Display**
   - Numbered ranking (1-4)
   - Score and confidence for each stock
   - Action badges (BUY/SELL/HOLD) with color coding
   - AI-generated rationale for each ranking

6. **Relative Performance Cards**
   - Grid of performance % for each stock
   - Color-coded (green for gains, red for losses)
   - Clean, card-based layout

## API Endpoints

### Compare Stocks
```bash
POST /api/compare/stocks
Content-Type: application/json

{
  "tickers": ["AAPL", "MSFT", "GOOGL"],
  "market": "US"
}
```

**Response:**
```json
{
  "tickers": ["AAPL", "MSFT", "GOOGL"],
  "best_pick": "MSFT",
  "comparison_summary": "Microsoft shows strongest fundamentals with...",
  "rankings": [
    {
      "ticker": "MSFT",
      "rank": 1,
      "score": 87.5,
      "rationale": "Strong revenue growth and positive sentiment",
      "decision": {
        "action": "BUY",
        "confidence": 0.85,
        "rationale": "..."
      }
    },
    ...
  ],
  "relative_strength": {
    "correlation_matrix": {
      "AAPL": {"AAPL": 1.0, "MSFT": 0.72, "GOOGL": 0.65},
      ...
    },
    "relative_performance": {
      "AAPL": 12.3,
      "MSFT": 18.7,
      "GOOGL": 8.4
    },
    "valuation_comparison": {
      "AAPL": {"pe_ratio": 28.5, "revenue_growth": 8.2, ...},
      ...
    }
  },
  "price_histories": {
    "AAPL": [{"time": "2026-01-01", "close": 175.23}, ...],
    ...
  },
  "stock_data": {
    "AAPL": {
      "fundamental": {...},
      "sentiment": {...},
      "technical": {...},
      "decision": {...}
    },
    ...
  }
}
```

### Analyze Sector
```bash
POST /api/compare/sector
Content-Type: application/json

{
  "sector": "technology",
  "limit": 5,
  "market": "US"
}
```

Returns same structure as compare stocks, plus:
```json
{
  "sector": "technology",
  ...
}
```

### List Sectors
```bash
GET /api/compare/sectors
```

**Response:**
```json
{
  "sectors": [
    {
      "key": "technology",
      "name": "Technology",
      "description": "Technology and software companies",
      "ticker_count": 8
    },
    ...
  ]
}
```

## Usage Examples

### Example 1: Compare Tech Stocks
```typescript
// Navigate to /compare
// Select Manual mode
// Add tickers: AAPL, MSFT, GOOGL
// Click "Run Comparison"

// Results show:
// - Best Pick: MSFT (87.5 score)
// - Price chart showing MSFT outperformed by 6%
// - Table showing MSFT has higher revenue growth
// - Rankings with detailed rationale
```

### Example 2: Analyze Technology Sector
```typescript
// Navigate to /compare
// Select Sector mode
// Choose "Technology"
// Click "Run Comparison"

// Analyzes: AAPL, MSFT, GOOGL, NVDA, META
// Shows sector-level insights and rankings
```

## Technical Architecture

### Backend Flow

```
User Request
    ↓
POST /api/compare/stocks
    ↓
BoardroomGraph.run_comparison_streaming()
    ↓
For each ticker:
  ├─ Fundamental Agent (parallel)
  ├─ Sentiment Agent (parallel)
  └─ Technical Agent (parallel)
    ↓
For each ticker:
  ├─ Risk Manager
  └─ Chairperson Decision
    ↓
Chairperson Comparison:
  ├─ Rank all stocks
  ├─ Select best pick
  └─ Generate comparison summary
    ↓
Calculate Relative Strength:
  ├─ Correlation matrix
  ├─ Relative performance
  └─ Valuation comparison
    ↓
Return ComparisonResult
```

### Frontend Flow

```
User Input (tickers/sector)
    ↓
POST to /api/compare/stocks or /sector
    ↓
Display Loading State
    ↓
Receive ComparisonResult
    ↓
Render:
  ├─ Best Pick Card
  ├─ Price Performance Chart (normalized)
  ├─ Rankings with rationale
  ├─ Side-by-Side Comparison Table
  └─ Relative Performance Cards
```

## Key Files

### Backend
| File | Purpose |
|------|---------|
| `backend/api/comparison.py` | REST endpoints for comparison |
| `backend/graph/workflow.py` | `run_comparison_streaming()` method |
| `backend/tools/relative_strength.py` | Correlation and performance calculations |
| `backend/tools/sector_data.py` | Sector-to-stocks mapping |
| `backend/state/agent_state.py` | Type definitions (ComparisonResult, etc.) |

### Frontend
| File | Purpose |
|------|---------|
| `frontend/src/pages/ComparePage.tsx` | Main comparison page |
| `frontend/src/components/RelativePerformanceChart.tsx` | Multi-line price chart |
| `frontend/src/components/ComparisonTable.tsx` | Side-by-side metrics table |
| `frontend/src/types/comparison.ts` | TypeScript types |

## Performance Considerations

### Parallel Execution
- With 4 stocks and 3 agents = 12 parallel LLM calls
- Uses `asyncio.gather()` for efficient concurrent execution
- Results streamed as they complete (no blocking)

### Rate Limiting
- Monitor API rate limits for high comparison volumes
- Consider implementing request throttling if needed
- Quick mode (technical only) reduces load by 66%

### Optimization Opportunities
- Cache individual stock analyses (not yet implemented)
- Implement "quick compare" mode with technical-only analysis
- Add result caching layer for frequently compared stocks

## Testing

### Manual Testing
```bash
# 1. Start backend
uv run uvicorn backend.main:app --reload

# 2. Start frontend
cd frontend && npm run dev

# 3. Navigate to http://localhost:5173/compare

# 4. Test manual comparison
# - Add 2-4 tickers
# - Verify all components render
# - Check price chart displays
# - Verify comparison table shows correct data

# 5. Test sector analysis
# - Select a sector
# - Verify correct stocks are compared
# - Check sector info displays
```

### API Testing
```bash
# Compare stocks
curl -X POST http://localhost:8000/api/compare/stocks \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["AAPL", "MSFT"], "market": "US"}'

# Sector analysis
curl -X POST http://localhost:8000/api/compare/sector \
  -H "Content-Type: application/json" \
  -d '{"sector": "technology", "limit": 3, "market": "US"}'

# List sectors
curl http://localhost:8000/api/compare/sectors
```

## Future Enhancements

### Phase 3+ Extensions
1. **Custom Sectors**: Allow users to create custom sector groupings
2. **Comparison History**: Save and revisit past comparisons
3. **More Chart Types**:
   - Correlation heatmap
   - Risk-return scatter plot
   - Valuation spider chart
4. **Export**: Download comparison results as PDF/CSV
5. **Watchlist Integration**: "Compare All Watchlist Items" button
6. **Advanced Filters**: Filter by P/E range, market cap, sector
7. **Sharpe Ratio**: Add risk-adjusted return comparison
8. **Correlation Insights**: AI commentary on correlation patterns

## Known Limitations

1. **Maximum 4 stocks**: To maintain performance and UI clarity
2. **Static sector mappings**: Sectors are hardcoded (not dynamic)
3. **US market only**: Currently only supports US tickers
4. **No caching**: Each comparison re-runs full analysis
5. **Basic ranking**: LLM-based ranking could be enhanced with weighted scoring

## Integration Points

### Dashboard Integration
- Add "Compare" button in Dashboard header ✅
- Future: After analyzing a stock, show "Compare with..." suggestion
- Future: Watchlist "Compare All" button

### Navigation
- Accessible via `/compare` route ✅
- Header navigation button ✅
- Direct links from analysis results (future)

## Summary

Phase 3 is **COMPLETE** with all core features implemented:
- ✅ Multi-stock comparison (2-4 stocks)
- ✅ Sector analysis (8 predefined sectors)
- ✅ Relative strength metrics
- ✅ Price performance chart
- ✅ Side-by-side comparison table
- ✅ AI-powered rankings
- ✅ Comprehensive frontend UI
- ✅ Full API endpoints

The system now supports sophisticated multi-stock analysis workflows, enabling users to make informed relative investment decisions rather than just single-stock analysis.
