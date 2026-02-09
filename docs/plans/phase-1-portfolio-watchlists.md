# Phase 1: Portfolio & Watchlists

## Goal

Allow users to save stocks they're interested in, track positions they hold, and see personalized portfolio data that feeds into the analysis pipeline.

## Why First

- Highest immediate user value — transforms a one-shot tool into a persistent workspace
- Foundation for Phases 2, 4, and 5 (all need user/portfolio context)
- The risk manager already accepts `portfolio_sector_weight` (`backend/graph/workflow.py:22`) but it's always passed as `0.0` from the WebSocket handler (`backend/api/websocket.py:16`) — real portfolio data would make risk assessment meaningful

## Features

### 1.1 User Authentication

Simple auth so users have persistent state.

**Backend:**
- Add `backend/auth/` module with JWT token handling
- New DB model `User` in `backend/dao/models.py`:
  ```python
  class User(Base):
      __tablename__ = "users"
      id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
      email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
      password_hash: Mapped[str] = mapped_column(String(255))
      created_at: Mapped[datetime] = mapped_column(default=datetime.now)
  ```
- Auth endpoints in `backend/api/routes.py`:
  - `POST /api/auth/register`
  - `POST /api/auth/login` → returns JWT
  - `GET /api/auth/me` → returns user profile
- Middleware to extract user from JWT on protected routes
- Add `user_id` FK to existing `AnalysisSession` model for analysis history

**Frontend:**
- Login/register page at `/auth`
- Auth context provider wrapping the app
- JWT stored in localStorage, attached to WebSocket connection and API calls
- Protected route wrapper for dashboard

**Dependencies:** `pyjwt`, `passlib[bcrypt]`

### 1.2 Watchlist

**Backend:**
- New DB model:
  ```python
  class Watchlist(Base):
      __tablename__ = "watchlists"
      id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
      user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("users.id"))
      name: Mapped[str] = mapped_column(String(100), default="Default")
      created_at: Mapped[datetime] = mapped_column(default=datetime.now)
      items: Mapped[list["WatchlistItem"]] = relationship(...)

  class WatchlistItem(Base):
      __tablename__ = "watchlist_items"
      id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
      watchlist_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("watchlists.id"))
      ticker: Mapped[str] = mapped_column(String(20))
      market: Mapped[Market] = mapped_column(SQLEnum(Market))
      added_at: Mapped[datetime] = mapped_column(default=datetime.now)
  ```
- CRUD endpoints:
  - `GET /api/watchlists`
  - `POST /api/watchlists`
  - `POST /api/watchlists/{id}/items`
  - `DELETE /api/watchlists/{id}/items/{item_id}`

**Frontend:**
- Watchlist sidebar component showing saved tickers
- "Add to watchlist" button on the dashboard after analysis
- Click a watchlist item → runs analysis for that ticker
- Quick price indicators next to each watchlist item (fetched from market data)

### 1.3 Portfolio Tracking

**Backend:**
- New DB models:
  ```python
  class Portfolio(Base):
      __tablename__ = "portfolios"
      id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
      user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("users.id"))
      name: Mapped[str] = mapped_column(String(100), default="My Portfolio")
      created_at: Mapped[datetime] = mapped_column(default=datetime.now)
      positions: Mapped[list["Position"]] = relationship(...)

  class Position(Base):
      __tablename__ = "positions"
      id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
      portfolio_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("portfolios.id"))
      ticker: Mapped[str] = mapped_column(String(20))
      market: Mapped[Market] = mapped_column(SQLEnum(Market))
      quantity: Mapped[float] = mapped_column(Float)
      avg_entry_price: Mapped[float] = mapped_column(Float)
      sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
      opened_at: Mapped[datetime] = mapped_column(default=datetime.now)
      closed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
  ```
- CRUD endpoints:
  - `GET /api/portfolios`
  - `POST /api/portfolios`
  - `POST /api/portfolios/{id}/positions`
  - `PATCH /api/portfolios/{id}/positions/{pos_id}` (update quantity, close)
  - `GET /api/portfolios/{id}/summary` (P&L, sector weights, total value)
- **Integration with analysis pipeline**: When user runs analysis on a ticker, calculate actual `portfolio_sector_weight` from their portfolio and pass it to `BoardroomGraph.run_streaming()` — replacing the hardcoded `0.0`

**Frontend:**
- Portfolio page showing all positions with:
  - Current price (from market data tool)
  - P&L per position (current vs entry)
  - Total portfolio value and daily change
  - Sector allocation pie/donut chart
- "Add position" form (ticker, quantity, entry price)
- From dashboard: "Add to portfolio" button after BUY recommendation

### 1.4 Analysis History

**Backend:**
- The `AnalysisSession` and related models already exist in `backend/dao/models.py`
- Add `user_id` FK to `AnalysisSession`
- New endpoint: `GET /api/analyses?ticker=AAPL&limit=10` — returns past sessions with decisions
- Persist analysis results in the WebSocket handler (currently not saving to DB)

**Frontend:**
- History panel on dashboard showing past analyses for the current ticker
- "Analysis history" page listing all past analyses with filters (date, ticker, action)
- Click to expand and see full agent reports from that session

## File Changes Summary

| Action | Path | Description |
|--------|------|-------------|
| Create | `backend/auth/__init__.py` | Auth module |
| Create | `backend/auth/jwt.py` | JWT token creation/validation |
| Create | `backend/auth/dependencies.py` | FastAPI dependencies for auth |
| Modify | `backend/dao/models.py` | Add User, Watchlist, Portfolio, Position models |
| Modify | `backend/api/routes.py` | Add auth, watchlist, portfolio, history endpoints |
| Modify | `backend/api/websocket.py` | Auth on WS connect, persist results, portfolio weight |
| Modify | `backend/config.py` | Add `jwt_secret` setting |
| Create | `frontend/src/pages/AuthPage.tsx` | Login/register |
| Create | `frontend/src/pages/PortfolioPage.tsx` | Portfolio management |
| Create | `frontend/src/components/WatchlistSidebar.tsx` | Watchlist panel |
| Create | `frontend/src/components/AnalysisHistory.tsx` | Past analyses |
| Create | `frontend/src/contexts/AuthContext.tsx` | Auth state management |
| Modify | `frontend/src/components/Dashboard.tsx` | Add watchlist, history, portfolio links |
| Create | `alembic/versions/xxx_add_users_portfolios.py` | DB migration |

## Alembic Migration

Single migration adding all Phase 1 tables:
- `users`
- `watchlists`, `watchlist_items`
- `portfolios`, `positions`
- Add `user_id` column to `analysis_sessions`

## Testing

- `tests/test_auth.py` — registration, login, JWT validation, protected routes
- `tests/test_watchlist.py` — CRUD operations, user isolation
- `tests/test_portfolio.py` — positions CRUD, P&L calculation, sector weight calc
- `tests/test_analysis_history.py` — persistence, retrieval, filtering
- Update `tests/test_workflow.py` — verify portfolio weight integration

## Estimated Scope

~15-20 files touched/created. Backend-heavy phase.
