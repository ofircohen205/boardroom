# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Information

**Git Repository:** https://github.com/ofircohen205/boardroom

> **Important:** When making significant corrections to approaches, code patterns, or architectural decisions, update this file (CLAUDE.md) to prevent repeating the same mistakes in future sessions.

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

**Recent Changes:**

- **Backend services layer refactoring** (✅ COMPLETE - Feb 2026)
  - ✅ Phase 0: DAO layer standardization (singleton → direct instantiation)
  - ✅ Phase 1: BaseService + exception hierarchy (`backend/services/base.py`)
  - ✅ Phase 2: Missing service classes (WatchlistService, ScheduleService, AnalysisService)
  - ✅ Phase 3: Function-based → class-based services (AuthService, PortfolioService)
  - ✅ Phase 4: Dependency injection wiring in API endpoints (`backend/services/dependencies.py`)
  - ✅ Phase 6: Documentation (SERVICES.md, DEPENDENCY_INJECTION.md)
  - ⏭️ Phase 5: Testing (deferred)

**Key Documentation:**

- [AGENTS.md](./AGENTS.md) — Detailed agent system architecture
- [docs/SERVICES.md](./docs/SERVICES.md) — Services layer architecture and usage
- [docs/DEPENDENCY_INJECTION.md](./docs/DEPENDENCY_INJECTION.md) — Dependency injection patterns
- [docs/plans/roadmap.md](./docs/plans/roadmap.md) — Implementation phases and roadmap
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) — System architecture overview
- [docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md) — Development setup and workflow

## Quick Start

```bash
# Backend
make dev                                       # Start backend (requires PostgreSQL)
make test                                      # Run all tests
make test-cov                                  # Run tests with coverage

# Frontend
make frontend                                  # Start frontend dev server

# Database
make db-migrate                                # Run Alembic migrations
make db-revision MESSAGE="description"         # Create new migration

# Full System (Docker)
make dev                                       # Start all services via Docker Compose
make down                                      # Stop all services
```

## Development Commands

