# CI/CD Workflows & Pre-Commit Hooks Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Set up production-grade CI/CD workflows, pre-commit hooks, and code quality standards to ensure clean commits, safe PRs, and reliable deployments to Railway.

**Architecture:**
- **Pre-commit hooks** catch issues locally (linting, formatting, type checking) for fast feedback
- **PR checks** enforce quality gates on GitHub (tests, coverage thresholds, type safety)
- **Build & push** creates Docker images after merge to main
- **Railway deployment** auto-deploys images with health checks and rollback support

**Tech Stack:** GitHub Actions, pre-commit, ruff, black, mypy, eslint, pytest with coverage, Docker, Railway

---

## Task 1: Create Pre-Commit Configuration

**Files:**
- Create: `.pre-commit-config.yaml`
- Modify: `Makefile` (add pre-commit targets)
- Modify: `.gitignore` (add pre-commit cache)

**Step 1: Write .pre-commit-config.yaml**

Create a new file `.pre-commit-config.yaml` with the following content:

```yaml
# Pre-commit hooks configuration
# Install: pre-commit install
# Run manually: pre-commit run --all-files

repos:
  # General file fixers
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-json
      - id: detect-private-key

  # Python formatting & linting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.2.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  # Python type checking (light - strict check in CI)
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        args: [--ignore-missing-imports, --no-error-summary]
        additional_dependencies: [types-all]
        stages: [commit]

  # JavaScript/TypeScript linting
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v9.0.0
    hooks:
      - id: eslint
        files: frontend/src/.*\.(ts|tsx|js|jsx)$
        types: [file]
        additional_dependencies:
          - eslint
          - '@eslint/js'
          - 'typescript-eslint'
          - 'eslint-plugin-react-hooks'
          - 'eslint-plugin-react-refresh'

  # Secrets detection
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

default_language_version:
  python: python3.13
  node: 18.17.0

default_stages: [commit]
ci:
  autofix_commit_msg: 'chore: auto-format with pre-commit'
  autofix_prs: true
  autoupdate_branch: ''
  autoupdate_commit_msg: 'chore: pre-commit autoupdate'
  skip: [mypy]  # mypy takes too long, skip in CI
  stages: [commit]
```

**Step 2: Initialize secrets baseline**

Run: `uv run detect-secrets scan --baseline .secrets.baseline`

This creates a baseline file to track known secrets (API keys in .env).

**Step 3: Update Makefile to add pre-commit targets**

Add these lines to the Makefile (before `.PHONY` line, update it):

```makefile
.PHONY: help dev prod down logs test lint migrate db-up db-down clean build pre-commit-install pre-commit-run

# ... existing content ...

# Pre-commit hooks
pre-commit-install:
	@echo "Installing pre-commit hooks..."
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "Pre-commit hooks installed. Run 'pre-commit run --all-files' to test."

pre-commit-run:
	pre-commit run --all-files

pre-commit-update:
	pre-commit autoupdate
```

**Step 4: Update .gitignore to include pre-commit cache**

Add to `.gitignore`:

```
# Pre-commit
.pre-commit/
.secrets.baseline
```

**Step 5: Test the configuration locally**

Run: `pre-commit install`
Then: `pre-commit run --all-files`

Expected: Some files may be reformatted. Run again to verify all pass.

**Step 6: Commit**

```bash
git add .pre-commit-config.yaml .secrets.baseline Makefile .gitignore
git commit -m "feat: add pre-commit hooks for code quality"
```

---

## Task 2: Configure Python Linting & Type Checking

**Files:**
- Create: `.ruff.toml`
- Create: `pyproject.toml` (update existing)
- Create: `.mypy.ini`

**Step 1: Create .ruff.toml for linting configuration**

```toml
# Ruff configuration
[lint]
# Enable specific rule sets
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort (import sorting)
    "N",      # pep8-naming
    "ASYNC",  # flake8-async
    "RUF",    # ruff-specific rules
]
ignore = [
    "E501",   # line too long (black handles this)
    "W503",   # line break before binary operator (conflicts with black)
]

# Exclude test directories from some checks
exclude = [
    "tests/",
    ".venv/",
    "__pycache__/",
]

[format]
# Match black's formatting
line-length = 88
indent-width = 4
```

