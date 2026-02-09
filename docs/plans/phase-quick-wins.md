# Quick Wins

Improvements that can be done independently, in parallel with any phase. Each is self-contained and small in scope.

---

## QW-1: Candlestick Chart + Technical Overlays

**Current state:** `StockChart.tsx` uses lightweight-charts `AreaSeries` for a simple area chart.

**Improvement:**
- Add candlestick chart option using lightweight-charts `CandlestickSeries`
- Overlay MA50 and MA200 lines (data already available in `TechnicalReport.ma_50`, `TechnicalReport.ma_200`)
- Add RSI sub-chart below the main price chart
- Volume bars at the bottom

**Files:**
- Modify `frontend/src/components/StockChart.tsx` — add chart type toggle, overlays
- Modify `backend/state/agent_state.py` — include OHLCV in `price_history` (currently just close prices)
- Modify `backend/tools/technical_indicators.py` — return full OHLCV data

**Effort:** Small (1-2 sessions)

---

## QW-2: Dark/Light Mode Toggle

**Current state:** Dark mode only (hardcoded dark theme in Tailwind/CSS).

**Improvement:**
- Add theme toggle button in header
- Use shadcn's built-in theme support (CSS variables already set up)
- Store preference in localStorage
- Light theme with matching color tokens

**Files:**
- Create `frontend/src/components/ThemeToggle.tsx`
- Create `frontend/src/contexts/ThemeContext.tsx`
- Modify `frontend/src/index.css` — add light theme CSS variables
- Modify `frontend/src/components/Dashboard.tsx` — add toggle to header

**Effort:** Small (1 session)

---

## QW-3: Mobile Responsive Layout

**Current state:** Dashboard uses grid layout that works on desktop but agent panels stack poorly on mobile.

**Improvement:**
- Responsive breakpoints for agent grid (1 col mobile, 2 col tablet, 4 col desktop)
- Collapsible agent panels on mobile (tap to expand)
- Bottom sheet for ticker input on mobile
- Swipeable agent cards
- Touch-friendly chart interactions

**Files:**
- Modify `frontend/src/components/Dashboard.tsx` — responsive grid classes
- Modify `frontend/src/components/AgentPanel.tsx` — collapsible state
- Modify `frontend/src/components/TickerInput.tsx` — mobile layout

**Effort:** Medium (2-3 sessions)

---

## QW-4: Analysis Presets

**Current state:** Every analysis runs the full pipeline with all agents.

**Improvement:**
- Quick Scan: Technical analysis only (fastest, no LLM calls needed for indicators)
- Standard: All agents (current behavior)
- Deep Dive: All agents + additional data sources, longer LLM context
- Add preset selector next to the ticker input

**Backend changes:**
- Add `analysis_mode` parameter to WebSocket command
- Conditionally skip agents based on mode in `BoardroomGraph.run_streaming()`
- Quick Scan skips sentiment and fundamental agents

**Files:**
- Modify `backend/graph/workflow.py` — accept and handle `analysis_mode`
- Modify `backend/api/websocket.py` — pass mode from client
- Create `frontend/src/components/PresetSelector.tsx` — dropdown/toggle
- Modify `frontend/src/components/TickerInput.tsx` — integrate preset selector
- Modify `frontend/src/hooks/useWebSocket.ts` — send mode in request

**Effort:** Small (1-2 sessions)

---

## QW-5: More Technical Indicators

**Current state:** `backend/tools/technical_indicators.py` calculates MA50, MA200, RSI.

**Improvement:**
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands (20-day, 2 standard deviations)
- Fibonacci retracement levels
- ATR (Average True Range) for volatility
- Add these to `TechnicalReport` and display in the technical agent panel

**Files:**
- Modify `backend/tools/technical_indicators.py` — add new indicator calculations
- Modify `backend/state/agent_state.py` — extend `TechnicalReport` with new fields
- Modify `backend/agents/technical.py` — include new indicators in analysis prompt
- Modify `frontend/src/components/AgentPanel.tsx` — display new metrics

