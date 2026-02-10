# Implementation Status & Tracking

Detailed breakdown of what's completed, what's in progress, and what remains for each phase.

**Last Updated:** Feb 10, 2026
**Overall Progress:** 98% across all planned phases

**Quick Summary:**

- ✅ Phase 0 (Core) — COMPLETE: 5-agent pipeline, WebSocket, stock search, charts
- ✅ Phase 1 (Auth/Watchlist) — 100% COMPLETE: All backend endpoints, all frontend pages, auth flow fully integrated
- ✅ Phase 2 (Performance) — 100% COMPLETE: Full backend with job system, frontend dashboard with all components
- ✅ Phase 3 (Comparison) — 100% COMPLETE: Backend API, frontend page, full multi-stock comparison
- ✅ Phase 4a (Alerts & Notifications) — 100% COMPLETE: Price alerts, notifications, WebSocket push, alert checker job
- ✅ Phase 4b (Scheduled Analysis & Enhanced Notifications) — 100% COMPLETE: Scheduled analysis, TASE support, WebSocket reconnection, notification grouping, SendGrid foundation
- ✅ Backend Refactoring — 100% COMPLETE: Modular routers (auth, watchlists, portfolios, analysis, sectors, websocket, alerts, notifications, schedules)
- ✅ Frontend Refactoring — 100% COMPLETE: Shared layout components (AppLayout, Navbar, Footer, PageContainer) implemented. All pages migrated to shared layout. Styling inconsistencies fixed.
- ✅ User Settings Page — 100% COMPLETE: Profile management, password change, API key CRUD
- ⏳ Phase 5-6 — Not started

---

## Phase 0: Core System ✅ COMPLETE

The foundation is solid and working.

**Implemented:**

- ✅ 5-agent analysis pipeline with LangGraph orchestration
- ✅ Real-time WebSocket streaming from `/ws/analyze`
- ✅ Stock search with autocomplete (ticker lookup)
- ✅ TradingView lightweight-charts integration
- ✅ News/sentiment display
- ✅ PostgreSQL audit trail (AnalysisSession, AgentReport, FinalDecision)
- ✅ Multi-LLM support (Claude, GPT-4, Gemini)
- ✅ Caching layer
- ✅ Docker Compose setup
- ✅ Test suite (agents, tools, workflow)

**Status:** Production-ready. All Phase 0 goals met.

---

## Phase 1: Portfolio & Watchlists ✅ 100% COMPLETE

User authentication and portfolio management is fully implemented and integrated.

### ✅ COMPLETED

**Backend Database Models:**

- `User` table with email/password, relationships to watchlists, portfolios, sessions, API keys
- `Watchlist` and `WatchlistItem` tables for saved stock lists
- `Portfolio` and `Position` tables for tracking holdings
- `UserAPIKey` table for storing encrypted multi-provider API keys
- FK relationship from `AnalysisSession` to `User` for session history per user

**Backend Authentication:**

- JWT token creation and validation (`backend/auth/jwt.py`)
- Password hashing with bcrypt (`backend/auth/`)
- Auth dependencies module (`backend/auth/dependencies.py`)
- Database models support user context

**Backend REST API Endpoints** (all implemented in `backend/api/routes.py`):

- ✅ `POST /api/auth/register` — user registration with default watchlist & portfolio
- ✅ `POST /api/auth/login` — JWT token generation
- ✅ `GET /api/auth/me` — current user info
- ✅ `GET /api/watchlists` — list user's watchlists with items
- ✅ `POST /api/watchlists` — create new watchlist
- ✅ `POST /api/watchlists/{id}/items` — add ticker to watchlist
- ✅ `DELETE /api/watchlists/{id}/items/{item_id}` — remove from watchlist
- ✅ `GET /api/portfolios` — list user's portfolios with positions
- ✅ `POST /api/portfolios` — create new portfolio
- ✅ `POST /api/portfolios/{id}/positions` — add position to portfolio
- ✅ `DELETE /api/portfolios/{id}/positions/{position_id}` — remove position
- ✅ `GET /api/analyses?ticker=...&limit=...` — analysis history per user

**Frontend Components & Pages:**

- ✅ `AuthPage.tsx` — login/register with form toggle, error handling
- ✅ `PortfolioPage.tsx` — portfolio display and position CRUD
- ✅ `WatchlistSidebar.tsx` — watchlist display and selection
- ✅ `AnalysisHistory.tsx` — past analysis viewing
- ✅ `PresetSelector.tsx` — preset stock lists
- ✅ `AuthContext` — JWT token management and auth state
- ✅ `ProtectedRoute` wrapper in App.tsx
- ✅ App routing to `/auth`, `/`, `/portfolio`, `/compare`

**Database:**

- ✅ Migration `1e04e15e9cbb_...` creates all Phase 1 & 2 tables

### ✅ ALL COMPLETE

All Phase 1 features have been implemented and integrated:

- ✅ WebSocket authentication with JWT token verification
- ✅ Portfolio sector weight calculation and risk assessment integration
- ✅ Analysis persistence to DB per user
- ✅ WebSocket message filtering by user scope
- ✅ Dashboard integration with watchlist/portfolio management
- ✅ Portfolio page with P&L tracking
- ✅ Token refresh and auth state management
- ✅ Comprehensive test coverage for auth, watchlists, portfolios

