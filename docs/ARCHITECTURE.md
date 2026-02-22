# System Architecture

This document describes the architecture of the **Boardroom** system, an AI-powered autonomous investment analyst platform.

## Table of Contents

1. [High-Level Overview](#high-level-overview)
2. [Backend Architecture](#backend-architecture)
3. [Frontend Architecture](#frontend-architecture)
4. [Data Architecture](#data-architecture)
5. [AI Agent Pipeline](#ai-agent-pipeline)

## High-Level Overview

Boardroom is a full-stack application composed of:

- **Frontend**: A React single-page application (SPA) for the dashboard and user interface.
- **Backend**: A FastAPI server handling API requests, authentication, and WebSocket connections.
- **AI Core**: A LangGraph-based multi-agent system for financial analysis.
- **Database**: PostgreSQL for persistent storage of user data, portfolios, and analysis history.

## Backend Architecture

### Project Structure

The backend follows the **project-root/package-name/** pattern:

- Project root: `boardroom/`
- Package name: `backend/` (importable as `from backend.*`)

This is a standard Python project layout, equivalent to the alternative `src/` layout.

### Directory Structure

The backend uses **domain-driven design**: cross-cutting infrastructure lives in `shared/`, while feature logic lives in `domains/` (vertical slices).

```
backend/
├── shared/                  # Cross-domain infrastructure (imported by all domains)
│   ├── core/                # App fundamentals (settings, enums, security, logging, exceptions)
│   ├── db/                  # Database layer (engine, session management, models)
│   ├── dao/                 # Data Access Objects (CRUD wrappers)
│   ├── ai/                  # LangGraph agent system (workflow, agents, state, tools, prompts)
│   ├── auth/                # Auth dependency injection (get_current_user)
│   ├── services/            # BaseService & exceptions
│   ├── jobs/                # APScheduler background jobs
│   ├── data/                # Historical data utilities
│   └── utils/               # Misc shared utilities
│
├── domains/                 # Feature domains (vertical slices)
│   ├── analysis/            # Stock analysis & backtesting
│   ├── auth/                # Authentication domain
│   ├── notifications/       # Alerts & scheduled analysis
│   ├── performance/         # Performance tracking & leaderboards
│   ├── portfolio/           # Portfolio & watchlist management
│   ├── sectors/             # Sector info endpoints
│   └── settings/            # User settings
│   # Inside each domain:
│   # ├── api/               # REST/WebSocket endpoints & schemas
│   # └── services/          # Business logic services
│
├── api.py                   # Main router (aggregates all domain routers)
├── dependencies.py          # Shared FastAPI dependencies
└── main.py                  # FastAPI app entry point
```

### Layer Responsibilities & Patterns

#### 1. **API Endpoints (`api/`)**

- **Purpose**: HTTP/WebSocket entry points, request validation, and response formatting.
- **Responsibilities**:
  - FastAPI route definitions and Pydantic schema validation.
  - WebSocket connection management (`analysis/api/websocket.py`).
  - Uses FastAPI's `Depends()` system to inject dependencies (Services and Database Sessions). Endpoints **do not** contain business logic.

#### 2. **Service Layer (`services/`) & Dependency Injection**

- **Purpose**: Encapsulates all business logic, orchestrating DAOs and external calls.
- **Responsibilities**:
  - Services are created via Factory functions (e.g., `get_portfolio_service` in `backend.dependencies`) and injected into endpoints using `Depends()`.
  - **Dependency Injection (DI)**: Services accept Data Access Objects (DAOs) via constructor injection. They _do not_ create DAOs themselves.
  - **Transaction Control**: Services accept a fresh `AsyncSession` (provided per request) so that operations can be grouped in a single transaction. The endpoints dictate session lifecycle.
  - They inherit from `BaseService` and raise domain-specific exceptions (inheriting from `ServiceError`).

#### 3. **Database Access Layer (`shared/db/` and `shared/dao/`)**

- **Purpose**: Database connection, ORM models, and CRUD wrappers.
- **Responsibilities**:
  - SQLAlchemy 2.0 async ORM models definition.
  - `get_db()` provides a fresh database session for each request, keeping requests isolated.
  - DAOs isolate database queries. They are passed directly into the Service layer.

#### 4. **AI Agent & Workflow Layer (`shared/ai/`)**

- **Purpose**: Multi-agent financial analysis using LangGraph.
- **Responsibilities**:
  - `agents`: Specialized financial analysis (fundamental, sentiment, technical, risk, chairperson). Multi-LLM support via `base.py`.
  - `workflow`: LangGraph orchestration of parallel agent execution and state passing.
  - `tools`: External data integration (Yahoo Finance, Exa search, indicators).
  - `state`: Shared `AgentState` TypedDict definitions flowing through the pipeline.

#### 5. **Jobs Layer (`shared/jobs/`)**

- **Purpose**: Background task processing.
- **Responsibilities**:
  - Scheduled periodic jobs via APScheduler.
  - Ongoing background analysis and alert checking.

### Data Flow

1. **User Request** → Frontend sends ticker via WebSocket or REST API
2. **API Layer** → `websocket.py` or `routes.py` handles request
3. **Workflow Layer** → `workflow.py` orchestrates agent execution:
   - **Parallel**: Fundamental, Sentiment, Technical agents run concurrently
   - **Sequential**: Risk Manager validates results
   - **Final**: Chairperson synthesizes decision
4. **Agent Layer** → Each agent:
   - Fetches data via `tools/`
   - Calls LLM via `agents/base.py`
   - Returns structured report
5. **State Management** → `AgentState` flows through workflow, accumulating reports
6. **Database Layer** → Results saved to PostgreSQL via `dao/models.py`
7. **Response** → WebSocket streams agent completions in real-time OR REST returns final result

### Technology Stack

- **Framework**: FastAPI (async Python web framework)
- **Workflow**: LangGraph (agent orchestration)
- **Database**: PostgreSQL with SQLAlchemy 2.0 (async ORM)
- **Authentication**: JWT tokens with bcrypt password hashing
- **LLM Providers**: Anthropic Claude, OpenAI GPT-4, Google Gemini (configurable)
- **External APIs**: Yahoo Finance (market data), Exa (search/news)
- **Background Jobs**: APScheduler (periodic outcome tracking)
- **Caching**: In-memory cache with TTL (optional Redis support planned)

### API Versioning

**Current State**: No versioning (flat structure).
**Future**: May introduce `/api/v1/`, `/api/v2/` as needed for breaking changes.

---

## Frontend Architecture

The frontend is a **React** application built with **Vite**.

### Directory Structure (`frontend/src/`)

```
frontend/src/
├── components/      # React UI components
│   ├── Dashboard.tsx           # Main analysis dashboard
│   ├── AgentPanel.tsx          # Individual agent report display
│   ├── DecisionCard.tsx        # Final decision display
│   ├── StockChart.tsx          # TradingView lightweight-charts integration
│   ├── TickerInput.tsx         # Stock symbol input with autocomplete
│   ├── WatchlistSidebar.tsx    # User watchlist management (Phase 1)
│   ├── AnalysisHistory.tsx     # Past analysis sessions (Phase 1)
│   ├── ComparisonTable.tsx     # Multi-stock comparison (Phase 3)
│   ├── RelativePerformanceChart.tsx  # Comparison charts (Phase 3)
│   ├── performance/            # Performance dashboard components (Phase 2)
│   └── ui/                     # shadcn/ui base components (Button, Card, etc.)
│
├── contexts/        # React Context providers
│   └── AuthContext.tsx         # User authentication state (Phase 1)
│
├── hooks/           # Custom React hooks
│   └── useWebSocket.ts         # WebSocket connection management
│
├── pages/           # Route page components
│   ├── AuthPage.tsx            # Login/Registration (Phase 1)
│   ├── PortfolioPage.tsx       # Portfolio management (Phase 1)
│   ├── ComparisonPage.tsx      # Multi-stock comparison (Phase 3)
│   └── PerformancePage.tsx     # Agent accuracy dashboard (Phase 2)
│
├── types/           # TypeScript type definitions
│   ├── index.ts                # Core types (AgentReport, Decision, etc.)
│   ├── comparison.ts           # Comparison-specific types (Phase 3)
│   └── performance.ts          # Performance metrics types (Phase 2)
│
└── App.tsx          # Root component with routing (Phase 0: no routing yet)
```

### Key Components

- **`Dashboard.tsx`**: Main orchestrator component
  - Manages WebSocket connection via `useWebSocket` hook
  - Displays agent panels as they complete
  - Shows final decision card
  - Renders stock price chart

- **`AgentPanel.tsx`**: Displays individual agent report
  - Shows agent name, status (pending/loading/complete)
  - Renders agent-specific summary and key metrics
  - Color-coded by action (BUY/SELL/HOLD)

- **`StockChart.tsx`**: Interactive price chart
  - Uses TradingView `lightweight-charts` library
  - Displays historical price data
  - Supports overlays (MA lines, indicators)

- **`useWebSocket.ts`**: Custom hook for real-time updates
  - Manages WebSocket connection lifecycle
  - Handles incoming agent messages (`MessageType` enum)
  - Updates state as agents complete
  - Error handling and reconnection logic

### Technology Stack

- **Framework**: React 19
- **Language**: TypeScript (strict mode)
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS v4
- **Component Library**: shadcn/ui (headless UI components)
- **Charts**: TradingView lightweight-charts
- **Routing**: React Router DOM v6 (Phase 1+)
- **Icons**: Lucide React
- **HTTP Client**: Native `fetch` API

### State Management

- **Local State**: React `useState`, `useReducer`
- **WebSocket State**: Custom `useWebSocket` hook
- **Auth State**: `AuthContext` provider (Phase 1)
- **No Redux/Zustand**: Simple context + hooks sufficient for current complexity

---

## Data Architecture

The system uses **PostgreSQL** with **SQLAlchemy 2.0** (async ORM).

### Database Models

All models defined in `backend/dao/models.py`:

#### 1. **User**

- **Purpose**: User identity and authentication
- **Fields**: `id`, `email`, `hashed_password`, `created_at`, `updated_at`
- **Relationships**: Has many `Watchlist`, `Portfolio`, `AnalysisSession`

#### 2. **Watchlist**

- **Purpose**: User's saved stock tickers for monitoring
- **Fields**: `id`, `user_id`, `name`, `created_at`
- **Relationships**: Belongs to `User`, has many `WatchlistItem`

#### 3. **WatchlistItem**

- **Purpose**: Individual ticker in a watchlist
- **Fields**: `id`, `watchlist_id`, `ticker`, `added_at`
- **Relationships**: Belongs to `Watchlist`

#### 4. **Portfolio**

- **Purpose**: User's investment portfolio
- **Fields**: `id`, `user_id`, `name`, `created_at`
- **Relationships**: Belongs to `User`, has many `Position`

#### 5. **Position**

- **Purpose**: Stock position within a portfolio
- **Fields**: `id`, `portfolio_id`, `ticker`, `shares`, `entry_price`, `entry_date`
- **Relationships**: Belongs to `Portfolio`

#### 6. **AnalysisSession**

- **Purpose**: Record of an AI analysis run
- **Fields**: `id`, `user_id`, `ticker`, `market`, `created_at`, `llm_provider`, `final_action`
- **Relationships**: Belongs to `User`, has many `AgentReport`, has one `FinalDecision`

#### 7. **AgentReport**

- **Purpose**: Individual agent's analysis output
- **Fields**: `id`, `session_id`, `agent_type`, `report_data` (JSONB), `created_at`
- **Relationships**: Belongs to `AnalysisSession`

#### 8. **FinalDecision**

- **Purpose**: Chairperson's final BUY/SELL/HOLD decision
- **Fields**: `id`, `session_id`, `action`, `reasoning`, `confidence`, `created_at`
- **Relationships**: Belongs to `AnalysisSession`

#### 9. **AnalysisOutcome** (Phase 2 - Performance Tracking)

- **Purpose**: Track actual price movement after recommendations
- **Fields**: `id`, `session_id`, `ticker`, `action`, `price_at_analysis`, `price_after_1d`, `price_after_7d`, `price_after_30d`, `tracked_at`
- **Relationships**: Belongs to `AnalysisSession`

#### 10. **AgentAccuracy** (Phase 2 - Performance Tracking)

- **Purpose**: Aggregate accuracy metrics per agent
- **Fields**: `id`, `agent_type`, `time_period`, `accuracy`, `total_predictions`, `correct_predictions`, `updated_at`

### Database Migrations

- **Tool**: Alembic
- **Location**: `alembic/versions/`
- **Commands**:
  - `make db-migrate` - Run all pending migrations
  - `make db-revision MESSAGE="description"` - Create new migration

---

## AI Agent Pipeline

The core intelligence is powered by **LangGraph** with a multi-agent workflow.

### Workflow Architecture

```
┌─────────────────────────────────────────────────────┐
│                   WebSocket Request                  │
│                  (ticker: "AAPL")                    │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│              LangGraph Workflow Start                │
│              (AgentState initialized)                │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│          PARALLEL EXECUTION (3 agents)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │ Fundamental  │  │  Sentiment   │  │Technical │  │
│  │    Agent     │  │    Agent     │  │  Agent   │  │
│  └──────┬───────┘  └──────┬───────┘  └────┬─────┘  │
│         │ report           │ report         │ report │
└─────────┼──────────────────┼────────────────┼────────┘
          │                  │                │
          └──────────────────┴────────────────┘
                             │
                             ▼
                  ┌────────────────────┐
                  │   Risk Manager     │
                  │   Agent (veto?)    │
                  └─────────┬──────────┘
                            │ assessment
                            ▼
                  ┌────────────────────┐
                  │   Chairperson      │
                  │   Agent (final)    │
                  └─────────┬──────────┘
                            │ decision
                            ▼
                  ┌────────────────────┐
                  │  Save to Database  │
                  │  Stream to Client  │
                  └────────────────────┘
```

### Agent Responsibilities

#### 1. **Fundamental Agent** (`backend/shared/ai/agents/fundamental.py`)

- **Data Sources**: Yahoo Finance (via `backend/shared/ai/tools/market_data.py`)
- **Analysis**:
  - Financial metrics (P/E, EPS, revenue growth, margins)
  - Company fundamentals (market cap, sector, description)
  - Valuation assessment
- **Output**: `FundamentalReport` with summary and key metrics

#### 2. **Sentiment Agent** (`backend/shared/ai/agents/sentiment.py`)

- **Data Sources**: Exa search (via `backend/shared/ai/tools/search.py`)
- **Analysis**:
  - News sentiment (recent headlines, articles)
  - Social media mentions
  - Overall sentiment score (bullish/bearish)
- **Output**: `SentimentReport` with summary and sentiment indicators

#### 3. **Technical Agent** (`backend/shared/ai/agents/technical.py`)

- **Data Sources**: Historical price data (via `backend/shared/ai/tools/market_data.py`)
- **Analysis**:
  - Moving averages (50-day, 200-day)
  - RSI (Relative Strength Index)
  - Trend detection (bullish/bearish/neutral)
  - Support/resistance levels
- **Output**: `TechnicalReport` with summary and indicators

#### 4. **Risk Manager Agent** (`backend/shared/ai/agents/risk_manager.py`)

- **Data Sources**: Portfolio data (via `backend/shared/db/models/`), historical prices
- **Analysis**:
  - Portfolio sector concentration (max 30% per sector)
  - Value at Risk (VaR) calculations
  - Volatility assessment
  - **Veto Power**: Can override BUY recommendation if risk too high
- **Output**: `RiskAssessment` with veto decision and reasoning

#### 5. **Chairperson Agent** (`backend/shared/ai/agents/chairperson.py`)

- **Data Sources**: All previous agent reports
- **Analysis**:
  - Weighs fundamental, sentiment, technical reports
  - Considers risk assessment
  - Synthesizes conflicting signals
  - Makes final decision with confidence score
- **Output**: `Decision` with BUY/SELL/HOLD action and reasoning

### LLM Abstraction

The `backend/shared/ai/agents/base.py` module provides a unified interface for multiple LLM providers:

```python
from backend.shared.ai.agents import get_llm_client

llm = get_llm_client()  # Returns AnthropicClient, OpenAIClient, or GeminiClient
response = llm.generate(system_prompt, user_prompt)
```

**Supported Providers**:

- **Anthropic Claude** (default): `claude-3-5-sonnet-20241022`
- **OpenAI GPT-4**: `gpt-4-turbo-preview`
- **Google Gemini**: `gemini-pro`

Provider selection via `LLM_PROVIDER` environment variable.

### State Management

The `AgentState` TypedDict (defined in `backend/shared/ai/state/agent_state.py`) flows through the entire workflow:

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

Each agent adds its report to the state, which is then available to downstream agents.

---

## Future Architecture Considerations

### Planned Enhancements

1. **API Versioning** (Phase 4+):
   - Introduce `/api/v1/` structure for breaking changes
   - Maintain backward compatibility

2. **Service Layer Expansion** (Phase 1-3):
   - Extract business logic from API routes
   - Create services for auth, portfolio, watchlist, comparison

3. **Core Utilities Module** (Optional):
   - Consolidate `config.py`, `cache.py` into `backend/shared/core/`
   - Add logging, metrics, exception handling utilities

4. **Redis Caching** (Phase 4+):
   - Replace in-memory cache with Redis for distributed caching
   - Session storage for JWT refresh tokens

5. **Middleware Layer** (Phase 4+):
   - Rate limiting
   - Request logging
   - Security headers

---

## Development Workflow

### Adding a New Agent

1. Create `backend/shared/ai/agents/new_agent.py`
2. Define report TypedDict in `backend/shared/ai/state/agent_state.py`
3. Add agent to workflow in `backend/shared/ai/workflow.py`
4. Update `AgentState` to include new report field
5. Wire into frontend in `frontend/src/components/AgentPanel.tsx`
6. Write tests in `tests/unit/analysis/test_agents.py`

### Adding a New API Endpoint

1. Add route to `backend/domains/<domain>/api/endpoints.py` (or create new module)
2. Use Pydantic models for request/response validation
3. Add auth dependency for protected routes: `user: User = Depends(get_current_user)`
4. Write tests in `tests/test_api.py`

### Running the System

```bash
# Backend
make dev              # Start FastAPI server (localhost:8000)
make test             # Run all tests
make test-cov         # Tests with coverage report

# Frontend
make frontend         # Start Vite dev server (localhost:5173)

# Full Stack
make up               # Docker Compose (all services)
make down             # Stop all services
```

---

## Summary

The Boardroom backend follows a **pragmatic layered architecture** that prioritizes:

- **Simplicity**: Flat structure where possible, nested only when needed
- **Testability**: Clear separation of concerns, dependency injection
- **Scalability**: Async everywhere, parallel agent execution
- **Maintainability**: Standard Python patterns, clear module boundaries

The current structure is **production-ready for Phase 0** and designed to evolve incrementally as new phases add features.