```bash
# Backend
uv run uvicorn backend.main:app --reload     # Run API server
uv run pytest tests/ -v                       # Run all tests
uv run pytest tests/test_specific.py -v       # Run specific test file
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
- All imports use `from backend.*` (e.g., `from backend.agents import FundamentalAgent`)

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

- **Fundamental Agent** (`backend/ai/agents/fundamental.py`): Pulls hard data via Yahoo Finance
- **Sentiment Agent** (`backend/ai/agents/sentiment.py`): Scans news/social via Exa
- **Technical Agent** (`backend/ai/agents/technical.py`): Analyzes price trends (MA, RSI)

**Risk Manager (Brake)** (`backend/ai/agents/risk_manager.py`):

- Checks portfolio sector weight (max 30%)
- Has veto power over trades

**Chairperson (Closer)** (`backend/ai/agents/chairperson.py`):

- Weighs all reports
- Makes final BUY/SELL/HOLD decision

See [AGENTS.md](./AGENTS.md) for detailed agent documentation.

### Key Directories

```
backend/
├── core/            # ✨ Application fundamentals
│   ├── settings.py  # Pydantic Settings (formerly config.py)
│   ├── enums.py     # LLMProvider, MarketDataProvider
│   ├── security.py  # JWT, password hashing
│   ├── logging.py   # Structured logging
│   └── exceptions.py # Base exceptions, error handlers
│
├── db/              # ✨ Database models layer
│   ├── database.py  # Engine, session maker, get_db()
│   └── models/      # SQLAlchemy models (modular)
│       ├── base.py       # DeclarativeBase
│       ├── user.py       # User, UserAPIKey
│       ├── portfolio.py  # Watchlist, Portfolio, Position
│       ├── analysis.py   # AnalysisSession, AgentReport, FinalDecision
│       ├── alerts.py     # Alert, AlertHistory
│       └── performance.py # AnalysisOutcome, AgentAccuracy
│
├── dao/             # ✨ Data Access Objects layer
│   ├── base.py      # Base DAO with CRUD operations
│   ├── user.py      # User data operations
│   ├── portfolio.py # Portfolio/Watchlist operations
│   ├── analysis.py  # Analysis session operations
│   ├── alerts.py    # Alert operations
│   └── performance.py # Performance tracking operations
│
├── ai/              # ✨ AI/LLM analysis system
│   ├── workflow.py  # LangGraph orchestration
│   ├── agents/      # All 5 agents + LLM abstraction
│   │   ├── base.py
│   │   ├── fundamental.py
│   │   ├── sentiment.py
│   │   ├── technical.py
│   │   ├── risk_manager.py
│   │   └── chairperson.py
│   ├── state/       # TypedDicts and enums
│   │   ├── agent_state.py  # State definitions
│   │   └── enums.py        # Action, Market, AgentType enums
│   └── tools/       # Market data, search, indicators
│       ├── market_data.py       # Yahoo Finance integration
│       ├── search.py            # Exa search for news/social
│       ├── stock_search.py      # Stock symbol autocomplete
│       ├── technical_indicators.py  # MA, RSI calculations
│       ├── relative_strength.py     # Comparative metrics
│       └── sector_data.py           # Sector information
│
├── api/             # ✨ FastAPI routes (feature-based organization)
│   ├── __init__.py
│   ├── routes.py         # Main router aggregation
│   ├── auth/             # Authentication endpoints
│   ├── analysis/         # Stock analysis endpoints
│   ├── websocket/        # WebSocket connections
│   ├── portfolios/       # Portfolio management
│   ├── watchlists/       # Watchlist endpoints
│   ├── alerts/           # Alert management
│   ├── schedules/        # Scheduled analysis
│   ├── performance/      # Performance tracking
│   ├── settings/         # User settings
│   ├── sectors/          # Sector information
│   └── notifications/    # Notification endpoints
│
├── services/        # ✨ Business logic layer
│   ├── __init__.py
│   ├── auth/                    # Authentication services
│   ├── analysis_history/        # Analysis history services
│   ├── performance_tracking/    # Performance tracking
│   ├── portfolio_management/    # Portfolio operations
│   ├── alerts/                  # Alert services
│   ├── settings/                # Settings management
│   └── email.py                 # Email notifications
│
├── auth/            # Authentication dependencies
│   └── dependencies.py  # get_current_user, etc.
│
├── jobs/            # Background jobs (APScheduler)
│   ├── scheduler.py
│   └── outcome_tracker.py
│
└── main.py          # FastAPI app entry point

frontend/
└── src/
    ├── components/      # React components
    │   ├── layout/          # AppLayout, Navbar, Footer, PageContainer
    │   ├── Dashboard.tsx    # Main analysis dashboard
    │   ├── AgentPanel.tsx   # Individual agent display
    │   ├── DecisionCard.tsx # Final decision display
    │   ├── StockChart.tsx   # Price chart (lightweight-charts)
    │   └── ui/              # shadcn/ui components
    ├── pages/           # Route pages
    │   ├── DashboardPage.tsx
    │   ├── PortfolioPage.tsx
    │   ├── AlertsPage.tsx
    │   ├── SchedulesPage.tsx
    │   ├── PerformancePage.tsx
    │   ├── ComparePage.tsx
    │   └── SettingsPage.tsx
    ├── hooks/           # React hooks
    │   └── useWebSocket.ts    # WebSocket state management
    ├── contexts/        # React contexts
    │   └── AuthContext.tsx
    ├── types/           # TypeScript types
    ├── lib/             # Utilities
    └── App.tsx          # Root component with routing

tests/
├── conftest.py          # Pytest fixtures
├── unit/                # Unit tests (SQLite in-memory)
│   ├── test_agents.py
│   ├── test_tools.py
│   ├── test_dao.py
│   └── ...
└── integration/         # Integration tests (PostgreSQL)
    ├── test_workflow.py
    ├── test_api.py
    └── ...

docs/
├── plans/                  # Phase implementation plans
│   ├── roadmap.md
│   ├── phase-1-portfolio-watchlists.md
│   └── ...
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
     - [CLAUDE.md](./CLAUDE.md) - Claude-specific guidance and corrections
     - [GEMINI.md](./GEMINI.md) - Gemini-specific guidance
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
   - **Warning:** It's easy to get "carried away" with Claude Code and make dozens of changes without committing
   - If "everything breaks," small commits make it much easier to identify and revert the problematic change
   - **IMPORTANT:** Do NOT add `Co-Authored-By:` footers or author information to commits—all commits are by the user