### Impact When Complete

- Users can save/organize stocks of interest
- Portfolio tracking feeds into risk assessment (real sector weights instead of 0.0)
- Personalized analysis history per user
- Foundation for Phase 2 user-scoped performance metrics

---

## Phase 2: Performance Tracking ✅ 100% COMPLETE

Backend job system, API, and frontend dashboard are fully implemented.

### ✅ COMPLETED

**Backend Database Models:**

- ✅ `AnalysisOutcome` table:
  - Tracks recommendation (BUY/SELL/HOLD) and initial price
  - Follow-up prices: 1d, 7d, 30d, 90d
  - `outcome_correct` boolean (calculated)
  - Auto-updated timestamp
- ✅ `AgentAccuracy` table:
  - Per-agent accuracy metrics (fundamental, sentiment, technical, risk, chairperson)
  - Time periods: 7d, 30d, 90d
  - Signal count and accuracy percentage
  - Last calculated timestamp

**Backend Job System:**

- ✅ `backend/jobs/scheduler.py` — APScheduler setup and lifecycle
- ✅ `backend/jobs/outcome_tracker.py` — background job to:
  - Query AnalysisOutcomes with elapsed time windows
  - Fetch current prices from market data tool
  - Update price fields
  - Calculate `outcome_correct` (BUY +2%, SELL -2%, HOLD ±5%)
  - Scheduled to run every 4 hours during market hours
- ✅ Job started on app startup in `backend/main.py`

**Backend API (`backend/api/performance.py`):**

- ✅ `GET /api/performance/summary` — overall accuracy stats
- ✅ `GET /api/performance/agents` — all agents' accuracy by period
- ✅ `GET /api/performance/agent/{agent_type}` — specific agent details
- ✅ `GET /api/performance/recent?limit=20&ticker=...` — recent outcomes with returns
- ✅ `GET /api/performance/ticker/{ticker}` — per-ticker accuracy
- ✅ `POST /api/performance/trigger-update` — manual job trigger
- ✅ Routers included in `backend/main.py`

**Backend Services:**

- ✅ `backend/services/outcome_service.py` — performance calculation logic
- ✅ Integration with existing market_data tools

**Database:**

- ✅ Migration creates AnalysisOutcome and AgentAccuracy tables
- ✅ Unique constraint on (session_id) in AnalysisOutcome

### ✅ ALL COMPLETE

All Phase 2 features have been implemented:

- ✅ `PerformancePage.tsx` at `/performance` route
- ✅ `PerformanceSummary.tsx` — headline accuracy stats and metrics
- ✅ `AccuracyChart.tsx` — line chart of accuracy trends
- ✅ `AgentLeaderboard.tsx` — agent ranking table
- ✅ `RecentOutcomes.tsx` — recent recommendations with green/red indicators
- ✅ App routing with ProtectedRoute
- ✅ Integration with DecisionCard for historical accuracy badges
- ✅ Performance metrics display across all dashboards
- ✅ Comprehensive test coverage for outcome tracking and performance APIs

### Key Details

- Correctness thresholds: BUY = +2%, SELL = -2%, HOLD = ±5% (configurable)
- Job runs every 4 hours
- Handles edge cases: stock delisted, splits/dividends, weekend pricing

### Impact When Complete

- Show users how accurate our recommendations are
- Identify strongest/weakest agent signals
- Build trust through transparency
- Differentiator from other AI tools

---

## Phase 3: Comparative Analysis ✅ 100% COMPLETE

Multi-stock comparison backend and frontend page are fully implemented and integrated.

### ✅ COMPLETED

**Backend API (`backend/api/comparison.py`):**

- ✅ `POST /api/compare/stocks` — compare 2-4 stocks:
  - Input: tickers list, market
  - Output: individual analyses + rankings + best pick
  - Streams individual agent completions
  - Returns comparison result
- ✅ `POST /api/compare/sector` — analyze top N stocks in sector:
  - Input: sector name, limit (2-8)
  - Returns ranked stocks for sector
- ✅ `GET /api/compare/sectors` — list available sectors
- ✅ Routers included in `backend/main.py`

**Backend Tools:**

- ✅ `backend/tools/sector_data.py`:
  - Static mapping of sectors to stocks (Tech, Finance, Healthcare, Energy, etc.)
  - `get_sector_tickers(sector, limit)` function
  - `get_all_sectors()` function
- ✅ `backend/tools/relative_strength.py`:
  - Correlation analysis between stock price movements
  - Relative performance normalization
  - Sharpe ratio calculations
  - Valuation comparison (P/E, P/S, EV/EBITDA)

**Backend Workflow Integration:**

- ✅ `backend/graph/workflow.py::run_comparison_streaming()` method
- ✅ Runs all analyst agents for each ticker in parallel
- ✅ Risk assessment for each ticker
- ✅ Chairperson comparison step (ranks and rationales)
- ✅ Streams results as they complete

**Frontend Components & Pages:**

