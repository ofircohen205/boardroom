# Getting Started

This guide will help you set up and run the Boardroom Multi-Agent Financial Analysis System.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** and **Docker Compose** (recommended method)
- **Node.js** v18+ and npm (for local frontend development)
- **Python 3.11+** and [uv](https://github.com/astral-sh/uv) (for local backend development)
- **PostgreSQL 16** (if running database locally)

## Quick Start with Docker (Recommended)

The fastest way to get started is using Docker Compose, which handles all dependencies automatically.

### 1. Clone and Configure

```bash
# Clone the repository
git clone <repository-url>
cd boardroom

# Copy environment file
cp .env.example .env
```

### 2. Add Your API Keys

Edit the `.env` file and add your API keys:

```env
# Required: Choose your LLM provider and add key
LLM_PROVIDER=anthropic  # or openai or gemini
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Optional: For market data and search
ALPHA_VANTAGE_API_KEY=...
EXA_API_KEY=...
```

### 3. Start the Application

```bash
make dev
```

This single command starts:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Database**: PostgreSQL on port 5432

### 4. Verify Installation

- Open http://localhost:5173 in your browser
- You should see the Boardroom dashboard

## Local Development Setup (Without Docker)

For more control during development, you can run services locally.

### Database Setup

```bash
# Option 1: Use Docker for just the database
make db-up

# Option 2: Local PostgreSQL
createdb boardroom
```

### Backend Setup

```bash
# Install Python dependencies
uv sync

# Run database migrations
make migrate

# Start the backend server
uv run uvicorn backend.main:app --reload
```

The backend API will be available at http://localhost:8000

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:5173

## Available Make Commands

| Command              | Description                               |
| -------------------- | ----------------------------------------- |
| `make dev`           | Start full development environment        |
| `make down`          | Stop all containers                       |
| `make logs`          | Follow all container logs                 |
| `make logs-backend`  | Follow backend logs only                  |
| `make logs-frontend` | Follow frontend logs only                 |
| `make db-up`         | Start database only                       |
| `make migrate`       | Run database migrations                   |
| `make test`          | Run all tests                             |
| `make clean`         | Remove all containers and build artifacts |

## Environment Variables Reference

| Variable                | Description                                     | Required    |
| ----------------------- | ----------------------------------------------- | ----------- |
| `LLM_PROVIDER`          | AI provider: `anthropic`, `openai`, or `gemini` | Yes         |
| `ANTHROPIC_API_KEY`     | Anthropic API key (if using Claude)             | Conditional |
| `OPENAI_API_KEY`        | OpenAI API key (if using GPT)                   | Conditional |
| `GOOGLE_API_KEY`        | Google API key (if using Gemini)                | Conditional |
| `DATABASE_URL`          | PostgreSQL connection string                    | Yes         |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API for market data               | Optional    |
| `EXA_API_KEY`           | Exa search API key                              | Optional    |

## Troubleshooting

### Port Already in Use

If you get a port conflict error:

```bash
# Stop existing containers
make down

# Or kill processes on specific ports
lsof -ti :5173 | xargs kill -9  # Frontend
lsof -ti :8000 | xargs kill -9  # Backend
lsof -ti :5432 | xargs kill -9  # Database
```

### Database Connection Issues

```bash
# Ensure database is running
docker compose ps

# Check database logs
docker compose logs db

# Reset database
make clean
make dev
```

### Frontend Not Loading

```bash
# Check frontend logs
make logs-frontend

# Rebuild frontend container
docker compose up -d --build frontend
```

## Next Steps

- Read the [Usage Guide](./usage-guide.md) to learn how to use the application
- Check the [Architecture Documentation](./plans/2026-02-02-boardroom-design.md) for technical details
