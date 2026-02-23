# GEMINI.md

This file provides guidance to Gemini when working with code in this repository.

## Repository Information

**Git Repository:** https://github.com/ofircohen205/boardroom

> **Important:** When making significant corrections to approaches, code patterns, or architectural decisions, update this file (GEMINI.md) to prevent repeating the same mistakes in future sessions.

## Project Overview

Boardroom is a multi-agent financial analysis system using LangGraph. Agents pass a "Token of Authority" between them to collaboratively analyze stocks and make trading decisions.

**Current Status:**

- ✅ Phase 0 (Core System) complete - 5-agent pipeline, WebSocket streaming
- ✅ Phase 1 (Auth/Watchlist) complete - User authentication, portfolio management
- ✅ Phase 2 (Performance) complete - Accuracy tracking, agent leaderboards
- ✅ Phase 3 (Comparison) complete - Multi-stock side-by-side analysis
- ✅ Phase 4a (Alerts) complete - Price alerts, WebSocket notifications
- ✅ Phase 4b (Scheduled Analysis) complete - Automated analysis, TASE support
- ✅ Phase 5 (Backtesting) complete - Historical testing, paper trading, strategy builder
- ✅ Services Layer Refactoring complete - Class-based services with dependency injection
- ⏳ Phase 6 (Export & Reporting) - Not yet started

**Key Documentation:**

- [AGENTS.md](./AGENTS.md) — Detailed agent system architecture
- [docs/plans/roadmap.md](./docs/plans/roadmap.md) — Implementation phases and roadmap
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) — System architecture overview
- [docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md) — Development setup and workflow

## Quick Start

```bash
# Full system (Docker Compose — backend + frontend + DB)
make dev                                       # Start all services
make down                                      # Stop all services

# Backend only (requires PostgreSQL already running)
uv run uvicorn backend.main:app --reload

# Frontend only
make frontend                                  # or: cd frontend && npm run dev

# Database
make db-migrate                                # Run Alembic migrations
make db-revision MESSAGE="description"         # Create new migration

# Tests
make test                                      # Run all tests
make test-cov                                  # Run tests with coverage report
```

## Development Commands

```bash
# Backend
uv run uvicorn backend.main:app --reload     # Run API server
uv run pytest tests/ -v                       # Run all tests
uv run pytest tests/unit/analysis/ -v         # Run specific domain tests
uv run pytest tests/test_file.py::test_name   # Run single test

# Frontend
cd frontend && npm run dev                    # Development server
cd frontend && npm run build                  # Production build
cd frontend && npm run lint                   # Run ESLint

# Dependencies
uv sync                                       # Install Python dependencies
uv add <package>                              # Add Python package
cd frontend && npm install                    # Install JS dependencies
```

## Architecture

### Project Structure