- ✅ `ComparePage.tsx` at `/compare` route (partial implementation)
- ✅ `ComparisonTable.tsx` — tabular view with metrics and highlights:
  - P/E Ratio, Revenue Growth, Debt/Equity, Sentiment, RSI
  - Highlights best/worst per metric (green/red)
- ✅ `RelativePerformanceChart.tsx` — multi-line chart:
  - Overlaid normalized price history
  - Multiple series support (up to 6 different colors)
  - Uses lightweight-charts
- ✅ `PresetSelector.tsx` — preset watchlist/sector selection
- ✅ App routing to `/compare` with ProtectedRoute

**State & Types:**

- ✅ `ComparisonResult` TypedDict with rankings, best_pick, summary (`frontend/src/types/comparison.ts`)
- ✅ `RelativeStrength` TypedDict with metrics
- ✅ `WSMessageType.COMPARISON_RESULT` enum

### ✅ ALL COMPLETE

All Phase 3 features have been implemented:

- ✅ Comparison endpoint wired into API
- ✅ `ComparePage.tsx` with full multi-ticker input (2-4 stocks)
- ✅ Manual and sector comparison modes
- ✅ `ComparisonTable.tsx` — tabular metrics view
- ✅ `RelativePerformanceChart.tsx` — normalized price overlay charts
- ✅ `RankingCard.tsx` — Chairperson's ranked comparison
- ✅ Dashboard integration with quick comparison actions
- ✅ WebSocket support for streaming comparison results
- ✅ Comprehensive test coverage for comparison workflows

### Performance Notes

- 4 stocks × 3 agents = 12 parallel LLM calls (monitor rate limits)
- Consider caching individual analyses for re-comparisons
- "Quick compare" mode could skip expensive agents

### Impact When Complete

- Answer "Which should I buy: AAPL or MSFT?" type questions
- Sector-level analysis provides macro context
- Relative strength metrics for better decision-making

---

## Phase 4a: Alerts & Notifications ✅ 100% COMPLETE

Enable users to set price alerts and receive real-time notifications.

### ✅ COMPLETED

**Backend Database Models:**

- `PriceAlert` table with ticker, market, condition (above/below/change_pct), target_value, triggered status, cooldown, active flag
- `Notification` table with type (price_alert, analysis_complete, veto_alert), title, body, JSONB data, read status
- `AlertCondition` enum: ABOVE, BELOW, CHANGE_PCT
- `NotificationType` enum: PRICE_ALERT, ANALYSIS_COMPLETE, RECOMMENDATION_CHANGE, VETO_ALERT
- FK relationships from PriceAlert and Notification to User with CASCADE delete
- Composite indexes for efficient job queries

**Backend DAO Layer:**

- `PriceAlertDAO` with methods: get_user_alerts, get_active_alerts_for_ticker, get_all_active_tickers, reset_alert, count_user_alerts
- `NotificationDAO` with methods: get_user_notifications, get_unread_count, mark_as_read, mark_all_read
- Cooldown filtering in queries to prevent spam

**Backend Services Layer:**

- `create_price_alert()` with validation: max 50 alerts per user, target_value > 0, change_pct 0.1-100
- `trigger_alert()` creates notification, updates alert status, sets 1-hour cooldown, sends WebSocket notification
- `create_analysis_notification()` for future scheduled analysis feature (Phase 4b)

**Backend Background Jobs:**

- `check_price_alerts()` job runs every 5 minutes during market hours (9:30 AM - 4:00 PM ET, Mon-Fri)
- Batch fetches prices for all tickers with active alerts (single API call per ticker)
- Evaluates alert conditions: ABOVE, BELOW, CHANGE_PCT
- Creates notifications and triggers WebSocket push for triggered alerts
- Respects cooldown period to prevent alert spam

**Backend WebSocket Integration:**

- `ConnectionManager` class tracks active WebSocket connections per user (multi-device support)
- `connect()`, `disconnect()`, `send_notification()` methods
- Integrated into existing `/ws/analyze` endpoint for persistent connections
- Notifications pushed in real-time when alerts trigger
- Added `NOTIFICATION` message type to `WSMessageType` enum

**Backend REST API Endpoints:**

- ✅ `POST /api/alerts` — create price alert with validation
- ✅ `GET /api/alerts?active_only=true` — list user's alerts
- ✅ `DELETE /api/alerts/{id}` — delete alert (ownership check)
- ✅ `PATCH /api/alerts/{id}/reset` — reset triggered alert
- ✅ `PATCH /api/alerts/{id}/toggle` — toggle active/paused status
- ✅ `GET /api/notifications?unread_only=false&limit=50` — list notifications
- ✅ `GET /api/notifications/unread-count` — get unread count for badge
- ✅ `PATCH /api/notifications/{id}/read` — mark notification as read
- ✅ `POST /api/notifications/read-all` — mark all notifications as read

**Frontend Components:**

- `NotificationBell.tsx` — bell icon with unread badge, popover dropdown, mark as read/all functionality
- Integrated into Dashboard header next to History button
- Uses WebSocket hook for real-time notifications
- Formats timestamps (e.g., "5m ago", "3h ago", "2d ago")
- Icons per notification type: 💰 price_alert, ✅ analysis_complete, ⚠️ veto_alert

**Frontend Pages:**

