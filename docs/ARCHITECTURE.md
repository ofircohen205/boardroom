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

```
backend/
├── agents/          # AI agent implementations
│   ├── base.py             # BaseLLMClient and LLM provider abstraction
│   ├── fundamental.py      # FundamentalAgent - financial metrics analysis
│   ├── sentiment.py        # SentimentAgent - news/social sentiment
│   ├── technical.py        # TechnicalAgent - price action and indicators
│   ├── risk_manager.py     # RiskManagerAgent - portfolio risk assessment
│   └── chairperson.py      # ChairpersonAgent - final decision synthesis
│
├── api/             # FastAPI routes and endpoints (flat structure)
│   ├── routes.py           # Main REST endpoints (auth, watchlists, portfolios)
│   ├── websocket.py        # WebSocket handler for real-time analysis streaming
│   ├── comparison.py       # Multi-stock comparison endpoints
│   └── performance.py      # Performance tracking and accuracy metrics
│
├── auth/            # Authentication and authorization
│   ├── jwt.py              # JWT token creation and verification
│   └── dependencies.py     # FastAPI auth dependencies (get_current_user)
│
├── dao/             # Database access layer
│   ├── models.py           # SQLAlchemy ORM models (User, Portfolio, AnalysisSession, etc.)
│   └── database.py         # Database connection and session management
│
├── graph/           # LangGraph workflow orchestration
│   └── workflow.py         # Multi-agent workflow definition
│
├── jobs/            # Background job processing
│   ├── scheduler.py        # APScheduler configuration for periodic jobs
│   └── outcome_tracker.py  # Track recommendation outcomes and accuracy
│
├── services/        # Business logic layer
│   └── outcome_service.py  # Outcome tracking business logic
│
├── state/           # State management for agents
│   ├── agent_state.py      # TypedDict definitions for agent state
│   └── enums.py            # Enums (Action, Market, AgentType, etc.)
│
├── tools/           # External data integration tools
│   ├── market_data.py          # Yahoo Finance integration
│   ├── search.py               # Exa search for news/social data
│   ├── stock_search.py         # Stock symbol autocomplete
│   ├── technical_indicators.py # MA, RSI, trend calculations
│   ├── sector_data.py          # Sector-based stock data
│   └── relative_strength.py    # Relative strength calculations
│
├── cache.py         # In-memory caching layer with TTL support
├── config.py        # Pydantic Settings for environment configuration
└── main.py          # FastAPI application entry point
```

### Layer Responsibilities

#### 1. **API Layer** (`backend/api/`)
- **Purpose**: HTTP/WebSocket endpoints, request/response handling
- **Responsibilities**:
  - FastAPI route definitions
  - Request validation (Pydantic models)
  - Response serialization
  - WebSocket connection management
  - Error handling and HTTP status codes
- **Current Structure**: Flat (no versioning). All endpoints in root-level route files.
- **Key Files**:
  - `routes.py`: User auth, watchlists, portfolios (REST endpoints)
  - `websocket.py`: Real-time analysis streaming
  - `comparison.py`: Multi-stock comparison API
  - `performance.py`: Agent accuracy and performance metrics

#### 2. **Authentication Layer** (`backend/auth/`)
- **Purpose**: User authentication and authorization
- **Responsibilities**:
  - JWT token generation and verification
  - Password hashing with bcrypt
  - User session management
  - FastAPI dependency injection for protected routes
- **Key Files**:
  - `jwt.py`: Token creation/validation utilities
  - `dependencies.py`: `get_current_user` dependency for route protection

#### 3. **Database Access Layer** (`backend/dao/`)
- **Purpose**: Database operations and ORM models
- **Responsibilities**:
  - SQLAlchemy ORM model definitions
  - Database connection pooling
  - Session management
  - Query execution
- **Key Files**:
  - `models.py`: All database models (User, Watchlist, Portfolio, AnalysisSession, etc.)
  - `database.py`: Async database engine and session factory

#### 4. **Service Layer** (`backend/services/`)
- **Purpose**: Business logic separate from API/database concerns
- **Responsibilities**:
  - Complex business operations
  - Orchestration of multiple data sources
  - Integration with external services
- **Current State**: Minimal (only `outcome_service.py`)
- **Future**: Will expand as business logic grows

#### 5. **Agent Layer** (`backend/agents/`)
- **Purpose**: AI-powered financial analysis agents
- **Responsibilities**:
  - Multi-LLM support (Claude, GPT-4, Gemini) via `base.py`
  - Specialized financial analysis (fundamental, technical, sentiment)
  - Risk assessment and portfolio constraints
  - Final decision synthesis
- **Key Files**:
  - `base.py`: LLM client abstraction (`get_llm_client()`)
  - `fundamental.py`: Financial metrics and company data analysis
  - `sentiment.py`: News and social media sentiment analysis
  - `technical.py`: Price action, MA, RSI, trend analysis
  - `risk_manager.py`: Portfolio risk checks, VaR calculations
  - `chairperson.py`: Aggregates all reports into final BUY/SELL/HOLD decision

