# Frontend-Backend Integration Test Checklist

## Prerequisites
- [ ] Backend running at http://localhost:8000
- [ ] Frontend running at http://localhost:5173
- [ ] PostgreSQL database accessible
- [ ] Environment variables configured (.env file)
- [ ] At least one LLM API key configured (ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY)
- [ ] EXA_API_KEY configured for sentiment analysis

## Authentication Tests
- [ ] User registration works (`POST /api/auth/register`)
- [ ] User login works (`POST /api/auth/login`)
- [ ] Token stored in localStorage after successful login
- [ ] Protected route access works with token (`GET /api/auth/me`)
- [ ] Logout clears token from localStorage
- [ ] No 401 errors on authenticated pages when logged in
- [ ] Proper 401 error when accessing protected routes without token

## WebSocket Tests
- [ ] WebSocket connects successfully to `ws://localhost:8000/ws/analyze`
- [ ] Single stock analysis streams results in real-time
- [ ] All 5 agents (fundamental, sentiment, technical, risk, chairperson) stream their reports
- [ ] Comparison analysis works with 2+ stocks
- [ ] No WebSocket connection errors in browser console
- [ ] Reconnection works after manual disconnect
- [ ] Backtest WebSocket (`ws://localhost:8000/ws/backtest`) connects and streams progress

## Portfolio & Watchlist Tests
- [ ] Fetch portfolios (`GET /api/portfolios`)
- [ ] Create portfolio (`POST /api/portfolios`)
- [ ] Update portfolio name (`PATCH /api/portfolios/{id}`)
- [ ] Delete portfolio (`DELETE /api/portfolios/{id}`)
- [ ] Add positions to portfolio (`POST /api/portfolios/{id}/positions`)
- [ ] Remove positions from portfolio (`DELETE /api/portfolios/{id}/positions/{position_id}`)
- [ ] Fetch watchlists (`GET /api/watchlists`)
- [ ] Create watchlist (`POST /api/watchlists`)
- [ ] Add stocks to watchlist (`POST /api/watchlists/{id}/items`)
- [ ] Remove stocks from watchlist (`DELETE /api/watchlists/{id}/items/{item_id}`)

## Alerts Tests
- [ ] Fetch alerts (`GET /api/alerts`)
- [ ] Create price alert (`POST /api/alerts`)
  - [ ] Above threshold alert
  - [ ] Below threshold alert
  - [ ] Percentage change alert
- [ ] Toggle alert status (`PATCH /api/alerts/{id}/toggle`)
  - [ ] Active → Inactive
  - [ ] Inactive → Active
- [ ] Delete alert (`DELETE /api/alerts/{id}`)
- [ ] WebSocket notifications received when alert triggers
- [ ] Alert history displays correctly

## Scheduled Analysis Tests
- [ ] Fetch scheduled analyses (`GET /api/schedules`)
- [ ] Create scheduled analysis (`POST /api/schedules`)
  - [ ] Daily frequency
  - [ ] Weekly frequency
- [ ] Toggle schedule status (`PATCH /api/schedules/{id}/toggle`)
- [ ] Delete schedule (`DELETE /api/schedules/{id}`)
- [ ] Scheduled notifications appear in notifications list

## Performance Tracking Tests
- [ ] Agent leaderboard loads (`GET /api/performance/agents`)
  - [ ] Shows all 5 agents with accuracy metrics
  - [ ] Displays win rate, total predictions, and correct predictions
- [ ] Accuracy timeline loads (`GET /api/performance/timeline`)
  - [ ] Shows accuracy trend over time
  - [ ] Filterable by date range
- [ ] Recent outcomes display (`GET /api/performance/recent`)
  - [ ] Shows latest analysis outcomes with actual vs predicted
- [ ] Performance summary loads (`GET /api/performance/summary`)
  - [ ] Overall accuracy percentage
  - [ ] Total analysis count
- [ ] Individual agent performance (`GET /api/performance/agent/{agent_type}`)
  - [ ] Breakdown by action (BUY/SELL/HOLD)

## Comparison Analysis Tests
- [ ] Manual stock comparison (2-4 stocks)
  - [ ] Enter multiple tickers
  - [ ] Run comparison
  - [ ] Best pick displayed
  - [ ] Rankings shown with scores
- [ ] Sector comparison
  - [ ] Select sector from dropdown
  - [ ] Top 5 stocks analyzed
  - [ ] Relative performance chart displays
  - [ ] Side-by-side metrics table
- [ ] Price history chart renders correctly
- [ ] Comparison summary text generated

## Settings Tests
- [ ] Profile loads (`GET /api/settings/profile`)
  - [ ] Email displayed
  - [ ] Username displayed
- [ ] Profile update works (`PATCH /api/settings/profile`)
  - [ ] Update email
  - [ ] Update display name
- [ ] Password change works (`POST /api/settings/password`)
  - [ ] Validation for old password
  - [ ] Validation for new password strength