**Step 2: Update pyproject.toml with tool configs**

Update the existing `pyproject.toml` file. Add this section after the `[project.optional-dependencies]` section:

```toml
[tool.black]
line-length = 88
target-version = ['py313']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 88
multi_line_mode = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
skip_glob = ["*/migrations/*", ".venv/*"]

[tool.mypy]
python_version = "3.13"
check_untyped_defs = true
ignore_missing_imports = true
warn_unused_ignores = true
warn_redundant_casts = true
warn_unused_configs = true
disallow_incomplete_defs = false
disallow_untyped_defs = false

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_scope = "function"
markers = [
    "unit: Unit tests (fast, no external deps)",
    "integration: Integration tests (requires PostgreSQL)",
]
addopts = "--strict-markers -ra"

[tool.coverage.run]
source = ["backend"]
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__init__.py",
    "*/migrations/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
    "pass",
    "\\.\\.\\.",
]
fail_under = 80
precision = 2
```

**Step 3: Create .mypy.ini**

```ini
[mypy]
python_version = 3.13
check_untyped_defs = True
disallow_any_generics = False
disallow_incomplete_defs = False
disallow_untyped_defs = False
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_configs = True
warn_unused_ignores = True
warn_no_return = True

[mypy-tests.*]
ignore_errors = True

[mypy-backend.core.settings]
ignore_missing_imports = True

[mypy-sqlalchemy.*]
ignore_missing_imports = True

[mypy-langgraph.*]
ignore_missing_imports = True

[mypy-yfinance.*]
ignore_missing_imports = True

[mypy-redis.*]
ignore_missing_imports = True

[mypy-httpx.*]
ignore_missing_imports = True
```

**Step 4: Test ruff and mypy**

Run: `uv run ruff check backend tests --fix`
Then: `uv run mypy backend`

Expected: May find some issues to fix, but should complete.

**Step 5: Commit**

```bash
git add .ruff.toml .mypy.ini pyproject.toml
git commit -m "feat: configure Python linting and type checking (ruff, mypy)"
```

---

## Task 3: Configure Frontend Linting & TypeScript

**Files:**
- Modify: `frontend/.eslintrc.cjs`
- Modify: `frontend/tsconfig.json`
- Modify: `frontend/package.json` (add test script)

**Step 1: Verify/Update frontend/.eslintrc.cjs**

Check that frontend/.eslintrc.cjs exists. If it does, update it to be stricter:

```javascript
import js from '@eslint/js'
import globals from 'globals'
import react from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  { ignores: ['dist', 'node_modules'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      sourceType: 'module',
    },
    plugins: {
      react,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...react.configs.recommended.rules,
      'react/react-in-jsx-scope': 'off',
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      '@typescript-eslint/no-explicit-any': 'warn',
      'no-console': ['warn', { allow: ['warn', 'error'] }],
    },
  }
)
```

**Step 2: Update frontend/tsconfig.json**

Ensure these settings are present (strict mode):

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "esModuleInterop": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.app.json" }]
}
```

**Step 3: Add test script to frontend/package.json**

Update the `scripts` section in `frontend/package.json`:

```json
"scripts": {
  "dev": "vite",
  "build": "tsc -b && vite build",
  "lint": "eslint . --fix",
  "type-check": "tsc --noEmit",
  "preview": "vite preview"
}
```

**Step 4: Test frontend linting**

Run: `cd frontend && npm run lint && npm run type-check`

Expected: ESLint and TypeScript pass (may auto-fix some issues).

**Step 5: Commit**

```bash
git add frontend/.eslintrc.cjs frontend/tsconfig.json frontend/package.json
git commit -m "feat: configure frontend linting and TypeScript strict mode"
```

---

## Task 4: Create GitHub Actions - PR Checks Workflow

**Files:**
- Create: `.github/workflows/pr-checks.yml`

**Step 1: Create .github directory**

Run: `mkdir -p .github/workflows`

**Step 2: Create PR checks workflow**

Create `.github/workflows/pr-checks.yml`:

```yaml
name: PR Checks