- `AlertsPage.tsx` — full alert management UI
- Create new alert form: ticker, market, condition, target value
- Alert list with cards showing ticker, condition, target, triggered/paused status
- Action buttons: toggle active/pause, reset triggered, delete
- Info card explaining market hours, cooldown, and rate limits
- Navigation from Dashboard via "Alerts" button

**Frontend WebSocket Hook:**

- Updated `useWebSocket.ts` to handle `notification` message type
- `latestNotification` state exposed for components
- Notifications processed separately from analysis messages

**Database Migration:**

- Migration `cc6231cabf3b_add_alerts_notifications.py`
- Creates `alertcondition` and `notificationtype` PostgreSQL enums
- Creates `price_alerts` and `notifications` tables with indexes
- Uses existing `market` enum (adds TASE value if needed)
- Proper CASCADE delete on foreign keys

**Tests:**

- Unit tests for alert condition logic (above, below, change_pct)
- Tests for cooldown and rate limiting logic
- Integration tests for alert checker job with mocked market data
- Tests for market hours detection

### Business Rules Implemented

- **Rate Limiting**: Maximum 50 alerts per user
- **Cooldown**: 1-hour cooldown after triggering to prevent spam
- **Market Hours**: Alerts only checked during US market hours (9:30 AM - 4:00 PM ET, Mon-Fri)
- **Validation**: Target value must be > 0; change_pct must be 0.1-100
- **Multi-Device**: WebSocket notifications sent to all active user connections
- **Graceful Degradation**: WebSocket failures don't break alert triggering

### ✅ ALL COMPLETE

All Phase 4a features have been implemented and tested:

- ✅ Price alert creation and management
- ✅ Real-time notification delivery via WebSocket
- ✅ Background job checking alerts every 5 minutes
- ✅ Notification center with unread badge
- ✅ Alert management page with CRUD operations
- ✅ Database migration successfully applied
- ✅ Tests passing for core alert logic
- ✅ Multi-device notification support

### Known Limitations (Phase 4b Enhancements)

- **US Market Only**: Market hours check supports US market only (TASE support pending)
- **Change_pct Baseline**: Uses alert creation price as baseline (will store baseline in 4b)
- **In-Memory Connections**: ConnectionManager won't scale to multi-server (needs Redis pub/sub)
- **No Email/SMS**: Notifications are in-app only (email via SendGrid in 4b)
- **No Scheduled Analysis**: Automated analysis triggers coming in Phase 4b

### Impact

- Users can set automated price alerts without manual checking
- Real-time notifications keep users informed of price movements
- Foundation for Phase 4b scheduled analysis and enhanced notifications
- Reduced need for constant dashboard monitoring

---

## User Settings Page ✅ 100% COMPLETE

Comprehensive user settings management with profile updates, password changes, and API key management.

### ✅ COMPLETED

**Backend Services Layer:**

- ✅ `SettingsService` in `backend/services/settings/service.py`:
  - `update_profile()` — update user profile fields (first_name, last_name, email)
  - `change_password()` — change password with current password validation
  - `get_api_keys_masked()` — retrieve masked API keys for display
  - `upsert_api_key()` — create or update LLM provider API keys
  - `delete_api_key()` — remove API keys by provider
  - API key encryption using Fernet with JWT secret-derived key
  - Email uniqueness validation
  - Password strength validation (min 8 chars)

**Backend Exception Handling:**

- ✅ Custom exceptions in `backend/services/settings/exceptions.py`:
  - `SettingsError` — base exception for settings operations
  - `EmailAlreadyTakenError` — email conflict detection
  - `InvalidPasswordError` — password validation failures

**Backend Schemas:**

- ✅ Request/response models in `backend/api/settings/schemas.py`:
  - `ProfileUpdate` — partial profile update with optional fields
  - `ProfileResponse` — user profile data response
  - `PasswordChange` — password change request with validation
  - `APIKeyCreate` — API key creation/update
  - `APIKeyResponse` — masked API key response

**Backend REST API Endpoints:**

- ✅ `GET /api/settings/profile` — get current user profile
- ✅ `PATCH /api/settings/profile` — update profile fields
- ✅ `POST /api/settings/password` — change password
- ✅ `GET /api/settings/api-keys` — list API keys (masked)
- ✅ `POST /api/settings/api-keys` — create/update API key for provider
- ✅ `DELETE /api/settings/api-keys/{provider}` — delete API key
- ✅ All endpoints use JWT authentication
- ✅ Proper HTTP status codes (409 for conflicts, 404 for not found)

**Backend Router Integration:**

- ✅ Settings router registered in `backend/api/__init__.py`
- ✅ Mounted at `/api/settings` prefix
- ✅ Integrated with main API router

**Frontend Page:**

- ✅ `SettingsPage.tsx` — comprehensive settings UI:
  - Three tabbed sections: Profile, Password, API Keys
  - Profile section: edit first name, last name, email
  - Password section: current password validation, new password input
  - API Keys section: add/update/delete keys for Anthropic, OpenAI, Gemini
  - Real-time form validation
  - Success/error toast notifications
  - Loading states for all operations
  - Masked API key display with show/hide toggle
  - Provider icons and labels
  - Responsive design with glass theme styling

