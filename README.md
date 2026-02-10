# Boardroom

[![PR Checks](https://github.com/ofircohen205/boardroom/actions/workflows/pr-checks.yml/badge.svg)](https://github.com/ofircohen205/boardroom/actions/workflows/pr-checks.yml)
[![Build & Push](https://github.com/ofircohen205/boardroom/actions/workflows/build-and-push.yml/badge.svg)](https://github.com/ofircohen205/boardroom/actions/workflows/build-and-push.yml)

Multi-agent financial analysis system with React dashboard.

## Quick Start

```bash
# Clone and configure
cp .env.example .env
# Edit .env to add your API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY)

# Start with Docker (recommended)
make dev
```

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000

## Documentation

| Guide                                      | Description                                                |
| ------------------------------------------ | ---------------------------------------------------------- |
| [Getting Started](docs/getting-started.md) | Full setup guide with Docker and local development options |
| [Usage Guide](docs/usage-guide.md)         | How to use the dashboard and run stock analysis            |

## Make Commands

```bash
make dev      # Start development environment
make down     # Stop all containers
make logs     # View container logs
make test     # Run tests
make clean    # Remove containers and artifacts
```

Run `make help` for all available commands.

## Environment Variables

| Variable                | Description                        |
| ----------------------- | ---------------------------------- |
| `LLM_PROVIDER`          | `anthropic`, `openai`, or `gemini` |
| `ANTHROPIC_API_KEY`     | Anthropic API key                  |
| `OPENAI_API_KEY`        | OpenAI API key                     |
| `GOOGLE_API_KEY`        | Google AI API key                  |
| `EXA_API_KEY`           | Exa search API key                 |
| `ALPHA_VANTAGE_API_KEY` | Market data API key                |

## Architecture

See [Architecture Documentation](docs/plans/2026-02-02-boardroom-design.md) for technical details.