on:
  pull_request:
    branches: [main]
    paths:
      - 'backend/**'
      - 'frontend/**'
      - 'tests/**'
      - 'pyproject.toml'
      - 'frontend/package.json'
      - '.github/workflows/pr-checks.yml'

jobs:
  backend-lint:
    name: Backend Linting
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install uv
        uses: astral-sh/setup-uv@v2

      - name: Install dependencies
        run: uv sync

      - name: Run ruff lint
        run: uv run ruff check backend tests

      - name: Run ruff format check
        run: uv run ruff format --check backend tests

      - name: Run mypy type check
        run: uv run mypy backend

  backend-test:
    name: Backend Tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: boardroom_test
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: boardroom_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5433:5432

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install uv
        uses: astral-sh/setup-uv@v2

      - name: Install dependencies
        run: uv sync

      - name: Run backend tests with coverage
        env:
          TEST_DATABASE_URL: postgresql+asyncpg://boardroom_test:test_password@localhost:5433/boardroom_test
        run: uv run pytest tests/ -v --cov=backend --cov-report=xml --cov-report=term-missing

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          flags: backend
          fail_ci_if_error: false

      - name: Check coverage threshold (80%)
        run: |
          coverage_percent=$(grep -oP 'TOTAL.*?(\d+)%' <<< "$(uv run coverage report)" | grep -oP '\d+' | tail -1)
          if [ "$coverage_percent" -lt 80 ]; then
            echo "❌ Backend coverage is $coverage_percent%, minimum is 80%"
            exit 1
          fi
          echo "✅ Backend coverage is $coverage_percent%"

  frontend-lint:
    name: Frontend Linting
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: 'frontend/package-lock.json'

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Run ESLint
        run: cd frontend && npm run lint

      - name: Run TypeScript type check
        run: cd frontend && npm run type-check

  secrets-check:
    name: Detect Secrets
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Detect secrets
        uses: Yelp/detect-secrets-action@v1
        with:
          baseline: .secrets.baseline
```

**Step 3: Test the workflow by viewing it**

Run: `cat .github/workflows/pr-checks.yml`

Expected: Valid YAML structure, no syntax errors.

**Step 4: Commit**

```bash
git add .github/workflows/pr-checks.yml
git commit -m "feat: add PR checks workflow (lint, test, coverage)"
```

---

## Task 5: Create GitHub Actions - Build & Push Workflow

**Files:**
- Create: `.github/workflows/build-and-push.yml`

**Step 1: Create build and push workflow**

Create `.github/workflows/build-and-push.yml`:

```yaml
name: Build and Push Docker Images

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'
      - 'frontend/**'
      - 'docker/**'
      - '.github/workflows/build-and-push.yml'
  workflow_dispatch:

jobs:
  build-backend:
    name: Build Backend Image
    runs-on: ubuntu-latest
    permissions:
      contents: read

    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ secrets.DOCKER_USERNAME }}/boardroom-backend
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-
            type=raw,value=latest

      - name: Build and push backend
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./backend/docker/Dockerfile.prod
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  build-frontend:
    name: Build Frontend Image
    runs-on: ubuntu-latest
    permissions:
      contents: read

    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ secrets.DOCKER_USERNAME }}/boardroom-frontend
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-
            type=raw,value=latest

      - name: Build and push frontend
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          file: ./frontend/docker/Dockerfile.prod
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  trigger-deploy:
    name: Trigger Deployment
    needs: [build-backend, build-frontend]
    runs-on: ubuntu-latest
    if: success()

    steps:
      - name: Notify deployment
        run: |
          echo "✅ Docker images built and pushed successfully"
          echo "Backend: ${{ needs.build-backend.outputs.image-tag }}"
          echo "Frontend: ${{ needs.build-frontend.outputs.image-tag }}"
          echo "Railway deployment will auto-trigger from Docker Hub webhook"
