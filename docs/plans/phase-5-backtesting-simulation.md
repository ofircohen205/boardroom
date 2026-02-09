# Phase 5: Backtesting & Simulation

## Goal

Let users test how Boardroom's agent system would have performed historically, run paper trading simulations, and customize agent weights to fine-tune their strategy.

## Why This Matters

- "Would this system have told me to buy NVDA a year ago?" is the #1 question users will ask
- Paper trading lets users build confidence before acting on recommendations
- Customizable agent weights let power users tune the system to their style
- Requires Phase 2 (performance tracking) to validate backtests against real outcomes

## Features

### 5.1 Historical Data Pipeline

Fetch and store historical data for backtesting.

**Backend — new module `backend/data/historical.py`:**
- Use Yahoo Finance (already integrated via `backend/tools/market_data.py`) to pull:
  - Daily OHLCV data (up to 5 years back)
  - Historical fundamental snapshots (quarterly earnings)
- Storage: Dedicated DB tables for historical data to avoid re-fetching
  ```python
  class HistoricalPrice(Base):
      __tablename__ = "historical_prices"
      id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
      ticker: Mapped[str] = mapped_column(String(20), index=True)
      date: Mapped[datetime] = mapped_column(index=True)
      open: Mapped[float] = mapped_column(Float)
      high: Mapped[float] = mapped_column(Float)
      low: Mapped[float] = mapped_column(Float)
      close: Mapped[float] = mapped_column(Float)
      volume: Mapped[int] = mapped_column()
      adjusted_close: Mapped[float] = mapped_column(Float)
      # Unique constraint on (ticker, date)

  class HistoricalFundamentals(Base):
      __tablename__ = "historical_fundamentals"
      id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
      ticker: Mapped[str] = mapped_column(String(20), index=True)
      quarter_end: Mapped[datetime] = mapped_column(index=True)
      revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
      earnings: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
      pe_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
      debt_to_equity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
  ```
- Backfill job: Populate on first backtest request, then cache for future use
- Use `backend/cache.py` pattern for TTL-based freshness

### 5.2 Backtest Engine

Simulate running the analysis pipeline at historical points in time.

**Backend — new module `backend/backtest/engine.py`:**

**Approach:** Since we can't re-run LLM sentiment analysis for historical dates (no historical news context), the backtest engine uses a **rules-based simulation** of the agent outputs:

- **Technical Agent (fully replayable):** Calculate MA, RSI, trend from historical prices using `backend/tools/technical_indicators.py` — these are deterministic
- **Fundamental Agent (quarterly snapshots):** Use historical quarterly data (P/E, revenue growth, debt) that was current at each simulation date
- **Sentiment Agent (simplified):** Use price momentum as a sentiment proxy (5-day return direction + magnitude) since we can't replay historical news
- **Risk Manager:** Apply same veto rules (sector weight, VaR calculation from historical volatility)
- **Chairperson (rules-based):** Weighted scoring model instead of LLM call:
  - Technical score (0-100) based on RSI, MA crossovers, trend
  - Fundamental score (0-100) based on P/E relative to sector, growth rate
  - Sentiment score (0-100) based on momentum proxy
  - Weighted sum → BUY/SELL/HOLD thresholds

```python
class BacktestConfig(TypedDict):
    ticker: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    check_frequency: str  # "daily", "weekly", "monthly"
    agent_weights: dict[str, float]  # {"fundamental": 0.3, "technical": 0.4, "sentiment": 0.3}
    position_size_pct: float  # What % of capital to allocate per trade
    stop_loss_pct: Optional[float]  # Auto-sell if position drops X%
    take_profit_pct: Optional[float]  # Auto-sell if position gains X%

class BacktestResult(TypedDict):
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    trades: list[dict]  # [{date, action, price, reason, pnl}]
    equity_curve: list[dict]  # [{date, value}]
    buy_and_hold_return: float  # For comparison
```

**Endpoint:**
- `POST /api/backtest/run`
- Returns `BacktestResult` with full trade log and equity curve
- Long-running → use async job with progress updates via WebSocket

### 5.3 Paper Trading

Simulate live trading based on real-time Boardroom recommendations.

**Backend:**
- New DB models:
  ```python
  class PaperAccount(Base):
      __tablename__ = "paper_accounts"
      id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
      user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("users.id"))
      name: Mapped[str] = mapped_column(String(100))
      initial_capital: Mapped[float] = mapped_column(Float)
      current_cash: Mapped[float] = mapped_column(Float)
      created_at: Mapped[datetime] = mapped_column(default=datetime.now)

  class PaperTrade(Base):
      __tablename__ = "paper_trades"
      id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
      account_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("paper_accounts.id"))
      session_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID, ForeignKey("analysis_sessions.id"), nullable=True)
      ticker: Mapped[str] = mapped_column(String(20))
      action: Mapped[str] = mapped_column(String(10))  # "BUY", "SELL"
      quantity: Mapped[float] = mapped_column(Float)
      price: Mapped[float] = mapped_column(Float)
      executed_at: Mapped[datetime] = mapped_column(default=datetime.now)
  ```