2. **Protected Branches:**
   - NEVER commit directly to `main` branch
   - All work should be done in feature branches
   - Use pull requests for code review before merging

3. **Code Review:**
   - All code changes are subject to automated code review (via hooks)
   - Code review runs twice:
     - After completing major code changes
     - Before every Git commit (blocks commits that fail review)
   - Address code review feedback before committing

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
   - Instructions in CLAUDE.md, GEMINI.md, and AGENTS.md are authoritative
   - **However:** Sometimes these instructions may be ignored unintentionally
   - If you notice yourself deviating from documented patterns, flag it and ask
   - When in doubt, ask the user rather than making assumptions

4. **Data Integrity:**
   - Always validate data before processing
   - Handle missing data explicitly (don't silently drop rows)
   - Log data quality issues (missing fields, unexpected formats)
   - Use type hints and runtime validation (Pydantic) for all data structures

## Best Practices

### Import Patterns (Updated Architecture)

After the layered architecture refactoring, use these import patterns:

```python
# Core utilities
from backend.core.settings import settings
from backend.core.security import create_access_token, get_password_hash
from backend.core.enums import LLMProvider, MarketDataProvider

# Database
from backend.db.models import User, AnalysisSession, Portfolio
from backend.db.database import get_db, init_db

# AI system (preferred - uses module exports)
from backend.ai import (
    create_boardroom_graph,
    Market,
    Action,
    AgentType,
    FundamentalAgent,
    get_llm_client,
)

# AI system (alternative - direct imports)
from backend.ai.workflow import create_boardroom_graph
from backend.ai.state.enums import Market, Action, AgentType
from backend.ai.agents.fundamental import FundamentalAgent
from backend.ai.tools.market_data import get_market_data_client
```

**Deprecated imports** (for reference, do not use in new code):

- ❌ `from backend.config import settings` → ✅ `from backend.core.settings import settings`
- ❌ `from backend.auth.jwt import create_access_token` → ✅ `from backend.core.security import create_access_token`
- ❌ `from backend.dao.models import User` → ✅ `from backend.db.models import User`
- ❌ `from backend.agents.fundamental import FundamentalAgent` → ✅ `from backend.ai.agents.fundamental import FundamentalAgent`
- ❌ `from backend.state.enums import Market` → ✅ `from backend.ai.state.enums import Market`
- ❌ `from backend.tools.market_data import get_market_data_client` → ✅ `from backend.ai.tools.market_data import get_market_data_client`

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

- Tools are in `backend/tools/` and are synchronous or async functions
- Tools should handle errors gracefully and return sensible defaults
- Cache expensive operations (market data, LLM calls)
- Test tools with mocked external APIs

### Services Layer (Phase 4 Refactoring)

**Architecture:** Services encapsulate business logic between API endpoints and DAOs.

**Service Injection Pattern:**

```python
# In backend/services/dependencies.py - define factory functions
async def get_portfolio_service(db: AsyncSession) -> PortfolioService:
    return PortfolioService(PortfolioDAO(db))

# In API endpoint - inject the service
@router.post("/portfolios")
async def create_portfolio(
    data: PortfolioCreate,
    service: PortfolioService = Depends(get_portfolio_service),
    db: AsyncSession = Depends(get_db),
):
    portfolio = await service.create_portfolio(current_user.id, data.name, db)
    return PortfolioSchema.from_orm(portfolio)
```

**Best Practices:**

- Each service has a corresponding factory function in `backend/services/dependencies.py`
- Services receive DAOs through constructor (constructor injection)
- Services don't manage their own database sessions - callers pass `db` parameter
- All service methods are async
- Services raise domain-specific exceptions (inherit from `ServiceError`)
- Endpoints handle service exceptions and map to HTTP status codes

**Exception Handling:**

```python
try:
    schedule = await service.create_scheduled_analysis(...)
except ScheduleRateLimitError as e:
    raise HTTPException(status_code=400, detail=str(e))
except ScheduleError as e:
    logger.error(f"Failed: {e}")
    raise HTTPException(status_code=500, detail="Operation failed")
```

**Available Services:**

- `AuthService` - User registration, login, authentication
- `PortfolioService` - Portfolio CRUD and position management
- `WatchlistService` - Watchlist CRUD and item management
- `ScheduleService` - Scheduled analysis management
- `AnalysisService` - Analysis session and decision tracking
- `AlertService` - Price alert management
- `PerformanceService` - Performance tracking and outcomes
- `SettingsService` - User profile and settings

See [docs/SERVICES.md](./docs/SERVICES.md) and [docs/DEPENDENCY_INJECTION.md](./docs/DEPENDENCY_INJECTION.md) for detailed documentation.

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

1. Create agent class in `backend/agents/new_agent.py`
2. Define report TypedDict in `backend/state/agent_state.py`
3. Add agent to `BoardroomGraph` in `backend/graph/workflow.py`
4. Update `AgentState` to include new report
5. Wire into workflow (parallel or sequential)
6. Add WebSocket message type to `backend/state/enums.py`
7. Update frontend to display new agent results
8. Write tests in `tests/test_agents.py`

See [AGENTS.md](./AGENTS.md) for detailed instructions.

### Adding a New Tool

1. Create function in appropriate `backend/tools/*.py` file
2. Add type hints and docstring
3. Handle errors and edge cases
4. Add caching if expensive
5. Write tests in `tests/test_tools.py`
6. Use in agent by calling the tool function

### Adding a New Endpoint

1. Add route to `backend/api/routes.py`
2. Use FastAPI dependency injection for auth (Phase 1+)
3. Return Pydantic models for type safety
4. Add OpenAPI documentation via docstrings
5. Write tests in `tests/test_api.py` (or create new test file)

### Updating the Frontend

1. Run frontend dev server: `cd frontend && npm run dev`
2. Use shadcn CLI to add components: `npx shadcn@latest add <component>`
3. Update types in `frontend/src/types/` to match backend
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
- `JWT_SECRET` — Secret for JWT tokens (Phase 1+)

See `.env.example` for full list.

## Implementation Phases

**✅ Phase 0: Core System (Complete)**

- 5-agent analysis pipeline
- Real-time WebSocket streaming
- Stock search + charts + news
- PostgreSQL audit trail
- Multi-LLM support

**🚧 Next Up:**

1. **Phase 1:** Portfolio & Watchlists (user auth, saved tickers, positions)
2. **Phase 2:** Performance Tracking (track accuracy of recommendations)
3. **Phase 3:** Comparative Analysis (compare multiple stocks)
4. **Phase 4:** Alerts & Notifications (price alerts, scheduled analysis)
5. **Phase 5:** Backtesting & Simulation (paper trading, strategy builder)
6. **Phase 6:** Export & Reporting (PDF reports, API keys, webhooks)
7. **Quick Wins:** Small improvements (dark mode, keyboard shortcuts, etc.)

See [docs/plans/roadmap.md](./docs/plans/roadmap.md) for details.

## Testing

```bash
# Run all tests
make test

# Run specific test file
uv run pytest tests/test_agents.py -v

# Run with coverage
make test-cov

# Run single test
uv run pytest tests/test_agents.py::test_fundamental_agent -v
```

**Testing Philosophy:**

- **All Python execution uses `uv`** (not bare `pytest` or `python`)
- Unit test each agent independently with mocked tools
- Integration test the full workflow
- Mock external APIs (Yahoo Finance, Exa, LLM providers)
- Use fixtures for common test data
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

- Ensure test database is separate from dev: use `TEST_DATABASE_URL`
- Check that mocks are set up correctly
- Run individual test to isolate: `uv run pytest tests/test_file.py::test_name -v`

### WebSocket connection issues

- Check CORS settings in `backend/main.py`
- Verify WebSocket URL in `frontend/src/hooks/useWebSocket.ts`
- Check browser console for errors

## Contributing

When working on new features:

1. Create a new branch from `main`
2. Implement feature following best practices above
3. Write tests (aim for >80% coverage)
4. Update documentation if needed
5. Run tests and linting: `make test && cd frontend && npm run lint`
6. Commit with conventional commit messages
7. Create PR with description of changes

## Key Documentation Files

- [CLAUDE.md](./CLAUDE.md) - This file (Claude-specific guidance)
- [GEMINI.md](./GEMINI.md) - Gemini-specific guidance
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

**Last Updated:** 2026-02-10
**Version:** 2.0.0