The project follows the **project-root/package-name/** Python layout pattern:

- `boardroom/` (project root) contains `backend/` (importable as `backend`)
- This is a standard Python structure, equivalent to the alternative `src/` layout
- All imports use `from backend.*` (e.g., `from backend.shared.ai.agents import FundamentalAgent`)

### Technology Stack

**Backend:**

- FastAPI + WebSocket for real-time communication
- LangGraph for agent orchestration
- PostgreSQL for audit trail and data persistence
- SQLAlchemy 2.0 with async support
- Multi-LLM support: Anthropic Claude, OpenAI GPT-4, Google Gemini
- Redis for caching (optional)

**Frontend:**

- React 19 + TypeScript
- Tailwind CSS v4 + shadcn/ui components
- TradingView lightweight-charts
- Vite for build tooling

### Agent Hierarchy

**Analyst Agents (Workers):**

- **Fundamental Agent** (`backend/shared/ai/agents/fundamental.py`): Pulls hard data via Yahoo Finance
- **Sentiment Agent** (`backend/shared/ai/agents/sentiment.py`): Scans news/social via Exa
- **Technical Agent** (`backend/shared/ai/agents/technical.py`): Analyzes price trends (MA, RSI)

**Risk Manager (Brake)** (`backend/shared/ai/agents/risk_manager.py`):

- Checks portfolio sector weight (max 30%)
- Has veto power over trades

**Chairperson (Closer)** (`backend/shared/ai/agents/chairperson.py`):

- Weighs all reports
- Makes final BUY/SELL/HOLD decision

See [AGENTS.md](./AGENTS.md) for detailed agent documentation.

### Key Directories

The backend uses **domain-driven design**: cross-cutting infrastructure lives in `shared/`, feature logic lives in `domains/`.

```
backend/
├── shared/                  # Cross-domain infrastructure (imported by all domains)
│   ├── core/                # App fundamentals
│   │   ├── settings.py      # Pydantic Settings (env vars)
│   │   ├── enums.py         # LLMProvider, MarketDataProvider
│   │   ├── security.py      # JWT, password hashing
│   │   ├── logging.py       # Structured logging
│   │   ├── cache.py         # Redis caching helpers
│   │   └── exceptions.py    # Base exceptions, error handlers
│   ├── db/                  # Database layer
│   │   ├── database.py      # Engine, session maker, get_db()
│   │   └── models/          # SQLAlchemy models
│   │       ├── user.py          # User, UserAPIKey
│   │       ├── portfolio.py     # Watchlist, Portfolio, Position
│   │       ├── analysis.py      # AnalysisSession, AgentReport, FinalDecision
│   │       ├── alerts.py        # Alert, AlertHistory
│   │       ├── performance.py   # AnalysisOutcome, AgentAccuracy
│   │       └── backtesting.py   # BacktestRun, BacktestTrade
│   ├── dao/                 # Data Access Objects (CRUD wrappers)
│   │   ├── base.py          # Base DAO with shared CRUD helpers
│   │   ├── user.py
│   │   ├── portfolio.py
│   │   ├── analysis.py
│   │   ├── alerts.py
│   │   ├── performance.py
│   │   └── backtesting.py
│   ├── ai/                  # LangGraph agent system
│   │   ├── workflow.py      # LangGraph orchestration (create_boardroom_graph)
│   │   ├── agents/          # All 5 agents
│   │   │   ├── base.py
│   │   │   ├── fundamental.py
│   │   │   ├── sentiment.py
│   │   │   ├── technical.py
│   │   │   ├── risk_manager.py
│   │   │   └── chairperson.py
│   │   ├── state/           # Shared state definitions
│   │   │   ├── agent_state.py   # AgentState TypedDict
│   │   │   ├── enums.py         # Action, Market, AgentType
│   │   │   └── result_state.py  # Result state definitions
│   │   ├── tools/           # Market data & analysis tools
│   │   │   ├── market_data.py
│   │   │   ├── search.py
│   │   │   ├── stock_search.py
│   │   │   ├── technical_indicators.py
│   │   │   ├── relative_strength.py
│   │   │   └── sector_data.py
│   │   └── prompts/         # LLM prompt templates
│   ├── auth/                # Auth dependency injection
│   │   └── dependencies.py  # get_current_user, etc.
│   ├── services/            # Base service class & exceptions
│   │   ├── base.py          # BaseService
│   │   └── exceptions.py    # ServiceError base class
│   ├── jobs/                # APScheduler background jobs
│   │   ├── scheduler.py
│   │   ├── outcome_tracker.py
│   │   ├── alert_checker.py
│   │   └── scheduled_analyzer.py
│   ├── data/                # Historical data utilities
│   │   └── historical.py
│   └── utils/               # Misc shared utilities
│       └── routes.py
│
├── domains/                 # Feature domains (vertical slices)
│   ├── analysis/            # Stock analysis & backtesting
│   │   ├── api/
│   │   │   ├── endpoints.py     # REST + WebSocket analysis endpoints
│   │   │   ├── websocket.py     # WebSocket connection handler
│   │   │   ├── schemas.py
│   │   │   ├── backtest/        # Backtesting API (router, schemas, websocket)
│   │   │   ├── paper/           # Paper trading API
│   │   │   └── strategies/      # Strategy management API
│   │   ├── services/
│   │   │   ├── service.py       # AnalysisService
│   │   │   └── exceptions.py
│   │   └── scoring/             # Agent output scoring
│   │       ├── fundamental_scorer.py
│   │       ├── sentiment_scorer.py
│   │       ├── technical_scorer.py
│   │       └── chairperson_scorer.py
│   ├── auth/                # Authentication domain
│   │   ├── api/             # Login, register, token endpoints
│   │   └── services/        # AuthService
│   ├── notifications/       # Alerts & scheduled analysis
│   │   ├── api/             # alerts.py, schedules.py, endpoints.py
│   │   └── services/        # AlertService, ScheduleService, EmailService
│   ├── performance/         # Performance tracking & leaderboards
│   │   ├── api/
│   │   └── services/        # PerformanceService
│   ├── portfolio/           # Portfolio & watchlist management
│   │   ├── api/             # portfolios.py, watchlists.py
│   │   └── services/        # PortfolioService, WatchlistService
│   ├── sectors/             # Sector info endpoints
│   ├── settings/            # User settings
│   │   ├── api/
│   │   └── services/        # SettingsService
│   └── ...
│
├── api.py                   # Main router (aggregates all domain routers)
├── dependencies.py          # Shared FastAPI dependencies
└── main.py                  # FastAPI app entry point

frontend/src/
├── components/
│   ├── layout/              # AppLayout, Navbar, Footer, PageContainer
│   ├── backtest/            # BacktestForm, BacktestSummary, TradeLog
│   ├── common/              # AsyncDataDisplay, EmptyState, ErrorState, LoadingState
│   ├── performance/         # AccuracyChart, AgentLeaderboard, PerformanceSummary
│   ├── strategies/          # AgentWeightSliders, StrategyForm
│   ├── ui/                  # shadcn/ui components
│   └── (root)               # Dashboard, AgentPanel, DecisionCard, StockChart, etc.
├── pages/                   # AuthPage, PortfolioPage, AlertsPage, SchedulesPage,
│                            # BacktestPage, PaperTradingPage, StrategiesPage, etc.
├── hooks/                   # useWebSocket, useAPIClient, useFetch, useTheme, etc.
├── contexts/                # AuthContext, APIContext, ThemeContext
├── lib/
│   ├── api/                 # Per-feature API clients (alerts, analysis, portfolios, etc.)
│   ├── apiClient.ts         # Axios/fetch base client
│   └── utils.ts
└── App.tsx

tests/
├── conftest.py              # Pytest fixtures (DB setup, factories)
├── unit/                    # SQLite in-memory — fast, no external deps
│   ├── analysis/            # Agents, tools, scoring, DAO, services
│   ├── auth/                # Auth DAO, dependencies
│   ├── notifications/       # Alert/schedule services, email, market hours
│   ├── performance/         # DAO, service, API
│   ├── portfolio/           # DAO, watchlist service
│   ├── sectors/             # API
│   ├── settings/            # Service
│   └── shared/              # Cache, DAOs, exceptions, scheduler, workflow
└── integration/             # PostgreSQL — full stack tests
    ├── analysis/            # Full workflow, backtest flow
    ├── notifications/       # Alert checker, scheduled analysis
    └── shared/              # API, DB connection, health, scheduler

docs/
├── plans/                   # Phase implementation plans + roadmap
├── ARCHITECTURE.md
├── DEVELOPMENT.md

└── SECURITY.md
```

### Data Flow

1. User enters ticker in React dashboard
2. WebSocket sends request to FastAPI (`/ws/analyze`)
3. LangGraph workflow runs agents in sequence:
   - **Parallel execution:** Fundamental, Sentiment, Technical agents run concurrently
   - **Sequential execution:** Risk Manager analyzes results
   - **Final decision:** Chairperson weighs all reports
4. Each agent completion streams back via WebSocket as it finishes
5. Dashboard updates in real-time with agent results
6. All decisions logged to PostgreSQL for audit trail

### State Management

The system uses a shared `AgentState` TypedDict that flows through the workflow:

```python
AgentState = {
    "ticker": str,
    "market": Market,
    "fundamental_report": FundamentalReport | None,
    "sentiment_report": SentimentReport | None,
    "technical_report": TechnicalReport | None,
    "risk_assessment": RiskAssessment | None,
    "final_decision": Decision | None,
    "consensus_score": float,
    "audit_id": str,
}
```

## Workflow Orchestration

> These principles govern how to approach tasks, leverage AI capabilities effectively, and maintain quality throughout execution.

### 1. Plan Before You Build

- Enter plan mode for **any non-trivial task** — 3+ steps, architectural decisions, or anything touching multiple files
- Write detailed specs upfront to surface edge cases and reduce ambiguity before a single line of code is written
- If execution goes sideways, **STOP and re-plan** — don't keep pushing through a broken approach
- Use plan mode for verification steps too, not just initial design

### 2. Subagent Strategy

- Use subagents liberally to keep the main context window clean and focused
- Offload research, codebase exploration, and parallel analysis to subagents
- For complex problems: throw more compute via subagents rather than brute-forcing in a single context thread
- One focused task per subagent — don't overload a single subagent with unrelated concerns

### 3. Self-Improvement Loop

- After **any** correction from the user: update `tasks/lessons.md` with the pattern
- Write specific, actionable rules that prevent the same mistake from recurring
- Ruthlessly iterate on these lessons until mistake rate drops
- Review `tasks/lessons.md` at session start before beginning any work on this project

### 4. Verification Before Done

- **Never mark a task complete without proving it works** — run tests, check logs, demonstrate correctness
- When relevant, diff behavior between `main` and your changes to catch regressions
- Ask yourself: "Would a staff engineer approve this?" before presenting work
- See the [Git Workflow → Code Review](#git-workflow) section for automated review hooks

### 5. Demand Elegance (Balanced)

- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: step back — "Knowing everything I know now, what's the clean solution?"
- **Skip this for obvious, simple fixes** — don't over-engineer one-liners
- Challenge your own first draft before presenting it to the user

### 6. Autonomous Bug Fixing

- When given a bug report: **just fix it** — don't ask for hand-holding
- Point at logs, errors, and failing tests to identify the root cause, then resolve it
- Zero unnecessary context-switching required from the user
- Fix failing CI/tests proactively without waiting to be told how

## Task Management

When working on any multi-step task, follow this workflow:

1. **Plan First:** Write the plan to `tasks/todo.md` with checkable items (`- [ ] step`)
2. **Verify Plan:** Check in with the user before starting implementation
3. **Track Progress:** Mark items complete (`- [x]`) as you go; keep the file current
4. **Explain Changes:** Provide a high-level summary at each significant step — no silent changes
5. **Document Results:** Add a review/outcome section to `tasks/todo.md` when done
6. **Capture Lessons:** Update `tasks/lessons.md` after any corrections, surprises, or new insights

> The `tasks/` directory is gitignored and is for session-local planning only. Never commit it.

### Core Principles

These apply to every change, no matter how small:

- **Simplicity First:** Make every change as simple as possible. Impact the minimal amount of code necessary.
- **No Laziness:** Find root causes. No temporary fixes. Hold yourself to senior developer standards.
- **Minimal Impact:** Changes should only touch what's necessary. Avoid accidentally introducing bugs in adjacent code.

## Code Quality Standards

### General Coding Principles

1. **Keep Code Clean:**
   - Write clear, maintainable code following established patterns
   - Remove "orphaned" code when making changes (unused imports, dead functions, commented-out blocks)
   - Extract reused code into separate functions or files (DRY principle)
   - If the same code appears 2+ times, refactor it into a shared function

2. **Temporary Files:**
   - All temporary test files, debugging scripts, and experimental code MUST go in the `tmp/` directory
   - The `tmp/` directory is gitignored and should never be committed
   - Clean up temporary files after they're no longer needed

3. **Documentation:**
   - Update relevant documentation files when making architectural changes:
     - [GEMINI.md](./GEMINI.md) - Gemini-specific guidance and corrections
     - [CLAUDE.md](./CLAUDE.md) - Claude-specific guidance
     - [AGENTS.md](./AGENTS.md) - Agent system architecture
     - [STATUS.md](./STATUS.md) - Project status, completed features, pending bugs
   - Add docstrings to all new functions and classes
   - Update inline comments for complex logic

4. **Logging:**
   - Every significant operation MUST include detailed logging
   - Logs should be stored (not just printed to console)
   - Use structured logging with appropriate levels (DEBUG, INFO, WARNING, ERROR)
   - Include context in logs: ticker, agent name, operation, timing
   - Good logs make debugging 10x easier - invest in them upfront

### Git Workflow

1. **Commit Discipline:**
   - Make frequent, small commits rather than large, monolithic ones
   - Each commit should represent a logical unit of work
   - Use conventional commit messages: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
   - **Warning:** It's easy to get carried away and make dozens of changes without committing
   - If "everything breaks," small commits make it much easier to identify and revert the problematic change

2. **Protected Branches:**
   - NEVER commit directly to `main` branch
   - All work should be done in feature branches
   - Use pull requests for code review before merging

3. **Plan Execution Branches:**
   - **ALWAYS create a new git worktree + branch before executing any implementation plan**
   - Branch naming: `feature/<plan-topic>` (e.g., `feature/test-coverage-80pct`)
   - Worktrees live in `.worktrees/<branch-name>/` (already gitignored)
   - Create with: `git worktree add .worktrees/<branch> -b feature/<branch>`
   - Never execute plan tasks directly on `main` or the current working branch

4. **Code Review:**
   - All code changes are subject to automated code review (via hooks)
   - Code review runs twice:
     - After completing major code changes
     - Before every Git commit (blocks commits that fail review)
   - Address code review feedback before committing

### AI/Data Project Specific Guidelines

> **Critical for Data Analysis, Model Training, and Simulations:**

This project involves financial data analysis, agent decision-making, and LLM interactions. Extra caution is required:

1. **Beware of Silent Optimizations:**
   - **NEVER** make assumptions to simplify runtime without explicit permission
   - **Example:** If asked to analyze entire dataset, do NOT analyze only every 10th row to save time
   - Always process the full dataset unless explicitly told otherwise
   - If an operation would be expensive, ASK the user before optimizing

2. **Numerical Accuracy:**
   - Be extremely careful with numerical comparisons and thresholds
   - Double-check logic for "greater than," "less than," "good," "bad" interpretations
   - Example: Is a P/E ratio of 50 good or bad? Don't assume - use proper analysis
   - Verify calculations match expected formulas (e.g., RSI, moving averages)

3. **Follow Instructions Precisely:**
   - Instructions in GEMINI.md, CLAUDE.md, and AGENTS.md are authoritative
   - **However:** Sometimes these instructions may be ignored unintentionally
   - If you notice yourself deviating from documented patterns, flag it and ask
   - When in doubt, ask the user rather than making assumptions

4. **Data Integrity:**
   - Always validate data before processing
   - Handle missing data explicitly (don't silently drop rows)
   - Log data quality issues (missing fields, unexpected formats)
   - Use type hints and runtime validation (Pydantic) for all data structures

## Best Practices

### Import Patterns

The backend uses a `shared/` + `domains/` split. All shared infrastructure is under `backend.shared.*`; domain services/APIs are under `backend.domains.<domain>.*`.

```python
# Shared infrastructure
from backend.shared.core.settings import settings
from backend.shared.core.security import create_access_token, get_password_hash
from backend.shared.core.enums import LLMProvider, MarketDataProvider
from backend.shared.core.exceptions import ServiceError

# Database
from backend.shared.db.models import User, AnalysisSession, Portfolio
from backend.shared.db.database import get_db

# DAOs
from backend.shared.dao.user import UserDAO
from backend.shared.dao.portfolio import PortfolioDAO

# AI system
from backend.shared.ai.workflow import create_boardroom_graph
from backend.shared.ai.state.enums import Market, Action, AgentType
from backend.shared.ai.state.agent_state import AgentState
from backend.shared.ai.agents.fundamental import FundamentalAgent
from backend.shared.ai.tools.market_data import get_market_data_client

# Domain services
from backend.domains.analysis.services.service import AnalysisService
from backend.domains.auth.services.service import AuthService
from backend.domains.portfolio.services.portfolio_service import PortfolioService
from backend.domains.notifications.services.alert_service import AlertService
from backend.domains.notifications.services.schedule_service import ScheduleService

# Auth dependency
from backend.shared.auth.dependencies import get_current_user
```

**Do NOT use these old paths** (pre-refactor, no longer exist):

- ❌ `from backend.core.*` → ✅ `from backend.shared.core.*`
- ❌ `from backend.db.*` → ✅ `from backend.shared.db.*`
- ❌ `from backend.dao.*` → ✅ `from backend.shared.dao.*`
- ❌ `from backend.ai.*` → ✅ `from backend.shared.ai.*`
- ❌ `from backend.services.*` → ✅ `from backend.domains.<domain>.services.*`
- ❌ `from backend.auth.dependencies` → ✅ `from backend.shared.auth.dependencies`
- ❌ `from backend.api.*` → ✅ `from backend.domains.<domain>.api.*`

### Code Style

- **Backend:** Follow PEP 8, use type hints, async/await for I/O
- **Frontend:** Use TypeScript strict mode, functional components, custom hooks
- **Testing:** Aim for >80% coverage, mock external APIs
- **Commits:** Use conventional commits (feat:, fix:, docs:, etc.)

### Working with Agents

- Each agent is independent and can be tested in isolation
- Agents receive data via parameters, not shared state mutation
- All agent methods are async
- Use the LLM abstraction layer (`get_llm_client()`) for multi-provider support
- See [AGENTS.md](./AGENTS.md) for how to add new agents

### Working with Tools

- Tools are in `backend/shared/ai/tools/` and are synchronous or async functions
- Tools should handle errors gracefully and return sensible defaults
- Cache expensive operations (market data, LLM calls)
- Test tools with mocked external APIs

### Services Layer

**Architecture:** Each domain owns its own service(s) under `backend/domains/<domain>/services/`. The base class and shared exceptions live in `backend/shared/services/`.

**Service pattern:**

```python
# Domain service (e.g., backend/domains/portfolio/services/portfolio_service.py)
class PortfolioService(BaseService):
    def __init__(self, dao: PortfolioDAO):
        self.dao = dao

    async def create_portfolio(self, user_id: int, name: str, db: AsyncSession) -> Portfolio:
        ...

# API endpoint — construct service inline or via Depends
@router.post("/portfolios")
async def create_portfolio(
    data: PortfolioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PortfolioService(PortfolioDAO(db))
    return await service.create_portfolio(current_user.id, data.name, db)
```

**Key conventions:**

- Services live in `backend/domains/<domain>/services/service.py` (or named descriptively)
- Services receive DAOs via constructor injection; they do **not** manage their own sessions
- All service methods are async
- Services raise domain-specific exceptions that inherit from `ServiceError` (`backend/shared/services/exceptions.py`)
- Endpoints catch service exceptions and map them to HTTP status codes

**Exception handling pattern:**

```python
try:
    result = await service.create_scheduled_analysis(...)
except ScheduleRateLimitError as e:
    raise HTTPException(status_code=400, detail=str(e))
except ScheduleError as e:
    logger.error(f"Failed: {e}")
    raise HTTPException(status_code=500, detail="Operation failed")
```

**Available services** (one per domain):

| Domain        | Service                                           | Location                                  |
| ------------- | ------------------------------------------------- | ----------------------------------------- |
| auth          | `AuthService`                                     | `domains/auth/services/service.py`        |
| portfolio     | `PortfolioService`, `WatchlistService`            | `domains/portfolio/services/`             |
| notifications | `AlertService`, `ScheduleService`, `EmailService` | `domains/notifications/services/`         |
| performance   | `PerformanceService`                              | `domains/performance/services/service.py` |
| settings      | `SettingsService`                                 | `domains/settings/services/service.py`    |
| analysis      | `AnalysisService`                                 | `domains/analysis/services/service.py`    |

See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) for details about the architecture, services, and dependency injection patterns.

### Database Migrations

- Always create migrations for schema changes: `make db-revision MESSAGE="add users table"`
- Test migrations up and down before committing
- Never modify existing migrations once merged to main

### Frontend Components

- Use shadcn/ui components for consistency
- Keep components small and focused (< 200 lines)
- Use the `@/` alias for imports (maps to `src/`)
- Charts use lightweight-charts library (TradingView)

### Docker Development

- **Docker files structure:**
  - Compose files: `docker/docker-compose.{dev,prod}.yml`
  - Backend Dockerfiles: `backend/docker/Dockerfile.{dev,prod}`
  - Frontend Dockerfiles: `frontend/docker/Dockerfile.{dev,prod}`
- Frontend uses anonymous volume for node_modules
- After adding npm deps: `docker compose -f docker/docker-compose.dev.yml up -d --build boardroom-frontend`
- Backend runs with hot reload via uvicorn --reload
- Redis cache available at `boardroom-redis:6379` in Docker network

## Common Tasks

### Adding a New Agent

1. Create agent class in `backend/shared/ai/agents/new_agent.py`
2. Define report TypedDict in `backend/shared/ai/state/agent_state.py`
3. Update `AgentState` to include the new report field
4. Add agent to `BoardroomGraph` in `backend/shared/ai/workflow.py`
5. Wire into workflow (parallel or sequential)
6. Add WebSocket message type to `backend/shared/ai/state/enums.py`
7. Update frontend to display new agent results
8. Write tests in `tests/unit/analysis/test_<agent_name>.py`

See [AGENTS.md](./AGENTS.md) for detailed instructions.

### Adding a New Tool

1. Create function in `backend/shared/ai/tools/<name>.py`
2. Add type hints and docstring
3. Handle errors and edge cases gracefully
4. Add caching if the operation is expensive
5. Write tests in `tests/unit/analysis/test_tools.py`
6. Use in an agent by importing and calling the tool function

### Adding a New Endpoint

1. Add router to the relevant `backend/domains/<domain>/api/` module
2. Register it in `backend/api.py` (the main router aggregator)
3. Use `Depends(get_current_user)` for authenticated endpoints
4. Return Pydantic schemas for type safety
5. Add OpenAPI documentation via docstrings
6. Write tests in `tests/unit/<domain>/test_api.py`

### Updating the Frontend

1. Run frontend dev server: `cd frontend && npm run dev`
2. Use shadcn CLI to add components: `npx shadcn@latest add <component>`
3. Update types in `frontend/src/lib/api/types.ts` to match backend
4. Use `useWebSocket` hook for real-time data
5. Test in browser at http://localhost:5173

## Environment Variables

Required:

- `DATABASE_URL` — PostgreSQL connection string
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` or `GOOGLE_API_KEY` — LLM provider API key
- `EXA_API_KEY` — Exa search API key

Optional:

- `LLM_PROVIDER` — anthropic | openai | gemini (default: anthropic)
- `REDIS_URL` — Redis connection string for caching
- `JWT_SECRET` — Secret for JWT tokens

See `.env.example` for full list.

## Implementation Phases

- ✅ **Phase 0:** Core System — 5-agent pipeline, WebSocket streaming, stock search, charts, PostgreSQL audit trail
- ✅ **Phase 1:** Auth & Watchlists — User authentication, portfolio management
- ✅ **Phase 2:** Performance Tracking — Accuracy tracking, agent leaderboards
- ✅ **Phase 3:** Comparative Analysis — Multi-stock side-by-side analysis
- ✅ **Phase 4a:** Alerts — Price alerts, WebSocket notifications
- ✅ **Phase 4b:** Scheduled Analysis — Automated analysis, TASE support
- ✅ **Phase 5:** Backtesting & Paper Trading — Historical testing, paper trading, strategy builder
- ⏳ **Phase 6:** Export & Reporting — PDF reports, API keys, webhooks _(not started)_

See [docs/plans/roadmap.md](./docs/plans/roadmap.md) for details.

## Testing

```bash
# Run all tests
make test

# Unit tests only (fast, SQLite in-memory)
uv run pytest tests/unit/ -v

# Integration tests only (requires PostgreSQL on port 5433)
uv run pytest tests/integration/ -v

# Specific domain
uv run pytest tests/unit/analysis/ -v
uv run pytest tests/unit/notifications/ -v

# Single test
uv run pytest tests/unit/analysis/test_fundamental_agent.py::test_name -v

# With coverage
make test-cov
```

**Test structure mirrors domain structure:**

- `tests/unit/<domain>/` — fast, isolated, SQLite in-memory
- `tests/integration/<domain>/` — full stack, PostgreSQL (port 5433 to avoid dev DB conflicts)

**Philosophy:**

- **Always use `uv run pytest`**, never bare `pytest` or `python -m pytest`
- Unit test each agent/service independently with mocked external calls
- Integration tests cover end-to-end flows (workflow → DB → API)
- Mock external APIs (Yahoo Finance, Exa, LLM providers) in unit tests
- Aim for >80% coverage

## Troubleshooting

### Backend won't start

- Check PostgreSQL is running: `psql $DATABASE_URL`
- Verify API keys are set in `.env`
- Run migrations: `make db-migrate`

### Frontend build errors

- Delete `node_modules` and reinstall: `rm -rf frontend/node_modules && cd frontend && npm install`
- If using Docker, rebuild: `docker compose -f docker/docker-compose.dev.yml up -d --build --force-recreate boardroom-frontend`

### Tests failing

- Ensure test database is separate from dev: use `TEST_DATABASE_URL` (port 5433)
- Check that mocks are set up correctly
- Run individual test to isolate: `uv run pytest tests/unit/<domain>/test_file.py::test_name -v`

### WebSocket connection issues

- Check CORS settings in `backend/main.py`
- Verify WebSocket URL in `frontend/src/hooks/useWebSocket.ts`
- Check browser console for errors

## Contributing

When working on new features:

1. Create a feature branch from `main` (never commit to `main` directly)
2. Implement feature following best practices above
3. Write tests (aim for >80% coverage)
4. Update documentation if needed
5. Run tests and linting: `make test && cd frontend && npm run lint`
6. Commit with conventional commit messages
7. Create PR with description of changes

## Key Documentation Files

- [GEMINI.md](./GEMINI.md) - This file (Gemini-specific guidance)
- [CLAUDE.md](./CLAUDE.md) - Claude-specific guidance
- [AGENTS.md](./AGENTS.md) - Detailed agent system architecture
- [STATUS.md](./STATUS.md) - **Critical:** Project status, directory structure, completed work, pending bugs
  - Updated after almost every code change
  - Essential for understanding project state
  - Required for starting new sessions or transferring code to others
- [docs/plans/roadmap.md](./docs/plans/roadmap.md) - Implementation phases and roadmap
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) - System architecture overview
- [docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md) - Development setup and workflow

## External Resources

- [FastAPI docs](https://fastapi.tiangolo.com/)
- [LangGraph docs](https://langchain-ai.github.io/langgraph/)
- [shadcn/ui components](https://ui.shadcn.com/)
- [TradingView lightweight-charts](https://tradingview.github.io/lightweight-charts/)
- [SQLAlchemy 2.0 docs](https://docs.sqlalchemy.org/en/20/)

---

**Last Updated:** 2026-02-22
**Version:** 3.0.0
