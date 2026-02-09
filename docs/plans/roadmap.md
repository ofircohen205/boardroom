# Boardroom Improvement Roadmap

Complete development roadmap with 6 phases and quick wins.

## Implementation Status

| Phase | Name | Status | Priority | Depends On |
|-------|------|--------|----------|------------|
| 0 | Core System | ✅ Complete | — | — |
| [1](./phase-1-portfolio-watchlists.md) | Portfolio & Watchlists | 🚧 70% | High | — |
| [2](./phase-2-performance-tracking.md) | Performance Tracking | ✅ 100% | High | Phase 1 |
| [3](./phase-3-comparative-analysis.md) | Comparative Analysis | ✅ 90% | Medium | — |
| [4](./phase-4-alerts-notifications.md) | Alerts & Notifications | ⏳ 0% | Medium | Phase 1 |
| [5](./phase-5-backtesting-simulation.md) | Backtesting & Simulation | ⏳ 0% | Low | Phase 2 |
| [6](./phase-6-export-reporting.md) | Export & Reporting | ⏳ 0% | Low | — |
| [QW](./phase-quick-wins.md) | Quick Wins | 🚧 In Progress | Ongoing | — |

## Recommended Order

```
Phase 1 (finish) ──► Phase 2 ──► Phase 5
                 │
                 └──► Phase 4

Phase 3 (finish) (independent)
Phase 6 (independent, start anytime)
Quick Wins (parallel to everything)
```

## Current State Summary

**Phase 0: Core System (✅ Complete)**
- 5-agent analysis pipeline (fundamental, sentiment, technical, risk, chairperson)
- Real-time WebSocket streaming dashboard
- Stock search with autocomplete
- Price chart (lightweight-charts)
- News feed with sentiment indicators
- PostgreSQL audit trail (sessions, agent reports, decisions)
- Multi-LLM provider support (Anthropic, OpenAI, Gemini)
- Caching system
- Docker development environment
- Test suite covering all agents, tools, and workflow

**Phase 1: Portfolio & Watchlists (🚧 70% - Implemented, needs frontend wiring)**

Completed:
- ✅ User authentication backend (JWT token creation/validation, password hashing)
- ✅ User model with relationships to watchlists, portfolios, analysis history
- ✅ Watchlist & WatchlistItem database models
- ✅ Portfolio & Position database models
- ✅ User API key storage for multi-provider LLM support
- ✅ Analysis history user context (user_id FK on AnalysisSession)
- ✅ Frontend components: WatchlistSidebar, AnalysisHistory, PresetSelector

Remaining:
- ⏳ REST API endpoints wiring (auth routes, watchlist CRUD, portfolio CRUD)
- ⏳ Auth middleware integration for protected routes
- ⏳ Frontend auth pages (login/register)
- ⏳ Frontend portfolio management page
- ⏳ WebSocket authentication on connect
- ⏳ Portfolio weight integration into risk assessment
- ⏳ Database migrations for user-related tables

**Phase 2: Performance Tracking (✅ 100% - Complete)**

Completed:
- ✅ AnalysisOutcome database model for tracking recommendations
- ✅ AgentAccuracy database model for per-agent metrics
- ✅ Background job scheduler (APScheduler) in `backend/jobs/`
- ✅ Outcome tracker job to fetch follow-up prices
- ✅ Full performance analytics API (`backend/api/performance.py`)
- ✅ Database migration for AnalysisOutcome and AgentAccuracy tables
- ✅ Outcome service with performance calculation logic
- ✅ Frontend performance dashboard page
- ✅ Frontend performance components (charts, leaderboards, metrics)
- ✅ Integration with DecisionCard to show track record
- ✅ Integration with analysis history to show outcome badges

Remaining:
- None.

**Phase 3: Comparative Analysis (✅ 90% - Implemented, mostly complete)**

Completed:
- ✅ Comparative analysis API endpoint (`backend/api/comparison.py`):
  - `POST /api/compare/stocks` — multi-stock side-by-side analysis
  - `POST /api/compare/sector` — sector analysis endpoint
  - `GET /api/compare/sectors` — list available sectors
- ✅ Sector mapping tool (`backend/tools/sector_data.py`)
- ✅ Relative strength tools (`backend/tools/relative_strength.py`)
- ✅ Workflow integration (`backend/graph/workflow.py::run_comparison_streaming`)
- ✅ Frontend components:
  - ComparisonTable — tabular comparison of metrics
  - RelativePerformanceChart — multi-line chart overlay
  - ComparisonInput, RankingCard, SectorOverview (partial)
  - PresetSelector component

Remaining:
- ⏳ Complete frontend comparison page wiring
- ⏳ WebSocket streaming for comparison results
- ⏳ Dashboard "Compare" button integration
- ⏳ Watchlist "Compare all" functionality
- ⏳ Frontend state management for comparison data