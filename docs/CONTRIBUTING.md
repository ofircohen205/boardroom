# Contributing to Boardroom

This guide explains how to set up your development environment, use pre-commit hooks, and submit high-quality PRs.

## Prerequisites

- Python 3.13+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 16 (for local testing)
- `uv` (Python package manager)
- `pre-commit` (git hooks framework)

## Initial Setup

### 1. Clone and Install Dependencies

```bash
git clone https://github.com/yourusername/boardroom.git
cd boardroom

# Install Python and frontend dependencies
make install

# Set up pre-commit hooks
make pre-commit-install
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required variables:
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` or `GOOGLE_API_KEY`
- `DATABASE_URL` (local PostgreSQL)
- `EXA_API_KEY` (news/social search)

### 3. Start Development Environment

```bash
# Start all services (backend, frontend, database)
make dev

# Or individually:
make db-up              # Start PostgreSQL
cd frontend && npm run dev  # Start frontend dev server
uv run uvicorn backend.main:app --reload  # Start backend
```

Access:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Database: localhost:5432

## Pre-Commit Hooks

Pre-commit hooks run automatically when you commit. They catch common issues early:

- **Code formatting** (ruff, black, prettier)
- **Import sorting** (isort)
- **Type checking** (mypy for Python, TypeScript for frontend)
- **Linting** (ruff for Python, ESLint for frontend)
- **Secrets detection**

### Running Pre-Commit Manually

```bash
# Run all hooks on all files
make pre-commit-run

# Run specific hook
pre-commit run black --all-files
pre-commit run eslint --all-files

# Update hook versions
make pre-commit-update
```

If a hook fails, it will auto-fix what it can. Review changes and commit again.

## Code Quality Standards

### Backend

- **Style:** PEP 8 (enforced by ruff + black)
- **Type hints:** Required for all functions
- **Tests:** Aim for >80% coverage (enforced in CI)
- **Linting:** 0 ruff errors allowed

Run locally:

```bash
# Check all backend code
uv run ruff check backend tests
uv run ruff format --check backend tests
uv run mypy backend

# Format automatically
uv run ruff format backend tests
uv run ruff check backend tests --fix
```

### Frontend

- **Style:** ESLint rules (enforced in pre-commit)
- **Type Safety:** Strict TypeScript (noUnusedLocals, noUnusedParameters)
- **Formatting:** prettier via ESLint
- **Components:** <200 lines, functional, custom hooks

Run locally:

```bash
cd frontend

# Check code
npm run lint
npm run type-check

# Format automatically
npm run lint  # ESLint auto-fixes most issues
```

## Testing

### Run Tests Locally

```bash
# Unit tests (fast, no database)
make test-unit

# Integration tests (requires PostgreSQL on :5433)
make test-integration

# All tests with coverage
make test-cov
```

### Write Tests

- **Unit tests** in `tests/unit/` (use SQLite mocks)
- **Integration tests** in `tests/integration/` (use PostgreSQL)
- Aim for >80% coverage
- Mock external APIs (LLMs, Yahoo Finance, Exa)

Example test file structure:

```python
import pytest
from unittest.mock import AsyncMock, patch

# Unit test - fast, no external deps
@pytest.mark.unit
async def test_agent_returns_report():
    agent = FundamentalAgent(mock_llm)
    report = await agent.analyze("AAPL")
    assert report.ticker == "AAPL"
    assert report.summary is not None

# Integration test - requires database
@pytest.mark.integration
async def test_analysis_session_saved(db_session):
    session = AnalysisSession(ticker="AAPL")
    db_session.add(session)
    await db_session.commit()
    assert session.id is not None
```

## Workflow

### 1. Create a Branch

```bash
# Always branch from main
git checkout main
git pull origin main

# Create feature branch (use conventional prefix)
git checkout -b feat/auth-endpoints
git checkout -b fix/websocket-reconnect
git checkout -b docs/agent-architecture
```

### 2. Make Changes

- Write tests first (TDD)
- Keep commits small and atomic
- Use conventional commit messages:
  - `feat:` New feature
  - `fix:` Bug fix
  - `docs:` Documentation
  - `refactor:` Code refactoring
  - `test:` Adding/updating tests
  - `chore:` Build, deps, etc.

### 3. Pre-Commit Checks

```bash
# Hooks run automatically on commit
git add .
git commit -m "feat: add user authentication endpoint"

# If hooks fail, review changes and commit again
git add .
git commit -m "feat: add user authentication endpoint"
```

### 4. Push and Create PR

```bash
git push origin feat/auth-endpoints
# Open PR on GitHub
```

**PR Requirements:**
- All CI checks pass (linting, tests, coverage)
- >80% backend test coverage
- TypeScript strict mode passes
- No secrets in code
- Clear description of changes

### 5. Code Review & Merge

- Respond to reviewer feedback
- Push fixes as new commits (don't force-push)
- Once approved, merge with squash or rebase

## GitHub Actions (Automated CI/CD)

All pushes to `main` or PRs trigger automated checks:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **PR Checks** | PR to main | Linting, tests, coverage |
| **Build & Push** | Push to main | Build Docker images, push to registry |
| **Deploy** | After build | Deploy to Railway, health checks |

**Common Issues:**

- **Coverage check fails:** Increase test coverage or update threshold
- **Type check fails:** Add type hints or `# type: ignore` comments
- **Linting fails:** Run `make pre-commit-run` to auto-fix
- **Tests fail:** Debug locally with `make test-cov`

## Database Migrations

```bash
# Create a new migration after model changes
make db-revision MSG="add watchlist table"

# This creates a new file in alembic/versions/

# Review migration, then apply it
make db-migrate

# Test rollback
alembic downgrade -1
make db-migrate  # apply again
```

## Docker Development

When adding dependencies:

```bash
# Python
uv add <package>

# JavaScript
cd frontend && npm install <package>

# If using Docker, rebuild
docker compose -f docker/docker-compose.dev.yml up -d --build --force-recreate
```

## Tips & Tricks

```bash
# Run specific test
pytest tests/test_agents.py::test_fundamental_agent -v

# Debug mode
pytest tests/test_agents.py -v -s  # -s shows print() output

# Clear test cache
rm -rf .pytest_cache

# Reset Docker environment
make clean

# View backend logs
make logs-backend

# Shell into container
make shell-backend
```

## Getting Help

- Check [CLAUDE.md](../CLAUDE.md) for architecture overview
- See [AGENTS.md](../AGENTS.md) for agent system details
- Check [docs/ARCHITECTURE.md](./ARCHITECTURE.md) for data flow
- Open an issue on GitHub for bugs/questions

---

**Thank you for contributing! 🚀**