**Frontend Routing:**

- ✅ Route registered in `App.tsx` at `/settings`
- ✅ Protected route requiring authentication
- ✅ Navigation from Dashboard via Settings button
- ✅ Navbar includes Settings link (in upcoming refactor)

**Security Features:**

- ✅ API key encryption at rest using Fernet
- ✅ Encryption key derived from JWT secret via SHA-256
- ✅ Masked API key display (shows first 4 and last 3 chars)
- ✅ Current password validation before password change
- ✅ Email uniqueness enforcement
- ✅ Secure key storage in database
- ✅ User-scoped API key access (users can only see/modify their own keys)

**User Experience Features:**

- ✅ Inline form validation with error messages
- ✅ Success confirmations for all operations
- ✅ Graceful error handling with user-friendly messages
- ✅ Form reset after successful password change
- ✅ Visual feedback for loading states
- ✅ Provider-specific icons and labels
- ✅ Consistent glass theme styling
- ✅ Mobile-responsive layout

### Business Rules Implemented

- **Email Uniqueness**: Cannot change email to one already in use by another user
- **Password Validation**: New password must be 8-128 characters
- **Current Password Required**: Must provide current password to change password
- **API Key Encryption**: All API keys encrypted before storage
- **User Isolation**: Users can only access their own settings and API keys
- **Provider Support**: Supports Anthropic (Claude), OpenAI (GPT-4), Google (Gemini)
- **Key Masking**: API keys displayed as masked (e.g., "sk-a...xyz") for security

### ✅ ALL COMPLETE

All User Settings Page features have been implemented and tested:

- ✅ Profile management with email conflict detection
- ✅ Password change with validation
- ✅ API key CRUD operations with encryption
- ✅ Comprehensive frontend UI with all features
- ✅ Integration with authentication system
- ✅ Proper error handling and user feedback
- ✅ Security best practices (encryption, validation)

### Impact

- Users can manage their profile information
- Secure password updates with validation
- Multi-provider LLM API key management
- Foundation for user-specific LLM provider preferences
- Enhanced security with encrypted API key storage
- Self-service account management reduces support burden

**Status:** Production-ready. All User Settings goals met.

---

## Frontend Refactoring: Consistent Layout & Styling ✅ 100% COMPLETE

Standardize all pages to share a common layout structure (navbar, footer, containers) and fix styling inconsistencies.

### ✅ COMPLETED

1. **No shared layout** — each page builds its own header/navigation independently
2. **No global navbar** — Dashboard has inline nav buttons, other pages use ad-hoc back buttons
3. **No footer** — no page has a footer component
4. **Container width inconsistency** — `max-w-4xl` (alerts, schedules), `max-w-7xl` (dashboard, compare), none (portfolio, performance)
5. **Header duplication** — 3+ pages copy-paste the same back-button + title + action-button pattern
6. **Hardcoded colors** — `PerformanceSummary.tsx` uses `bg-gray-800`, `text-gray-400` instead of theme CSS variables
7. **Performance page missing header** — no navigation or back button at all
8. **Inconsistent padding/spacing** — varies across pages with no standard

### Plan

#### Step 1: Create Shared Layout Components

- **`AppLayout.tsx`** — top-level layout wrapper used by all authenticated pages
  - Renders persistent **Navbar** at top
  - Renders persistent **Footer** at bottom
  - Renders `<Outlet />` (React Router) or `children` for page content
  - Handles the animated background effects (move from App.tsx)

- **`Navbar.tsx`** — global navigation bar (replaces per-page headers)
  - Left: Boardroom logo/branding
  - Center: Navigation links (Dashboard, Compare, Portfolio, Alerts, Settings, Performance, Schedules)
  - Right: NotificationBell + user email + logout button
  - Active route highlighting
  - Mobile responsive: hamburger menu / collapsible nav
  - Consistent 56px height, glass styling (`bg-card/30 backdrop-blur-md border-b border-white/10`)

- **`Footer.tsx`** — simple footer
  - Branding / copyright
  - Links to key sections
  - Minimal, matches glass theme

- **`PageContainer.tsx`** — standardized content wrapper
  - Props: `maxWidth` (`narrow` = max-w-4xl, `wide` = max-w-7xl, `full` = no max-width)
  - Consistent padding (`px-6 py-6`)
  - Optional page title + description header section

#### Step 2: Migrate All Pages to Shared Layout

- **App.tsx** — wrap authenticated routes in `<AppLayout>` using React Router layout route
- **Dashboard** — remove inline header/nav buttons, keep WatchlistSidebar (page-specific)
- **ComparePage** — remove custom header, use `PageContainer maxWidth="wide"`
- **PortfolioPage** — remove custom header, use `PageContainer maxWidth="wide"`, add consistent max-width
- **AlertsPage** — remove custom header, use `PageContainer maxWidth="narrow"`
- **SchedulesPage** — remove custom header, use `PageContainer maxWidth="narrow"`
- **PerformancePage** — add to shared layout (currently has no header), use `PageContainer maxWidth="wide"`
- **AuthPage** — stays outside `AppLayout` (no navbar/footer for unauthenticated users)

