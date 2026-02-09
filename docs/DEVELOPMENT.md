# Development Guide

This document describes how to set up and work with the **Boardroom** development environment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Running Locally](#running-locally)
4. [Database Migrations](#database-migrations)
5. [Frontend Development](#frontend-development)
6. [Backend Development](#backend-development)

## Prerequisites

- **Python**: 3.9+
- **Node.js**: 16+
- **PostgreSQL**: Local or Dockerized instance
- **Virtual Environment** (recommended): `venv` or `conda`

## Installation

### 1. Clone Dependencies

```bash
git clone https://github.com/your-username/boardroom.git
cd boardroom
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Note**: Key dependencies include:

- `fastapi`, `uvicorn`: Web server
- `sqlalchemy`, `alembic`: Database and migrations
- `python-jose[cryptography]`: JWT authentication
- `passlib[bcrypt]`: Password hashing

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

**Note**: Key dependencies include:

- `react`, `react-dom`, `react-router-dom`: Core framework
- `lucide-react`: Icons
- `tailwindcss`: Styling

## Configuration

Create a `.env` file in the `backend/` directory:

```ini
# Database
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/boardroom_db

# Security
JWT_SECRET=your_super_secret_key_change_me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Keys (if applicable)
OPENAI_API_KEY=sk-...
```

## Running Locally

### Start Backend

```bash
# From root directory
source backend/venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`.
API Docs: `http://localhost:8000/docs`.

### Start Frontend

```bash
# From frontend directory
npm run dev
```

Frontend will be available at `http://localhost:5173` (or similar).

## Database Migrations

We use **Alembic** for migrations.

```bash
# Create a new migration (after modifying models.py)
alembic revision --autogenerate -m "Description of change"

# Apply migrations
alembic upgrade head
```

## Frontend Development

The frontend is built with **React** and **TypeScript**.

- **Components**: Located in `src/components/`. Use functional components with hooks.
- **Pages**: Top-level views in `src/pages/`.
- **Routing**: Defined in `App.tsx` using `react-router-dom`.
- **State**: `AuthContext` provides user session globally.

### Adding a New Page & Route

1. Create `src/pages/NewPage.tsx`.
2. Import `NewPage` in `src/App.tsx`.
3. Add `<Route path="/new-path" element={<NewPage />} />`.
4. (Optional) Protect it with `<ProtectedRoute>`.

## Backend Development

The backend is built with **FastAPI**.

### Adding a New Endpoint

1. **Model**: Add table definition in `backend/dao/models.py`.
2. **DTO**: Add Pydantic schemas in `backend/api/schemas.py` (optional/inline).
3. **Route**: Add endpoint function in `backend/api/routes.py`.
4. **Register**: Ensure router is included in `backend/main.py`.

### Authentication

- Use `Depends(get_current_user)` to protect endpoints.
- Access token is provided in `Authorization: Bearer <token>` header.

1. Check the configuration in `pyproject.toml`
2. You can add specific ignores in the tool configuration
3. For mypy, you can use `# type: ignore` comments for specific lines

### ESLint or Prettier errors

If you see errors from ESLint or Prettier:

1. Run `just lint-fix` to auto-fix issues
2. Check `.eslintrc.json` and `.prettierrc.json` for configuration

## Development Workflow

The development pipeline follows these stages:

1. **Read Task/Story** - Understand requirements from Linear
2. **Plan Sub-tasks** - Break down into implementable pieces
3. **Create Branch** - Create feature branch from main
4. **Implement** - Each sub-task owned by dedicated role
5. **Write Tests** - Ensure code quality
6. **Code Review** - Review using appropriate roles
7. **Fix Issues** - Address review feedback
8. **Commit & Push** - Commit with proper conventions
9. **Create PR** - Open pull request for review

For detailed workflow information, see [Linear Integration Guide](LINEAR.md).

## Related Documentation

- [Linear Integration](LINEAR.md) - Linear workflow and automation
- [Architecture Guide](ARCHITECTURE.md) - System architecture overview
- [Deployment Guide](DEPLOYMENT.md) - Deployment procedures
