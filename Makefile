.PHONY: help dev prod down logs test lint migrate db-up db-down clean build pre-commit-install pre-commit-run pre-commit-update

# Default target
help:
	@echo "Boardroom - Multi-Agent Financial Analysis System"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Development:"
	@echo "  dev          Start development environment (backend + frontend + db)"
	@echo "  down         Stop all containers"
	@echo "  logs         Follow container logs"
	@echo "  logs-backend Follow backend logs only"
	@echo "  logs-frontend Follow frontend logs only"
	@echo ""
	@echo "Database:"
	@echo "  db-up        Start database only"
	@echo "  db-down      Stop database"
	@echo "  migrate      Run database migrations (local)"
	@echo "  migrate-docker Run database migrations in Docker"
	@echo "  migrate-new  Create new migration (usage: make migrate-new msg='description')"
	@echo ""
	@echo "Testing:"
	@echo "  test         Run all tests (with PostgreSQL for integration tests)"
	@echo "  test-unit    Run unit tests only (fast, uses SQLite)"
	@echo "  test-integration Run integration tests only (uses PostgreSQL)"
	@echo "  test-cov     Run tests with coverage"
	@echo "  test-db-up   Start test database (PostgreSQL on port 5433)"
	@echo "  test-db-down Stop test database"
	@echo ""
	@echo "Production:"
	@echo "  prod         Start production environment"
	@echo "  prod-down    Stop production environment"
	@echo "  build        Build production images"
	@echo ""
	@echo "Utilities:"
	@echo "  install      Install all dependencies"
	@echo "  clean        Remove all containers, volumes, and build artifacts"
	@echo "  shell-backend  Open shell in backend container"
	@echo "  shell-db       Open psql in database container"

# Development
dev:
	docker compose -p boardroom -f docker/docker-compose.dev.yml up -d --build --force-recreate -V
	@echo "Development environment started"
	@echo "  Frontend: http://localhost:5173"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Database: localhost:5432"
	@echo "  Redis:    localhost:6379"

down:
	docker compose -p boardroom -f docker/docker-compose.dev.yml down

logs:
	docker compose -p boardroom -f docker/docker-compose.dev.yml logs -f

logs-backend:
	docker compose -p boardroom -f docker/docker-compose.dev.yml logs -f boardroom-backend

logs-frontend:
	docker compose -p boardroom -f docker/docker-compose.dev.yml logs -f boardroom-frontend

# Database
db-up:
	docker compose -p boardroom -f docker/docker-compose.dev.yml up -d boardroom-postgres-db
	@echo "Waiting for database to be ready..."
	@sleep 3
	@docker compose -p boardroom -f docker/docker-compose.dev.yml exec boardroom-postgres-db pg_isready -U boardroom

db-down:
	docker compose -p boardroom -f docker/docker-compose.dev.yml stop boardroom-postgres-db

migrate:
	uv run alembic upgrade head

migrate-docker:
	docker compose -p boardroom -f docker/docker-compose.dev.yml exec backend uv run alembic upgrade head

migrate-new:
	uv run alembic revision --autogenerate -m "$(msg)"

# Testing
test-db-up:
	docker compose -f docker/docker-compose.test.yml up -d
	@echo "Waiting for test database to be ready..."
	@sleep 2
	@docker compose -f docker/docker-compose.test.yml exec postgres-test pg_isready -U boardroom_test || true

test-db-down:
	docker compose -f docker/docker-compose.test.yml down -v

test-unit:
	@echo "Running unit tests (SQLite)..."
	uv run pytest tests/unit/ -v

test-integration: test-db-up
	@echo "Running integration tests (PostgreSQL)..."
	TEST_DATABASE_URL=postgresql+asyncpg://boardroom_test:test_password@localhost:5433/boardroom_test \
		uv run pytest tests/integration/ -v
	$(MAKE) test-db-down

test: test-db-up
	@echo "Running all tests..."
	TEST_DATABASE_URL=postgresql+asyncpg://boardroom_test:test_password@localhost:5433/boardroom_test \
		uv run pytest tests/ -v
	$(MAKE) test-db-down

test-cov: test-db-up
	TEST_DATABASE_URL=postgresql+asyncpg://boardroom_test:test_password@localhost:5433/boardroom_test \
		uv run pytest tests/ -v --cov=backend --cov-report=term-missing
	$(MAKE) test-db-down

# Production
prod:
	docker compose -f docker/docker-compose.prod.yml up -d
	@echo "Production environment started"
	@echo "  Frontend: http://localhost:80"

prod-down:
	docker compose -f docker/docker-compose.prod.yml down

build:
	docker compose -f docker/docker-compose.prod.yml build

# Utilities
install:
	uv sync --all-extras
	cd frontend && npm install

clean:
	docker compose -p boardroom -f docker/docker-compose.dev.yml down -v --remove-orphans
	docker compose -p boardroom -f docker/docker-compose.prod.yml down -v --remove-orphans 2>/dev/null || true
	rm -rf .venv frontend/node_modules frontend/dist
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

shell-backend:
	docker compose -p boardroom -f docker/docker-compose.dev.yml exec boardroom-backend /bin/sh

shell-db:
	docker compose -p boardroom -f docker/docker-compose.dev.yml exec boardroom-postgres-db psql -U boardroom -d boardroom

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