```

**Step 2: Verify workflow syntax**

Run: `cat .github/workflows/build-and-push.yml`

Expected: Valid YAML, no syntax errors.

**Step 3: Commit**

```bash
git add .github/workflows/build-and-push.yml
git commit -m "feat: add build and push workflow for Docker images"
```

---

## Task 6: Create GitHub Actions - Deploy Workflow (Railway)

**Files:**
- Create: `.github/workflows/deploy-railway.yml`

**Step 1: Create deployment workflow**

Create `.github/workflows/deploy-railway.yml`:

```yaml
name: Deploy to Railway

on:
  push:
    branches: [main]
  workflow_run:
    workflows: ["Build and Push Docker Images"]
    types: [completed]
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    name: Deploy to Railway
    runs-on: ubuntu-latest
    if: github.event_name == 'push' || github.event.workflow_run.conclusion == 'success'

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Railway
        run: |
          # Install Railway CLI
          curl -L https://railway.app/install.sh | bash

          # Authenticate with Railway
          railway login --token ${{ secrets.RAILWAY_TOKEN }}

          # Deploy project
          railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

      - name: Health check
        run: |
          # Wait for deployment
          sleep 30

          # Check backend health
          backend_health=$(curl -s -o /dev/null -w "%{http_code}" https://${{ secrets.RAILWAY_BACKEND_URL }}/health || echo "000")
          if [ "$backend_health" != "200" ]; then
            echo "❌ Backend health check failed: $backend_health"
            exit 1
          fi
          echo "✅ Backend health check passed"

      - name: Notify deployment success
        if: success()
        run: |
          echo "✅ Deployment to Railway successful"
          echo "Backend: https://${{ secrets.RAILWAY_BACKEND_URL }}"
          echo "Frontend: https://${{ secrets.RAILWAY_FRONTEND_URL }}"

      - name: Notify deployment failure
        if: failure()
        run: |
          echo "❌ Deployment to Railway failed"
          exit 1

  rollback:
    name: Rollback on Failure
    runs-on: ubuntu-latest
    needs: deploy
    if: failure()

    steps:
      - name: Rollback to previous version
        run: |
          curl -L https://railway.app/install.sh | bash
          railway login --token ${{ secrets.RAILWAY_TOKEN }}

          # Railway auto-rollback via deployment history
          echo "ℹ️ Manually rollback via Railway dashboard if needed"
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

**Step 2: Verify workflow**

Run: `cat .github/workflows/deploy-railway.yml`

Expected: Valid YAML structure.

**Step 3: Commit**

```bash
git add .github/workflows/deploy-railway.yml
git commit -m "feat: add deployment workflow for Railway"
```

---

## Task 7: Create CONTRIBUTING.md Guide

**Files:**
- Create: `docs/CONTRIBUTING.md`

**Step 1: Create contributing guide**

Create `docs/CONTRIBUTING.md`:

```markdown
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
```

**Step 2: Verify file**

Run: `cat docs/CONTRIBUTING.md | head -50`

Expected: Valid markdown, clear instructions.

**Step 3: Commit**

```bash
git add docs/CONTRIBUTING.md
git commit -m "docs: add comprehensive contributing guide"
```

---

## Task 8: Update GitHub CODEOWNERS & Add Status Badge

**Files:**
- Create: `.github/CODEOWNERS`
- Modify: `README.md` (add status badge)

**Step 1: Create CODEOWNERS file**

Create `.github/CODEOWNERS`:

```
# CODEOWNERS file - require approvals for sensitive areas

# Backend core
/backend/core/**          @ofircohen
/backend/ai/**            @ofircohen
/backend/db/**            @ofircohen

# Frontend
/frontend/src/**          @ofircohen

# Configuration
*.yml                     @ofircohen
*.yaml                    @ofircohen
pyproject.toml            @ofircohen
Makefile                  @ofircohen
docker/**                 @ofircohen

# Documentation
docs/                     @ofircohen
```

**Step 2: Update README.md with status badge**

Add this to the top of `README.md` (after the title):

```markdown
[![PR Checks](https://github.com/yourusername/boardroom/actions/workflows/pr-checks.yml/badge.svg)](https://github.com/yourusername/boardroom/actions/workflows/pr-checks.yml)
[![Build & Push](https://github.com/yourusername/boardroom/actions/workflows/build-and-push.yml/badge.svg)](https://github.com/yourusername/boardroom/actions/workflows/build-and-push.yml)
```

**Step 3: Commit**

```bash
git add .github/CODEOWNERS README.md
git commit -m "docs: add CODEOWNERS and CI status badges"
```

---

## Task 9: Create .gitignore Updates for Build Artifacts

**Files:**
- Modify: `.gitignore`

**Step 1: Enhance .gitignore**

Update `.gitignore` with additional patterns:

```
# Python-generated files
__pycache__/
*.py[oc]
build/
dist/
wheels/
*.egg-info

# Virtual environments
.venv

# Git worktrees
.worktrees/

# Environment variables
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
coverage.xml

# Pre-commit
.pre-commit/

# Frontend
frontend/node_modules/
frontend/dist/
frontend/.env.local

# Backend build
backend/__pycache__/
backend/*.egg-info/

# OS
.DS_Store
Thumbs.db

# Secrets
.secrets.baseline
```

**Step 2: Verify .gitignore**

Run: `cat .gitignore`

Expected: Comprehensive ignoring of build artifacts, cache, secrets.

**Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: enhance .gitignore for build artifacts"
```

---

## Task 10: Test Everything & Create Summary

**Files:**
- No new files, just verify everything works

**Step 1: Run pre-commit on all files**

Run: `pre-commit run --all-files`

Expected: All checks pass (some files may be auto-formatted). Run again if needed.

**Step 2: Test backend linting & types**

Run: `uv run ruff check backend tests && uv run ruff format --check backend tests && uv run mypy backend`

Expected: All pass (0 errors).

**Step 3: Test frontend linting & types**

Run: `cd frontend && npm run lint && npm run type-check`

Expected: All pass (0 errors).

**Step 4: Run unit tests**

Run: `make test-unit`

Expected: 126+ tests pass.

**Step 5: Verify all workflow files exist**

Run: `ls -la .github/workflows/`

Expected: Three YAML files (pr-checks, build-and-push, deploy-railway).

**Step 6: Create summary document**

Create `.github/WORKFLOWS.md`:

```markdown
# GitHub Actions Workflows

## Overview

This project uses 3 main CI/CD workflows to ensure code quality and reliable deployments.

### PR Checks (`pr-checks.yml`)

**Triggers:** On every push to a PR targeting `main`

**Jobs:**
1. **Backend Lint** - ruff format & check, mypy type checking
2. **Backend Test** - pytest with coverage (80% threshold)
3. **Frontend Lint** - ESLint, TypeScript strict mode
4. **Secrets Check** - Detect private keys, API keys

**Status:** Must pass before merge

**Coverage reports:** Uploaded to Codecov

### Build & Push (`build-and-push.yml`)

**Triggers:** On push to `main` (after PR merge)

**Jobs:**
1. **Build Backend** - Docker image with Python 3.13
2. **Build Frontend** - Docker image with Node 18
3. **Push to Registry** - Push tagged images to Docker Hub

**Tags created:**
- `latest` - Latest main branch
- `main-sha-xxxxx` - Commit SHA
- Git tags (when released)

**Requires secrets:**
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`

### Deploy (`deploy-railway.yml`)

**Triggers:** On push to `main` (after build completes)

**Jobs:**
1. **Deploy** - Deploy to Railway using Railway CLI
2. **Health Check** - Verify backend is responding
3. **Rollback** - Manual rollback option if deploy fails

**Requires secrets:**
- `RAILWAY_TOKEN`
- `RAILWAY_BACKEND_URL`
- `RAILWAY_FRONTEND_URL`

## Setting Up Secrets

### GitHub Secrets

Go to Settings > Secrets and variables > Actions:

1. **DOCKER_USERNAME** - Docker Hub username
2. **DOCKER_PASSWORD** - Docker Hub access token
3. **RAILWAY_TOKEN** - Railway API token
4. **RAILWAY_BACKEND_URL** - Deployed backend URL (e.g., api.boardroom.railway.app)
5. **RAILWAY_FRONTEND_URL** - Deployed frontend URL (e.g., boardroom.railway.app)

### Creating Docker Hub Token

1. Go to https://hub.docker.com/settings/security
2. Create "Personal Access Token"
3. Copy and paste into GitHub Secrets

### Creating Railway Token

1. Go to https://railway.app/account/tokens
2. Create new token
3. Copy and paste into GitHub Secrets

## Local Pre-Commit Hooks

Pre-commit runs automatically when you commit:

```bash
# Install hooks
make pre-commit-install

# Run manually
make pre-commit-run

# Update hook versions
make pre-commit-update
```

Hooks run:
- Python: ruff (lint + format), mypy (type check)
- JavaScript: eslint (lint + format), tsc (type check)
- General: detect-secrets, trailing-whitespace, end-of-file-fixer

## Monitoring Status

### GitHub UI

- Go to Actions tab to see workflow status
- Click workflow name to see details
- Click job to see logs

### Badge in README

PR Checks: [![PR Checks](https://github.com/.../badge.svg)]()

Build & Push: [![Build & Push](https://github.com/.../badge.svg)]()

## Troubleshooting

**PR checks fail - coverage too low:**
```bash
# Run locally to debug
make test-cov
# View coverage report: htmlcov/index.html
```

**Build fails - Docker image errors:**
```bash
# Build locally
docker build -f backend/docker/Dockerfile.prod -t test .
```

**Deploy fails - Railway error:**
```bash
# Check Railway logs
railway logs

# Rollback via dashboard or CLI
railway up --remove-version <version-id>
```

**Pre-commit hook skipped in CI:**
Some hooks (mypy) are skipped in CI to save time. Type checking is run as a separate job.

---

For detailed instructions, see [docs/CONTRIBUTING.md](../docs/CONTRIBUTING.md)
```

**Step 7: Commit summary**

```bash
git add .github/WORKFLOWS.md
git commit -m "docs: add workflows documentation"
```

---

## Final Checklist

**Verify completion:**

- [ ] `.pre-commit-config.yaml` created and installed
- [ ] `.ruff.toml`, `.mypy.ini`, `pyproject.toml` updated
- [ ] Frontend ESLint & TypeScript configured
- [ ] `.github/workflows/pr-checks.yml` created
- [ ] `.github/workflows/build-and-push.yml` created
- [ ] `.github/workflows/deploy-railway.yml` created
- [ ] `docs/CONTRIBUTING.md` created
- [ ] `.github/CODEOWNERS` created
- [ ] `.github/WORKFLOWS.md` created
- [ ] `.gitignore` enhanced
- [ ] All local tests pass (backend lint, type check, frontend lint, type check)
- [ ] All 10 tasks committed with clear messages

**Post-Implementation:**

1. Push branch and create PR to main
2. Verify PR checks pass
3. Merge PR to main
4. Verify build & push workflow runs
5. Set up GitHub Secrets (DOCKER_USERNAME, DOCKER_PASSWORD, RAILWAY_TOKEN)
6. Verify deployment workflow runs
7. Test pre-commit hooks locally: `make pre-commit-install && make pre-commit-run --all-files`
8. Have team members install hooks: `make pre-commit-install`

---

Plan complete! Ready to implement? Choose your approach:

**Option 1: Subagent-Driven (Recommended)**
- Fresh subagent per task
- Code review between tasks
- Fast iteration in current session

**Option 2: Parallel Session**
- Batch execution with checkpoints
- Separate session using executing-plans skill

Which would you prefer?
