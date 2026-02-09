# Phase 2: Performance Tracking

## Goal

Track how Boardroom's recommendations perform over time. Show users whether BUY/SELL/HOLD calls were accurate, which agents contribute most to correct predictions, and how stock prices moved since each analysis.

## Why This Matters

- Builds user trust — transparency about accuracy
- Differentiator — most AI analysis tools don't track their own performance
- Feedback loop — identifies which agents/signals are most valuable
- Requires Phase 1 (analysis history with persistence)

## Features

### 2.1 Outcome Tracking

Track what actually happened after each recommendation.

**Backend:**
- New DB model:
  ```python
  class AnalysisOutcome(Base):
      __tablename__ = "analysis_outcomes"
      id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
      session_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("analysis_sessions.id"), unique=True)
      ticker: Mapped[str] = mapped_column(String(20))
      action_recommended: Mapped[Action] = mapped_column(SQLEnum(Action))
      price_at_recommendation: Mapped[float] = mapped_column(Float)
      price_after_1d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
      price_after_7d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
      price_after_30d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
      price_after_90d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
      outcome_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
      created_at: Mapped[datetime] = mapped_column(default=datetime.now)
      last_updated: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)
  ```
- When analysis completes, save current price as `price_at_recommendation`
- Correctness logic:
  - BUY is correct if price went up by >2% in the tracked window
  - SELL is correct if price went down by >2%
  - HOLD is correct if price stayed within +/- 5%

### 2.2 Background Price Updater

Scheduled job to fill in follow-up prices.

**Backend:**
- New module `backend/jobs/outcome_tracker.py`:
  - Query all `AnalysisOutcome` rows with null price fields where enough time has elapsed
  - Fetch current prices using existing `backend/tools/market_data.py`
  - Update the price columns and calculate `outcome_correct`
- Runner options:
  - **Option A (simple):** APScheduler running inside the FastAPI process — good enough for single-instance
  - **Option B (scalable):** Celery with Redis broker — better for production
- Schedule: Run every 4 hours during market hours

**Config additions in `backend/config.py`:**
```python
outcome_check_interval_hours: int = 4
outcome_correctness_threshold: float = 0.02  # 2%
```

### 2.3 Performance Analytics API

**Endpoints:**
- `GET /api/performance/summary` — overall accuracy stats
  ```json
  {
    "total_analyses": 142,
    "tracked_outcomes": 98,
    "accuracy_7d": 0.67,
    "accuracy_30d": 0.71,
    "best_calls": [...],
    "worst_calls": [...]
  }
  ```
- `GET /api/performance/by-action` — accuracy broken down by BUY/SELL/HOLD
- `GET /api/performance/by-agent` — which agent signals correlated most with correct outcomes
- `GET /api/performance/ticker/{ticker}` — performance history for a specific stock
- `GET /api/performance/timeline` — accuracy over time (for charting)

### 2.4 Agent Attribution

Measure which agents contribute most to correct predictions.

**Backend:**
- New DB model:
  ```python
  class AgentAccuracy(Base):
      __tablename__ = "agent_accuracy"
      id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
      agent_type: Mapped[AgentType] = mapped_column(SQLEnum(AgentType))
      period: Mapped[str] = mapped_column(String(10))  # "7d", "30d", "90d"
      total_signals: Mapped[int] = mapped_column(default=0)
      correct_signals: Mapped[int] = mapped_column(default=0)
      accuracy: Mapped[float] = mapped_column(Float, default=0.0)
      last_calculated: Mapped[datetime] = mapped_column(default=datetime.now)
  ```
- Attribution logic:
  - Fundamental: Was the fundamental outlook (bullish/bearish based on growth + P/E) aligned with the actual price movement?
  - Sentiment: Did sentiment score direction match price direction?
  - Technical: Did the trend prediction (bullish/bearish/neutral from `TechnicalReport.trend`) match?
  - Risk: Were vetoes correct? (Would the stock have lost money?)
- Recalculate on every outcome update

### 2.5 Frontend Performance Dashboard

**New page: `/performance`**

**Components:**
- `PerformanceSummary` — headline stats: overall accuracy %, total tracked, streak
- `AccuracyChart` — line chart showing accuracy over time (using lightweight-charts)
- `ActionBreakdown` — bar chart: BUY vs SELL vs HOLD accuracy
- `AgentLeaderboard` — table ranking agents by accuracy with sparklines
- `RecentOutcomes` — scrollable list of recent recommendations with actual results
  - Green/red indicator showing if the call was correct
  - Price at recommendation → price now with % change

**Integration with existing dashboard:**
- On `DecisionCard` (`frontend/src/components/DecisionCard.tsx`): Add small "track record" indicator
  - "This agent's BUY calls are correct 72% of the time"
- On analysis history items: Show outcome badge (correct/incorrect/pending)

## File Changes Summary

| Action | Path | Description |
|--------|------|-------------|
| Modify | `backend/dao/models.py` | Add AnalysisOutcome, AgentAccuracy models |
| Create | `backend/jobs/__init__.py` | Jobs module |
| Create | `backend/jobs/outcome_tracker.py` | Background price tracking job |
| Create | `backend/api/performance.py` | Performance analytics endpoints |
| Modify | `backend/api/routes.py` | Mount performance router |
| Modify | `backend/api/websocket.py` | Create AnalysisOutcome on analysis complete |
| Modify | `backend/main.py` | Start scheduler on app startup |
| Modify | `backend/config.py` | Add outcome tracking settings |
| Create | `frontend/src/pages/PerformancePage.tsx` | Performance dashboard page |
| Create | `frontend/src/components/PerformanceSummary.tsx` | Headline accuracy stats |
| Create | `frontend/src/components/AccuracyChart.tsx` | Accuracy over time |
| Create | `frontend/src/components/AgentLeaderboard.tsx` | Agent ranking table |
| Create | `frontend/src/components/RecentOutcomes.tsx` | Recent calls with results |
| Modify | `frontend/src/components/DecisionCard.tsx` | Add track record indicator |
| Create | `alembic/versions/xxx_add_outcomes.py` | DB migration |

## Dependencies

- `apscheduler` (if using Option A for background jobs)
- Phase 1 must be complete (analysis persistence, user context)

## Testing

- `tests/test_outcome_tracker.py` — price fetching, correctness calculation, edge cases
- `tests/test_performance_api.py` — summary stats, filtering, agent attribution
- `tests/test_agent_accuracy.py` — attribution logic per agent type
- Mock market data to simulate price movements for deterministic tests

## Edge Cases

- Stock delisted after analysis → mark outcome as "unavailable"
- Splits/dividends affecting price comparison → use adjusted close prices
- Analyses on weekends/holidays → use next trading day price
- Veto outcomes — track whether the vetoed stock would have lost money (validates risk agent)
