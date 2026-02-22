# Quick Wins Design

**Date:** 2026-02-22
**Status:** Approved

## Context

Several quick wins were already implemented (QW-1 Candlestick Chart, QW-4 Analysis Presets, QW-8 Error Recovery). This document covers the remaining 6 items.

---

## QW-2: Fix Light Mode

**Problem:** `ThemeProvider` and Navbar toggle exist, but only `:root` (dark) CSS variables are defined. Toggling to light mode has no visual effect.

**Solution:** Add a `.light` class block in `index.css` with light theme color values. The existing `ThemeProvider` already applies `document.documentElement.classList.add('light')`.

**Files:**
- `frontend/src/index.css` — add `.light { ... }` block with appropriate color tokens

---

## QW-9: Keyboard Shortcuts Modal

**Problem:** A few shortcuts exist (Ctrl+K, Ctrl+H, Ctrl+B) but there's no discoverable help for them.

**Solution:** Create `ShortcutsModal.tsx` as a shadcn `Dialog`, add `?` key to Dashboard's `useKeyboardShortcuts`, and add a small `?` icon button to the Dashboard header.

**Files:**
- Create `frontend/src/components/ShortcutsModal.tsx`
- Modify `frontend/src/components/Dashboard.tsx` — add `?` shortcut + help button

---

## QW-5: More Technical Indicators

**Problem:** Only MA50, MA200, RSI are calculated. No MACD, Bollinger Bands, or ATR.

**Solution:**
- Backend: Add `calculate_macd()`, `calculate_bollinger_bands()`, `calculate_atr()` to `technical_indicators.py`. Extend `TechnicalReport` TypedDict with new optional fields. Include values in the technical agent.
- Frontend: Display MACD, Bollinger Band width, and ATR in `AgentPanel.tsx` technical metrics row. Optionally add Bollinger Band overlay lines to `StockChart.tsx`.

**Backend files:**
- `backend/shared/ai/tools/technical_indicators.py` — add 3 new calculations
- `backend/shared/ai/state/agent_state.py` — extend `TechnicalReport`
- `backend/shared/ai/agents/technical.py` — include new indicators in prompt

**Frontend files:**
- `frontend/src/components/AgentPanel.tsx` — show new metrics
- `frontend/src/components/StockChart.tsx` — Bollinger Band overlay (optional)
- `frontend/src/types/index.ts` — extend `TechnicalReport` type

---

## QW-3: Mobile Responsive

**Problem:** Agent grid works on desktop but stacks poorly on mobile.

**Solution:** Fix the 4-agent grid to be 1-col (mobile) → 2-col (tablet) → 4-col (desktop). Add collapsible behaviour to agent panels on small screens. Ensure the watchlist sidebar hides/overlays on mobile.

**Files:**
- `frontend/src/components/Dashboard.tsx` — fix grid breakpoints, sidebar overlay on mobile

---

## QW-7: Loading Polish (Frontend Only)

**Problem:** Loading state is generic shimmer placeholders.

**Solution:** Show agent-specific loading copy per agent (e.g. "Fetching fundamentals from Yahoo Finance...", "Scanning news & social signals...", "Computing RSI and moving averages..."). Uses the existing `isActive && !data` shimmer state in `AgentPanel.tsx`.

**Files:**
- `frontend/src/components/AgentPanel.tsx` — add descriptive loading text per agent type

---

## QW-6: International Markets

**Problem:** Only US and TASE markets are supported.

**Solution:** Add LSE (London), TSE (Tokyo), HKEX (Hong Kong), Xetra (Frankfurt) to the `Market` enum. Map each market to the correct Yahoo Finance ticker suffix. Update the market selector in `TickerInput` to show all markets.

**Backend files:**
- `backend/shared/ai/state/enums.py` — extend `Market` enum
- `backend/shared/ai/tools/market_data.py` — add suffix mapping per market
- `backend/shared/ai/tools/stock_search.py` — update search for new markets

**Frontend files:**
- `frontend/src/components/TickerInput.tsx` — expand market dropdown options
- `frontend/src/types/index.ts` — update `Market` type

---

## Implementation Order

1. QW-2 Light Mode (CSS only, 30 min)
2. QW-9 Keyboard Shortcuts Modal (frontend only, 1 hour)
3. QW-7 Loading Polish (frontend only, 30 min)
4. QW-3 Mobile Responsive (frontend only, 1–2 hours)
5. QW-5 More Technical Indicators (backend + frontend, 2–3 hours)
6. QW-6 International Markets (backend + frontend, 2–3 hours)
