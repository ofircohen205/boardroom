# Boardroom

Multi-agent financial analysis system with React dashboard.

## Quick Start

### Backend

```bash
# Install dependencies
uv sync

# Copy environment file and add your API keys
cp .env.example .env

# Run the server
uv run uvicorn backend.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Database

```bash
# Option 1: Docker
docker run -d --name boardroom-db \
  -e POSTGRES_DB=boardroom \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 postgres:16

# Option 2: Local PostgreSQL
createdb boardroom
```

## Environment Variables

```
LLM_PROVIDER=anthropic  # or openai or gemini
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=
EXA_API_KEY=
DATABASE_URL=postgresql+asyncpg://localhost/boardroom
```

## Architecture

See `docs/plans/2026-02-02-boardroom-design.md` for full architecture documentation.