#### 6. **Workflow Layer** (`backend/graph/`)
- **Purpose**: LangGraph orchestration of multi-agent pipeline
- **Responsibilities**:
  - Agent execution order (parallel + sequential)
  - State passing between agents
  - Workflow compilation and streaming
- **Key Files**:
  - `workflow.py`: Defines the `BoardroomGraph` with parallel analyst execution

#### 7. **Jobs Layer** (`backend/jobs/`)
- **Purpose**: Background task processing
- **Responsibilities**:
  - Scheduled periodic jobs (APScheduler)
  - Outcome tracking for recommendations
  - Agent accuracy calculations
- **Key Files**:
  - `scheduler.py`: APScheduler setup, job registration
  - `outcome_tracker.py`: Tracks BUY/SELL outcomes, calculates accuracy

#### 8. **Tools Layer** (`backend/tools/`)
- **Purpose**: External data integration utilities
- **Responsibilities**:
  - Market data fetching (Yahoo Finance)
  - News/social search (Exa)
  - Technical indicator calculations
  - Stock symbol search
- **Key Files**:
  - `market_data.py`: Historical prices, fundamentals
  - `search.py`: Exa search wrapper
  - `technical_indicators.py`: Pure functions for MA, RSI, trend
  - `stock_search.py`: Symbol autocomplete

#### 9. **State Management** (`backend/state/`)
- **Purpose**: Shared state definitions for agent pipeline
- **Responsibilities**:
  - TypedDict definitions for agent state
  - Enum definitions for actions, markets, agent types
- **Key Files**:
  - `agent_state.py`: `AgentState`, `FundamentalReport`, `SentimentReport`, etc.
  - `enums.py`: `Action`, `Market`, `AgentType`, `MessageType` enums

#### 10. **Core Utilities** (root-level files)
- **`config.py`**: Pydantic Settings for environment-based configuration (LLM keys, DB URL, JWT secret)
- **`cache.py`**: In-memory cache with TTL, stats, and `@cached` decorator
- **`main.py`**: FastAPI app initialization, CORS, route registration

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

#### 1. **Fundamental Agent** (`backend/agents/fundamental.py`)
- **Data Sources**: Yahoo Finance (via `tools/market_data.py`)
- **Analysis**:
  - Financial metrics (P/E, EPS, revenue growth, margins)
  - Company fundamentals (market cap, sector, description)
  - Valuation assessment
- **Output**: `FundamentalReport` with summary and key metrics

#### 2. **Sentiment Agent** (`backend/agents/sentiment.py`)
- **Data Sources**: Exa search (via `tools/search.py`)
- **Analysis**:
  - News sentiment (recent headlines, articles)
  - Social media mentions
  - Overall sentiment score (bullish/bearish)
- **Output**: `SentimentReport` with summary and sentiment indicators

#### 3. **Technical Agent** (`backend/agents/technical.py`)
- **Data Sources**: Historical price data (via `tools/market_data.py`)
- **Analysis**:
  - Moving averages (50-day, 200-day)
  - RSI (Relative Strength Index)
  - Trend detection (bullish/bearish/neutral)
  - Support/resistance levels
- **Output**: `TechnicalReport` with summary and indicators

#### 4. **Risk Manager Agent** (`backend/agents/risk_manager.py`)
- **Data Sources**: Portfolio data (via `dao/models.py`), historical prices
- **Analysis**:
  - Portfolio sector concentration (max 30% per sector)
  - Value at Risk (VaR) calculations
  - Volatility assessment
  - **Veto Power**: Can override BUY recommendation if risk too high
- **Output**: `RiskAssessment` with veto decision and reasoning

#### 5. **Chairperson Agent** (`backend/agents/chairperson.py`)
- **Data Sources**: All previous agent reports
- **Analysis**:
  - Weighs fundamental, sentiment, technical reports
  - Considers risk assessment
  - Synthesizes conflicting signals
  - Makes final decision with confidence score
- **Output**: `Decision` with BUY/SELL/HOLD action and reasoning

### LLM Abstraction

The `backend/agents/base.py` module provides a unified interface for multiple LLM providers:

```python
from backend.agents import get_llm_client

llm = get_llm_client()  # Returns AnthropicClient, OpenAIClient, or GeminiClient
response = llm.generate(system_prompt, user_prompt)
```

**Supported Providers**:
- **Anthropic Claude** (default): `claude-3-5-sonnet-20241022`
- **OpenAI GPT-4**: `gpt-4-turbo-preview`
- **Google Gemini**: `gemini-pro`

Provider selection via `LLM_PROVIDER` environment variable.

### State Management

The `AgentState` TypedDict (defined in `backend/state/agent_state.py`) flows through the entire workflow:

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
   - Consolidate `config.py`, `cache.py` into `backend/core/`
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

1. Create `backend/agents/new_agent.py`
2. Define report TypedDict in `backend/state/agent_state.py`
3. Add agent to workflow in `backend/graph/workflow.py`
4. Update `AgentState` to include new report field
5. Wire into frontend in `frontend/src/components/AgentPanel.tsx`
6. Write tests in `tests/test_agents.py`

### Adding a New API Endpoint

1. Add route to `backend/api/routes.py` (or create new module)
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
