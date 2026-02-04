# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Boardroom is a multi-agent financial analysis system using LangGraph. Agents pass a "Token of Authority" between them to collaboratively analyze stocks and make trading decisions.

## Development Commands

```bash
# Backend
uv run uvicorn backend.main:app --reload     # Run API server
uv run pytest tests/ -v                       # Run all tests
uv run pytest tests/test_specific.py -v       # Run specific test file
uv run pytest tests/test_file.py::test_name   # Run single test

# Frontend
cd frontend && npm run dev     # Development server
cd frontend && npm run build   # Production build

# Dependencies
uv sync                        # Install Python dependencies
uv add <package>               # Add Python package
cd frontend && npm install     # Install JS dependencies
```

## Architecture

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

### Key Directories

```
backend/
├── agents/      # All 5 agents + LLM abstraction
├── api/         # FastAPI routes + WebSocket
├── dao/         # SQLAlchemy models for audit trail
├── graph/       # LangGraph workflow
├── state/       # TypedDicts and enums
└── tools/       # Market data, search, technical indicators

frontend/
└── src/
    ├── components/   # React dashboard components
    ├── hooks/        # useWebSocket hook
    └── types/        # TypeScript types
```

### Data Flow

1. User enters ticker in React dashboard
2. WebSocket sends request to FastAPI
3. LangGraph workflow runs agents: Fundamental → Sentiment → Technical (parallel) → Risk Manager → Chairperson
4. Each agent result streams back via WebSocket
5. Dashboard updates in real-time
6. All decisions logged to PostgreSQL