**Effort:** Medium (2 sessions)

---

## QW-6: International Markets

**Current state:** `Market` enum supports US and TASE only.

**Improvement:**
- Add support for: LSE (London), TSE (Tokyo), HKEX (Hong Kong), Xetra (Frankfurt)
- Market-specific data source configuration
- Currency display (USD, ILS, GBP, JPY, HKD, EUR)
- Trading hours awareness per market

**Files:**
- Modify `backend/state/enums.py` — extend `Market` enum
- Modify `backend/tools/market_data.py` — market-specific Yahoo Finance suffixes
- Modify `backend/tools/stock_search.py` — search across new markets
- Modify `frontend/src/components/TickerInput.tsx` — market selector update

**Effort:** Medium (2-3 sessions)

---

## QW-7: Loading Experience Polish

**Current state:** Simple skeleton loaders and spinner badges while agents run.

**Improvement:**
- Typing indicator for LLM responses (stream partial text as it generates)
- Agent "thought process" display — show what tools each agent is calling
- Estimated time remaining based on historical agent completion times
- Sound effect on analysis complete (optional, toggleable)
- Confetti on BUY recommendation (optional, fun)

**Files:**
- Modify `backend/graph/workflow.py` — add intermediate progress events
- Modify `backend/state/enums.py` — add `WSMessageType.AGENT_PROGRESS`
- Modify `frontend/src/hooks/useWebSocket.ts` — handle progress events
- Modify `frontend/src/components/AgentPanel.tsx` — display progress details

**Effort:** Medium (2-3 sessions)

---

## QW-8: Error Recovery & Retry

**Current state:** If an agent fails, the whole analysis may fail silently or show a generic error.

**Improvement:**
- Per-agent error handling: If one agent fails, continue with others
- Retry button per agent: "Sentiment agent failed. Retry?"
- Graceful degradation: Show results from agents that succeeded
- Error details: Show what went wrong (API limit, timeout, etc.)
- Auto-retry with exponential backoff for transient failures

**Backend changes:**
- Wrap each agent in try/except in `BoardroomGraph.run_streaming()`
- Emit `WSMessageType.AGENT_ERROR` with error details
- Chairperson handles missing reports gracefully

**Files:**
- Modify `backend/graph/workflow.py` — per-agent error handling
- Modify `backend/state/enums.py` — add `AGENT_ERROR` message type
- Modify `frontend/src/hooks/useWebSocket.ts` — handle errors per agent
- Modify `frontend/src/components/AgentPanel.tsx` — error state with retry button

**Effort:** Small-Medium (1-2 sessions)

---

## QW-9: Keyboard Shortcuts

**Current state:** Only Enter to submit and Esc to clear (per usage guide).

**Improvement:**
- `/` — focus ticker input from anywhere
- `1-4` — expand/focus agent panel 1-4
- `r` — re-run last analysis
- `w` — toggle watchlist sidebar (Phase 1)
- `?` — show keyboard shortcuts modal

**Files:**
- Create `frontend/src/hooks/useKeyboardShortcuts.ts`
- Create `frontend/src/components/ShortcutsModal.tsx`
- Modify `frontend/src/components/Dashboard.tsx` — integrate shortcuts

**Effort:** Small (1 session)

---

## Priority Ranking

| # | Quick Win | Impact | Effort | Priority |
|---|-----------|--------|--------|----------|
| 8 | Error Recovery & Retry | High | Small | Do first |
| 1 | Candlestick Chart + Overlays | High | Small | Do first |
| 4 | Analysis Presets | High | Small | Do first |
| 5 | More Technical Indicators | Medium | Medium | Do second |
| 2 | Dark/Light Mode | Medium | Small | Do second |
| 9 | Keyboard Shortcuts | Medium | Small | Do second |
| 3 | Mobile Responsive | Medium | Medium | Do third |
| 7 | Loading Polish | Low | Medium | Nice to have |
| 6 | International Markets | Low | Medium | Nice to have |