- Auto-trade mode: Optionally auto-execute paper trades based on Chairperson decisions
- Manual mode: User reviews recommendation, clicks "Paper trade this" to execute
- P&L tracking tied to paper account

**Endpoints:**
- `POST /api/paper/accounts` — create paper account with starting capital
- `GET /api/paper/accounts/{id}` — account summary (cash, positions, total value)
- `POST /api/paper/accounts/{id}/trade` — execute paper trade
- `GET /api/paper/accounts/{id}/trades` — trade history
- `GET /api/paper/accounts/{id}/performance` — returns, Sharpe, drawdown

### 5.4 Strategy Builder

Let users customize how agents contribute to the final decision.

**Backend:**
- New DB model:
  ```python
  class Strategy(Base):
      __tablename__ = "strategies"
      id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
      user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("users.id"))
      name: Mapped[str] = mapped_column(String(100))
      weights: Mapped[dict] = mapped_column(JSONB)
      # {"fundamental": 0.3, "technical": 0.4, "sentiment": 0.3}
      risk_tolerance: Mapped[str] = mapped_column(String(20))  # "conservative", "moderate", "aggressive"
      stop_loss_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
      take_profit_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
      created_at: Mapped[datetime] = mapped_column(default=datetime.now)
  ```
- Feed strategy weights into the Chairperson's decision process
- Strategy can be used for both live analysis and backtesting

### 5.5 Frontend

**New pages:**

**`/backtest` — Backtesting page:**
- Config form: ticker, date range, initial capital, frequency, agent weights (sliders)
- Run button → shows progress bar
- Results display:
  - Equity curve chart (lightweight-charts `AreaSeries`)
  - Buy/sell markers on price chart
  - Stats card: total return, Sharpe, drawdown, win rate
  - Comparison line: equity curve vs buy-and-hold
  - Trade log table: date, action, price, P&L

**`/paper-trading` — Paper Trading page:**
- Account overview: cash balance, open positions, total value
- "Execute trade" button on analysis results
- Trade history with running P&L
- Performance chart showing account value over time

**`/strategies` — Strategy Builder page:**
- Agent weight sliders (fundamental, technical, sentiment)
- Risk tolerance selector
- Stop loss / take profit inputs
- "Test this strategy" → links to backtest with these settings
- Save/load strategies

## File Changes Summary

| Action | Path | Description |
|--------|------|-------------|
| Create | `backend/data/__init__.py` | Data module |
| Create | `backend/data/historical.py` | Historical data fetching and storage |
| Create | `backend/backtest/__init__.py` | Backtest module |
| Create | `backend/backtest/engine.py` | Backtest simulation engine |
| Create | `backend/backtest/scoring.py` | Rules-based agent scoring |
| Modify | `backend/dao/models.py` | Add HistoricalPrice, PaperAccount, PaperTrade, Strategy |
| Create | `backend/api/backtest.py` | Backtest endpoints |
| Create | `backend/api/paper_trading.py` | Paper trading endpoints |
| Create | `backend/api/strategies.py` | Strategy CRUD endpoints |
| Modify | `backend/api/routes.py` | Mount new routers |
| Modify | `backend/agents/chairperson.py` | Accept strategy weights |
| Create | `frontend/src/pages/BacktestPage.tsx` | Backtest interface |
| Create | `frontend/src/pages/PaperTradingPage.tsx` | Paper trading |
| Create | `frontend/src/pages/StrategiesPage.tsx` | Strategy builder |
| Create | `frontend/src/components/EquityCurve.tsx` | Equity curve chart |
| Create | `frontend/src/components/TradeLog.tsx` | Trade history table |
| Create | `frontend/src/components/WeightSliders.tsx` | Agent weight controls |
| Create | `alembic/versions/xxx_add_backtest_tables.py` | DB migration |

## Dependencies

- `numpy` (already in project) — for Sharpe ratio, drawdown calculations
- Phase 2 required — performance tracking validates backtest accuracy

## Testing

- `tests/test_backtest_engine.py` — simulation logic, trade execution, P&L
- `tests/test_historical_data.py` — data fetching, caching, gap handling
- `tests/test_paper_trading.py` — account management, trade execution, position tracking
- `tests/test_scoring.py` — rules-based agent scoring vs known outcomes
- Use deterministic historical data for reproducible backtest results

## Limitations to Document

- Backtest uses rules-based scoring, not LLM calls (no historical sentiment replay)
- Look-ahead bias: Technical indicators need warmup period (50 days for MA50)
- Survivorship bias: Only tests stocks that still exist today
- No slippage or commission modeling (simplified)
- Past performance ≠ future results (display disclaimer prominently)