#### Step 3: Fix Styling Inconsistencies

- **PerformanceSummary.tsx** — replace hardcoded `bg-gray-800`, `text-gray-400` with theme variables (`bg-card`, `text-muted-foreground`, `.glass`)
- **All performance components** — audit and align with glass theme
- **Standardize card patterns** — ensure all pages use `.glass` utility consistently
- **Audit spacing** — normalize section gaps, card padding, content margins

#### Step 4: Responsive Design Pass

- Navbar collapses to hamburger/drawer on mobile
- WatchlistSidebar behavior on mobile (overlay vs hidden)
- Page containers adapt padding for mobile
- Footer stacks vertically on small screens

#### Step 5: Polish & QA

- Verify all pages render correctly with new layout
- Test navigation flow (active states, transitions)
- Check mobile breakpoints across all pages
- Ensure WebSocket connections and auth context still work within new layout structure

### Files to Create

- `frontend/src/components/layout/AppLayout.tsx`
- `frontend/src/components/layout/Navbar.tsx`
- `frontend/src/components/layout/Footer.tsx`
- `frontend/src/components/layout/PageContainer.tsx`

### Files to Modify

- `frontend/src/App.tsx` — use layout routes
- `frontend/src/components/Dashboard.tsx` — remove inline header/nav
- `frontend/src/pages/ComparePage.tsx` — remove custom header
- `frontend/src/pages/PortfolioPage.tsx` — remove custom header
- `frontend/src/pages/AlertsPage.tsx` — remove custom header
- `frontend/src/pages/SchedulesPage.tsx` — remove custom header
- `frontend/src/pages/PerformancePage.tsx` — remove custom header, add PageContainer
- `frontend/src/components/performance/PerformanceSummary.tsx` — fix hardcoded colors

### Dependencies

- None (can be done independently of backend work)

### ✅ ALL COMPLETE

All Frontend Refactoring tasks have been completed:

- ✅ Shared layout components created (`AppLayout`, `Navbar`, `Footer`, `PageContainer`)
- ✅ `App.tsx` routes updated to use layout wrapper
- ✅ `Dashboard` migrated to shared layout
- ✅ `ComparePage` migrated to `PageContainer`
- ✅ `PortfolioPage` migrated to `PageContainer`
- ✅ `AlertsPage` migrated to `PageContainer`
- ✅ `SchedulesPage` migrated to `PageContainer`
- ✅ `PerformancePage` migrated to `PageContainer`
- ✅ `SettingsPage` migrated to `PageContainer`
- ✅ Styling inconsistencies fixed (colors, spacing, glass effect)
- ✅ Responsive design verified (mobile menu, collapsing sidebar)

### Impact

- Improves maintainability and developer velocity for all future frontend work
- Fixes user-facing inconsistencies and provides a polished, professional look

---

## Phase 4b: Scheduled Analysis & Enhanced Notifications ✅ 100% COMPLETE

Automated analysis execution and enhanced notification features fully implemented.

### ✅ COMPLETED

**Backend Database Models:**

- ✅ `ScheduledAnalysis` table with ticker, market, frequency (daily/weekly/on_change), last_run, next_run, active flag
- ✅ `AlertFrequency` enum: DAILY, WEEKLY, ON_CHANGE
- ✅ Added `baseline_price` column to `PriceAlert` for accurate change_pct calculations
- ✅ Added `notification_email` column to `User` for SendGrid foundation
- ✅ Indexes on scheduled_analyses (next_run, active) for efficient job queries

**Backend DAO Layer:**

- ✅ `ScheduledAnalysisDAO` with methods:
  - `get_user_schedules()` — list user's scheduled analyses
  - `get_due_schedules()` — get schedules ready to run (active, next_run <= now)
  - `update_run_times()` — update last_run and next_run after execution
  - `count_user_schedules()` — rate limiting (max 50 schedules)
  - `get_by_ticker_market_frequency()` — duplicate detection
- ✅ `NotificationDAO.find_recent_by_ticker()` — find notifications within 15-minute window for grouping

**Backend Services Layer:**

- ✅ Enhanced `create_price_alert()` to fetch and store baseline price for change_pct alerts
- ✅ Enhanced `trigger_alert()` with notification grouping logic:
  - Checks for recent notifications (15-minute window)
  - Groups similar notifications instead of creating duplicates
  - Increments grouped_count and updates timestamp
  - Shows count in title: "AAPL Above $200 (3x)"
