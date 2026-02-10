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