- [ ] API keys management
  - [ ] View API keys list (`GET /api/settings/api-keys`)
  - [ ] Create new API key (`POST /api/settings/api-keys`)
  - [ ] Delete API key (`DELETE /api/settings/api-keys/{id}`)

## Backtesting Tests
- [ ] Strategies list loads (`GET /api/strategies`)
- [ ] Strategy creation works (`POST /api/strategies`)
  - [ ] Custom agent weights
  - [ ] Buy/sell thresholds
  - [ ] Risk parameters
- [ ] Strategy update works (`PUT /api/strategies/{id}`)
- [ ] Strategy deletion works (`DELETE /api/strategies/{id}`)
- [ ] Backtest execution streams progress via WebSocket
  - [ ] Status updates received
  - [ ] Progress percentage updates
  - [ ] Completion message received
- [ ] Backtest results display
  - [ ] Summary metrics (win rate, total return, Sharpe ratio)
  - [ ] Trade log with all executed trades
  - [ ] Execution time displayed

## Paper Trading Tests
- [ ] Paper accounts list loads (`GET /api/paper/accounts`)
- [ ] Create paper account (`POST /api/paper/accounts`)
  - [ ] With initial balance
  - [ ] Linked to strategy
- [ ] Account details load with positions (`GET /api/paper/accounts/{id}?include_positions=true`)
  - [ ] Total value calculated correctly
  - [ ] Cash balance shown
  - [ ] P&L calculated
- [ ] Execute paper trade (`POST /api/paper/accounts/{id}/trades`)
  - [ ] BUY trade
  - [ ] SELL trade
  - [ ] Position updated after trade
- [ ] Trade history displays (`GET /api/paper/accounts/{id}/trades`)
- [ ] Account performance metrics accurate

## Browser Console Verification
- [ ] No 404 errors in browser console during normal usage
- [ ] No CORS errors in browser console
- [ ] No authentication errors (401/403) for logged-in users
- [ ] WebSocket connections establish without errors
- [ ] All network requests show correct base URL (`http://localhost:8000`)
- [ ] No hardcoded `localhost:8000` URLs in frontend code
- [ ] Environment variables (`VITE_API_URL`) properly used

## Network Tab Verification
- [ ] All API requests use the configured base URL
- [ ] Authorization headers present on protected endpoints
- [ ] Content-Type headers correct for POST/PUT requests
- [ ] Response status codes appropriate (200/201 for success, 400/401/404 for errors)
- [ ] WebSocket upgrade requests successful (status 101)

## Production Build Test
```bash
cd frontend
npm run build
npm run preview
```
- [ ] Production build completes without errors
- [ ] Preview server starts successfully
- [ ] All features work in production build
- [ ] Environment variables correctly embedded in build
- [ ] No hardcoded development URLs in production bundle

## Docker Production Test
```bash
docker compose -f docker/docker-compose.prod.yml up --build
```
- [ ] All services start successfully
- [ ] Frontend accessible on port 80
- [ ] Backend accessible from frontend container
- [ ] Database migrations run automatically
- [ ] Environment variables passed correctly to containers
- [ ] CORS configured correctly for production domain

## Success Criteria

All checkboxes above must be checked with:
- ✅ No 404 errors in browser console
- ✅ No CORS errors in browser console
- ✅ No authentication errors (401/403) for valid users
- ✅ All features functional as described
- ✅ WebSocket connections stable and reliable
- ✅ Production build works correctly
- ✅ Docker deployment successful

## Common Issues & Solutions

### 404 Errors
- **Problem:** API endpoints returning 404
- **Solution:** Check that `VITE_API_URL` is set correctly in frontend environment
- **Verify:** All `fetch()` calls use `API_BASE_URL` constant, not hardcoded URLs

### CORS Errors
- **Problem:** "Access-Control-Allow-Origin" errors
- **Solution:** Add frontend URL to `CORS_ORIGINS` in backend `.env`
- **Example:** `CORS_ORIGINS=http://localhost:5173,https://yourdomain.com`

### WebSocket Connection Failed
- **Problem:** WebSocket fails to connect
- **Solution:** Check `VITE_WS_URL` environment variable
- **Verify:** Backend WebSocket endpoint is accessible

### 401 Unauthorized
- **Problem:** Protected endpoints returning 401
- **Solution:** Ensure JWT token is stored in localStorage after login
- **Verify:** Authorization header is being sent with requests

### Environment Variables Not Working
- **Problem:** Frontend still using localhost:8000
- **Solution:** Restart development server after changing `.env` files
- **Note:** Vite only reads environment variables at build/start time

## Reporting Issues

If any test fails, please report with:
1. Which specific test failed
2. Error message from browser console
3. Network tab screenshot showing failed request
4. Steps to reproduce the issue
5. Environment details (OS, browser, Node version)
