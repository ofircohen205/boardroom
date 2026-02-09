# Phase 4: Alerts & Notifications

## Goal

Keep users informed about their watchlist and portfolio stocks without requiring them to manually run analyses. Price alerts, condition-triggered re-analyses, and scheduled reports.

## Why This Matters

- Users don't want to check the dashboard constantly
- Market conditions change — an analysis from last week may be stale
- Alerts create engagement and retention
- Requires Phase 1 (watchlists and portfolio to know what to alert on)

## Features

### 4.1 Price Alerts

Notify users when a stock crosses a price threshold.

**Backend:**
- New DB model:
  ```python
  class PriceAlert(Base):
      __tablename__ = "price_alerts"
      id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
      user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("users.id"))
      ticker: Mapped[str] = mapped_column(String(20))
      market: Mapped[Market] = mapped_column(SQLEnum(Market))
      condition: Mapped[str] = mapped_column(String(20))  # "above", "below", "change_pct"
      target_value: Mapped[float] = mapped_column(Float)
      triggered: Mapped[bool] = mapped_column(Boolean, default=False)
      triggered_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
      created_at: Mapped[datetime] = mapped_column(default=datetime.now)
  ```
- Alert conditions:
  - `above` — price goes above target
  - `below` — price goes below target
  - `change_pct` — price changes by more than X% in a day
- CRUD endpoints:
  - `POST /api/alerts` — create alert
  - `GET /api/alerts` — list user's alerts
  - `DELETE /api/alerts/{id}` — remove alert
  - `PATCH /api/alerts/{id}` — update/reset alert

### 4.2 Alert Checker Job

Background job to evaluate alerts against live prices.

**Backend — `backend/jobs/alert_checker.py`:**
- Runs every 5 minutes during market hours (9:30 AM - 4:00 PM ET)
- Batch-fetches prices for all active alert tickers (using `backend/tools/market_data.py`)
- Groups alerts by ticker to minimize API calls
- When triggered:
  1. Mark alert as `triggered=True`
  2. Create notification (see 4.4)
  3. Send via configured channel (see 4.5)

### 4.3 Scheduled Analysis

Automatically re-run analysis on watchlist stocks at user-defined intervals.

**Backend:**
- New DB model:
  ```python
  class ScheduledAnalysis(Base):
      __tablename__ = "scheduled_analyses"
      id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
      user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("users.id"))
      ticker: Mapped[str] = mapped_column(String(20))
      market: Mapped[Market] = mapped_column(SQLEnum(Market))
      frequency: Mapped[str] = mapped_column(String(20))  # "daily", "weekly", "on_change"
      last_run: Mapped[Optional[datetime]] = mapped_column(nullable=True)
      next_run: Mapped[Optional[datetime]] = mapped_column(nullable=True)
      active: Mapped[bool] = mapped_column(Boolean, default=True)
  ```
- Frequency options:
  - `daily` — run once per trading day, before market open
  - `weekly` — run every Monday morning
  - `on_change` — re-run when significant price movement detected (>3% daily move)
- Job: `backend/jobs/scheduled_analyzer.py`
  - Query scheduled analyses where `next_run <= now`
  - Run `BoardroomGraph` for each
  - Save results to analysis history
  - Create notification with summary

### 4.4 Notification System

Internal notification center for in-app alerts.

**Backend:**
- New DB model:
  ```python
  class Notification(Base):
      __tablename__ = "notifications"
      id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
      user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("users.id"))
      type: Mapped[str] = mapped_column(String(50))  # "price_alert", "analysis_complete", "recommendation_change"
      title: Mapped[str] = mapped_column(String(200))
      body: Mapped[str] = mapped_column(Text)
      data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
      read: Mapped[bool] = mapped_column(Boolean, default=False)
      created_at: Mapped[datetime] = mapped_column(default=datetime.now)
  ```
- Notification types:
  - `price_alert` — "AAPL crossed above $200"
  - `analysis_complete` — "Scheduled analysis for MSFT completed: BUY (78% confidence)"
  - `recommendation_change` — "TSLA recommendation changed from HOLD to SELL"
  - `veto_alert` — "Risk manager vetoed NVDA — sector overweight"
- Endpoints:
  - `GET /api/notifications?unread=true`
  - `PATCH /api/notifications/{id}/read`
  - `POST /api/notifications/read-all`

### 4.5 Delivery Channels

**Phase 4a (in-app only):**
- WebSocket push: When user is connected, push notifications in real-time
  - Add new `WSMessageType.NOTIFICATION` to `backend/state/enums.py`
  - Maintain a registry of connected user WebSockets
- Notification bell in the frontend header with unread count badge

**Phase 4b (external — future extension):**
- Email via SendGrid/SES (new `backend/notifications/email.py`)
- Push notifications via Web Push API
- Webhook delivery for power users

### 4.6 Frontend

**Components:**
- `NotificationBell` — header icon with unread count badge, dropdown showing recent notifications
- `NotificationCenter` — full page/modal listing all notifications with filters
- `AlertManager` — page to create/manage price alerts
  - Per-stock alert creation form
  - Active alerts list with toggle/delete
- `ScheduleManager` — configure scheduled analyses per watchlist item
- `AlertBanner` — toast-style pop-up when real-time notification arrives

**Dashboard integration:**
- After analysis: "Set alert for this stock" quick action
- Watchlist items: Alert icon indicating active alerts
- Portfolio positions: "Alert me if P&L drops below -5%"

## File Changes Summary

| Action | Path | Description |
|--------|------|-------------|
| Modify | `backend/dao/models.py` | Add PriceAlert, ScheduledAnalysis, Notification |
| Create | `backend/jobs/alert_checker.py` | Price alert evaluation job |
| Create | `backend/jobs/scheduled_analyzer.py` | Scheduled analysis job |
| Create | `backend/api/alerts.py` | Alert CRUD endpoints |
| Create | `backend/api/notifications.py` | Notification endpoints |
| Modify | `backend/api/routes.py` | Mount alert and notification routers |
| Modify | `backend/api/websocket.py` | Push notifications to connected users |
| Modify | `backend/state/enums.py` | Add NOTIFICATION message type |
| Modify | `backend/main.py` | Register alert checker and scheduler jobs |
| Create | `frontend/src/components/NotificationBell.tsx` | Header notification icon |
| Create | `frontend/src/components/NotificationCenter.tsx` | Full notification list |
| Create | `frontend/src/pages/AlertsPage.tsx` | Alert management |
| Modify | `frontend/src/components/Dashboard.tsx` | Add notification bell to header |
| Modify | `frontend/src/hooks/useWebSocket.ts` | Handle notification messages |
| Create | `alembic/versions/xxx_add_alerts_notifications.py` | DB migration |

## Dependencies

- `apscheduler` — background job scheduling (may already exist from Phase 2)
- Phase 1 required for user context, watchlists, portfolio

## Testing

- `tests/test_price_alerts.py` — alert creation, trigger logic, edge cases (exact match, gap open)
- `tests/test_alert_checker.py` — batch price fetch, multiple alerts per ticker, market hours check
- `tests/test_scheduled_analysis.py` — frequency calculation, next_run computation
- `tests/test_notifications.py` — creation, read/unread, WebSocket push

## Edge Cases

- Market hours detection — don't run alerts on weekends/holidays
- Rate limiting — cap alerts per user (e.g., max 50 active alerts)
- Duplicate prevention — don't re-trigger same alert within cooldown period
- Stale prices — handle cases where market data API is slow/unavailable
- User connected on multiple devices — notifications delivered to all active WebSockets
