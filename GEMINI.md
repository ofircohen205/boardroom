# GEMINI.md

This file provides guidance to Gemini when working with code in this repository.

## Project Overview

Boardroom is a multi-agent financial analysis system using LangGraph. Agents pass a "Token of Authority" between them to collaboratively analyze stocks and make trading decisions.

**Current Status:** Phase 0 (Core System) is complete. All 6 planned phases + quick wins remain to be implemented.

**Key Documentation:**
- [AGENTS.md](./AGENTS.md) — Detailed agent system architecture
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
- **Fundamental Agent** (`backend/agents/fundamental.py`): Pulls hard data via Yahoo Finance
- **Sentiment Agent** (`backend/agents/sentiment.py`): Scans news/social via Exa
- **Technical Agent** (`backend/agents/technical.py`): Analyzes price trends (MA, RSI)

**Risk Manager (Brake)** (`backend/agents/risk_manager.py`):
- Checks portfolio sector weight (max 30%)
- Has veto power over trades

**Chairperson (Closer)** (`backend/agents/chairperson.py`):
- Weighs all reports
- Makes final BUY/SELL/HOLD decision

See [AGENTS.md](./AGENTS.md) for detailed agent documentation.

### Key Directories

```
backend/
├── agents/          # All 5 agents + LLM abstraction
├── api/             # FastAPI routes + WebSocket
│   ├── routes.py    # REST endpoints
│   └── websocket.py # Real-time analysis streaming
├── auth/            # JWT authentication (Phase 1 - not yet implemented)
├── dao/             # SQLAlchemy models for audit trail
│   └── models.py    # Database models
├── graph/           # LangGraph workflow
│   └── workflow.py  # Agent orchestration logic
├── state/           # TypedDicts and enums
│   ├── agent_state.py  # State definitions
│   └── enums.py        # Action, Market, AgentType enums
├── tools/           # Market data, search, technical indicators
│   ├── market_data.py       # Yahoo Finance integration
│   ├── search.py            # Exa search for news/social
│   ├── stock_search.py      # Stock symbol autocomplete
│   └── technical_indicators.py  # MA, RSI calculations
├── cache.py         # Caching layer
├── config.py        # Settings and configuration
└── main.py          # FastAPI app entry point

frontend/
└── src/
    ├── components/      # React dashboard components
    │   ├── Dashboard.tsx      # Main dashboard
    │   ├── AgentPanel.tsx     # Individual agent display
    │   ├── DecisionCard.tsx   # Final decision display
    │   ├── StockChart.tsx     # Price chart (lightweight-charts)
    │   └── ui/                # shadcn/ui components
    ├── hooks/           # React hooks
    │   └── useWebSocket.ts    # WebSocket state management
    ├── pages/           # Route pages (Phase 1+ - not yet implemented)
    ├── contexts/        # React contexts (Phase 1+ - not yet implemented)
    ├── types/           # TypeScript types
    └── App.tsx          # Root component

tests/
├── test_agents.py          # Agent unit tests
├── test_tools.py           # Tool unit tests
├── test_workflow.py        # Integration tests
└── conftest.py             # Pytest fixtures

docs/
├── plans/                  # Phase implementation plans
│   ├── roadmap.md          # Overall roadmap
│   ├── phase-1-portfolio-watchlists.md
│   ├── phase-2-performance-tracking.md
│   └── ...
├── ARCHITECTURE.md         # Architecture overview
├── DEVELOPMENT.md          # Development guide
└── SECURITY.md             # Security considerations
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

## Best Practices

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
- Redis cache available at `boardroom-redis:6379` in Docker network
- Backend runs with hot reload via uvicorn --reload

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
- Run individual test to isolate: `pytest tests/test_file.py::test_name -v`

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

## Resources

- [FastAPI docs](https://fastapi.tiangolo.com/)
- [LangGraph docs](https://langchain-ai.github.io/langgraph/)
- [shadcn/ui components](https://ui.shadcn.com/)
- [TradingView lightweight-charts](https://tradingview.github.io/lightweight-charts/)
- [SQLAlchemy 2.0 docs](https://docs.sqlalchemy.org/en/20/)