- ✅ `EmailService` class with SendGrid integration foundation:
  - `send_price_alert_email()` — formatted price alert emails
  - `send_analysis_complete_email()` — scheduled analysis results
  - HTML email templates with responsive design
  - Feature flag: `email_notifications_enabled` (default: false)
  - Stub implementation (logs emails, doesn't send yet)

**Backend Background Jobs:**

- ✅ `run_scheduled_analyses()` job runs every 15 minutes:
  - Gets all due schedules (next_run <= now, active=True)
  - Runs BoardroomGraph analysis for each schedule
  - Creates notifications for completed analyses
  - Calculates next_run based on frequency using `calculate_next_run()`
  - Updates schedule timestamps
- ✅ `calculate_next_run()` function with timezone-aware scheduling:
  - DAILY: 8 AM ET before market open (Mon-Fri), skips weekends
  - WEEKLY: Monday 8 AM ET
  - ON_CHANGE: Every hour during market hours (10 AM - 4 PM ET)
  - Uses ZoneInfo for proper timezone handling
- ✅ `is_tase_market_hours()` — TASE market hours detection:
  - 10:00 AM - 4:45 PM IST
  - Sunday-Thursday (Israeli trading week)
  - Proper timezone handling with Asia/Jerusalem
- ✅ Enhanced `check_price_alerts()` to use stored baseline_price for change_pct alerts
- ✅ Enhanced `is_market_hours()` dispatch function for multi-market support

**Backend REST API Endpoints:**

- ✅ `POST /api/schedules` — create scheduled analysis (validates duplicates, rate limit)
- ✅ `GET /api/schedules` — list user's schedules
- ✅ `DELETE /api/schedules/{id}` — delete schedule (ownership check)
- ✅ `PATCH /api/schedules/{id}/toggle` — pause/resume schedule (recalculates next_run on reactivation)
- ✅ Routers registered in `backend/api/__init__.py`

**Backend Configuration:**

- ✅ Added SendGrid settings to `backend/core/settings.py`:
  - `sendgrid_api_key` — API key for SendGrid
  - `sendgrid_from_email` — sender email address
  - `sendgrid_from_name` — sender name
  - `email_notifications_enabled` — feature flag

**Frontend Components:**

- ✅ `SchedulesPage.tsx` — scheduled analysis management UI:
  - Create schedule form: ticker, market, frequency
  - Schedule list with ticker, market, frequency, next run, last run
  - Action buttons: toggle active/pause, delete
  - Status badges: Active (green), Paused (gray)
  - Smart time formatting: "in 5 min", "Tomorrow", "2d ago"
  - Info card explaining schedule frequencies
  - Empty state with helpful message
- ✅ Enhanced `Dashboard.tsx` with connection status indicators:
  - 🔵 Connecting... (blue pulsing dot)
  - 🟡 Reconnecting... (yellow pulsing dot with attempt counter)
  - Hidden when connected (clean UI)

**Frontend WebSocket Hook:**

- ✅ Enhanced `useWebSocket.ts` with automatic reconnection:
  - Connection states: disconnected, connecting, connected, reconnecting
  - Exponential backoff: 1s → 2s → 4s → 8s → 16s → 30s (max)
  - Max retry attempts: 5 before giving up
  - Request caching: stores last request and auto-retries after reconnection
  - Manual retry bypasses backoff delay
  - Graceful cleanup on logout/token change
  - Error messages show attempt count: "Reconnecting... (Attempt 2/5)"

**Database Migration:**

- ✅ Migration `a9ac28963d31_add_phase_4b_features.py`:
  - Created `alertfrequency` enum
  - Created `scheduled_analyses` table with indexes
  - Added `baseline_price` column to `price_alerts`
  - Added `notification_email` column to `users`
  - Proper CASCADE delete on foreign keys

**Tests:**

- ✅ `test_scheduled_analysis.py` — calculate_next_run() logic:
  - Daily schedule before/after 8 AM
  - Daily schedule skips weekends
  - Weekly schedule calculation
  - On-change schedule during/before/after market hours
  - On-change schedule skips weekends
- ✅ `test_market_hours.py` — TASE and US market hours detection:
  - US market hours (9:30 AM - 4:00 PM ET, Mon-Fri)
  - TASE market hours (10:00 AM - 4:45 PM IST, Sun-Thu)
  - Market hours dispatch function
  - Timezone handling
- ✅ `test_notification_grouping.py` — notification grouping logic:
  - First alert creates new notification
  - Second alert within 15 minutes groups with first
  - Grouped notification shows count in title
  - Different tickers create separate notifications
  - Old notifications (>15 min) not grouped
  - Grouped notification marks as unread
  - Grouped notification updates timestamp
- ✅ `test_email_service.py` — email service foundation:
  - Service enabled/disabled based on API key and feature flag
  - Email template generation (price alerts, analysis complete, veto alerts)
  - Subject line formatting
  - HTML content validation
  - Stub implementation returns success

### Business Rules Implemented

- **Rate Limiting**: Maximum 50 scheduled analyses per user
- **Duplicate Prevention**: Cannot create duplicate schedules (same ticker + market + frequency)
- **Smart Scheduling**:
  - Daily: 8 AM ET before market open (Mon-Fri), skips weekends
  - Weekly: Monday 8 AM ET
  - On-change: Every hour during market hours (10 AM - 4 PM ET)
- **Notification Grouping**: Similar notifications within 15 minutes are grouped
- **Multi-Market Support**: Proper timezone handling for US (ET) and TASE (IST)
- **WebSocket Resilience**: Automatic reconnection with exponential backoff (max 5 attempts)
- **Email Foundation**: SendGrid integration ready (stub implementation, not sending yet)

### ✅ ALL COMPLETE

All Phase 4b features have been implemented and tested:

- ✅ Scheduled analysis automation
- ✅ TASE market hours support
- ✅ Enhanced change_pct with baseline price storage
- ✅ WebSocket reconnection with exponential backoff
- ✅ Notification grouping to prevent spam
- ✅ SendGrid email service foundation
- ✅ Scheduled analysis API endpoints
- ✅ Scheduled analysis frontend page
- ✅ Database migration successfully applied
- ✅ Comprehensive test suite passing

### Known Limitations (Future Enhancements)

- **Email Sending**: SendGrid stub implemented but not sending actual emails (requires API key configuration)
- **In-Memory Connections**: WebSocket ConnectionManager won't scale to multi-server (needs Redis pub/sub)
- **No SMS**: Only in-app and email notifications (SMS via Twilio in future)
- **No Notification History**: Notifications are not archived after deletion
- **Fixed Grouping Window**: 15-minute grouping window is hardcoded (could be user-configurable)

### Impact

- Users can automate stock analysis without manual intervention
- Multi-market support enables global trading strategies
- Notification grouping reduces spam and improves UX
- WebSocket reconnection improves reliability for mobile/flaky connections
- Email foundation ready for production deployment
- Foundation for Phase 5 backtesting (automated analysis data)

**Dependencies:** Phase 4a (alerts infrastructure)

**Status:** Production-ready. All Phase 4b goals met.

---

## Phase 5: Backtesting & Simulation ⏳ 0% NOT STARTED

Allow users to test strategies on historical data.

**Planned:**

- Paper trading engine
- Historical replays
- Performance simulation
- Strategy builder

**Dependencies:** Phase 2 (performance tracking data)

**Priority:** Low

---

## Phase 6: Export & Reporting ⏳ 0% NOT STARTED

Export analyses and generate reports.

**Planned:**

- PDF report generation
- CSV export
- API key management for user integrations
- Webhook support for external systems

**Priority:** Low

---

## Quick Wins 🚧 IN PROGRESS

Small improvements that can be done anytime.

**Examples:**

- Dark mode toggle
- Keyboard shortcuts
- Analysis result copying
- Performance metric filters
- Sentiment indicator icons

---

## Next Steps

**Phases 0-4b Complete:** ✅ Core functionality + alerts & notifications + scheduled analysis fully implemented and integrated.

**Immediate Priority (ready to implement):**

1. **Phase 5: Backtesting & Simulation** (~3-4 days):
   - Paper trading engine with simulated portfolio
   - Historical price replay system
   - Strategy builder UI
   - Performance simulation on past data
   - Comparison of simulated vs real outcomes
   - Tests: paper trading accuracy, price replay logic

2. **Phase 6: Export & Reporting** (~2-3 days):
   - PDF report generation for analyses
   - CSV export of performance metrics
   - API key management for user integrations
   - Webhook support for external systems
   - Scheduled report delivery
   - Tests: PDF generation, export formats

**Quick Wins (can be done anytime):**

- Dark mode toggle
- Keyboard shortcuts for quick analysis
- Result copying to clipboard
- Advanced filtering in history
- Custom alert thresholds UI
- Performance metric comparisons

---

## Current Issues & Blockers

**All Major Blockers Resolved:** ✅

Phases 0-3 are complete and fully integrated. No outstanding blockers.

**Known Limitations:**

- Export functionality not yet implemented (Phase 6)
- Alerting system not yet implemented (Phase 4)
- Backtesting/simulation not yet implemented (Phase 5)
- Real-time P&L updates require periodic price refreshes (acceptable for current scope)

---

## File Reference

**Backend Architecture (Layered & Modular):**

- **Database Models:** `backend/dao/models.py`
- **Auth Layer:** `backend/auth/` (jwt.py, dependencies.py)
- **API Routers (Modular by domain):**
  - `backend/api/auth/endpoints.py` — Auth endpoints
  - `backend/api/watchlists/endpoints.py` — Watchlist CRUD
  - `backend/api/portfolios/endpoints.py` — Portfolio CRUD
  - `backend/api/analysis/endpoints.py` — Analysis history and single-stock analysis
  - `backend/api/sectors/endpoints.py` — Sector/comparison endpoints
  - `backend/api/websocket/endpoints.py` — WebSocket /ws/analyze
  - `backend/api/routes.py` — Utility endpoints (markets, cache, search)
- **Background Jobs:** `backend/jobs/scheduler.py`, `backend/jobs/outcome_tracker.py`
- **Services Layer:** `backend/services/` (business logic)
- **Core Module:** `backend/core/` (cache, configuration)
- **AI Module:** `backend/ai/` (agents, tools, workflow)
- **Database Migrations:** `alembic/versions/`

**Frontend:**

- **Pages:** `frontend/src/pages/` (AuthPage, PortfolioPage, ComparePage, PerformancePage)
- **Components:** `frontend/src/components/` (Dashboard, AgentPanel, DecisionCard, etc.)
- **Performance Components:** `frontend/src/components/performance/` (PerformanceSummary, AccuracyChart, AgentLeaderboard, RecentOutcomes)
- **Hooks:** `frontend/src/hooks/useWebSocket.ts` — WebSocket state management
- **Contexts:** `frontend/src/contexts/AuthContext.tsx` — Auth state and JWT management
- **Types:** `frontend/src/types/` (agent, comparison, performance types)
