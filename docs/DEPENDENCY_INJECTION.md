# Dependency Injection in Boardroom

This document describes how the Boardroom API uses dependency injection (DI) to wire services into endpoints.

## Overview

FastAPI's `Depends()` system provides a clean, declarative way to inject dependencies into endpoints. Boardroom uses this pattern to:

1. **Create services with proper DAO injection** - Services get DAOs in constructor
2. **Inject fresh database sessions** - Each request gets a new AsyncSession
3. **Separate concerns** - Endpoints focus on HTTP, services focus on business logic
4. **Enable testing** - Services can be mocked easily

## The Pattern

### 1. Service Factory Functions

Located in `backend/services/dependencies.py`, these functions create service instances:

```python
async def get_auth_service(db: AsyncSession) -> AuthService:
    """Factory function to create AuthService with dependency injection."""
    return AuthService(UserDAO(db), WatchlistDAO(db), PortfolioDAO(db))

async def get_portfolio_service(db: AsyncSession) -> PortfolioService:
    """Factory function to create PortfolioService with dependency injection."""
    return PortfolioService(PortfolioDAO(db))

async def get_watchlist_service(db: AsyncSession) -> WatchlistService:
    """Factory function to create WatchlistService with dependency injection."""
    return WatchlistService(WatchlistDAO(db))
```

### 2. Endpoint Injection

Endpoints use `Depends()` to inject both services and database sessions:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.portfolio_management.service import PortfolioService
from backend.services.dependencies import get_portfolio_service
from backend.db.database import get_db

router = APIRouter()

@router.post("/portfolios")
async def create_portfolio(
    name: str,
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
    db: AsyncSession = Depends(get_db),
) -> PortfolioSchema:
    """Create a new portfolio."""
    portfolio = await service.create_portfolio(current_user.id, name, db)
    return PortfolioSchema(id=str(portfolio.id), name=portfolio.name, positions=[])
```

## Request Flow

For a single `POST /portfolios` request:

```
1. FastAPI receives request
2. Resolves dependencies in order:
   a. get_current_user(token) → User
   b. get_db() → AsyncSession (fresh)
   c. get_portfolio_service(db) → PortfolioService
      - Inside: PortfolioDAO(db)
3. Calls endpoint with all dependencies
4. Endpoint calls service method with db
5. Service calls DAO methods
6. DAOs execute SQL with the session
7. Endpoint returns response
```

## Database Session Lifecycle

### Per-Request Sessions

Each endpoint gets a fresh database session:

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get a fresh database session for each request."""
    async with AsyncSession(engine) as session:
        try:
            yield session  # Request uses this session
        finally:
            await session.close()  # Automatically closed after request
```

### Why Fresh Sessions?

1. **Isolation** - Each request is independent
2. **Clean state** - No cross-request pollution
3. **Error recovery** - Failed request doesn't affect others
4. **Connection pooling** - Sessions returned to pool after use

## Dependency Resolution Order

FastAPI resolves dependencies from top to bottom:

```python
async def create_portfolio(
    name: str,  # Query parameter (no dependency)
    current_user: User = Depends(get_current_user),  # 1. Resolve first
    service: PortfolioService = Depends(get_portfolio_service),  # 2. Then this
    db: AsyncSession = Depends(get_db),  # 3. Finally this
):
    pass
```

**Important:** If `get_portfolio_service` depends on `db`, FastAPI resolves `get_db` first automatically.

## Nested Dependencies

Services that need multiple DAOs use nested dependencies:

```python
# In dependencies.py
async def get_auth_service(db: AsyncSession) -> AuthService:
    # AuthService needs 3 DAOs, all created from single db session
    return AuthService(
        UserDAO(db),
        WatchlistDAO(db),
        PortfolioDAO(db),
    )

# In endpoint
async def register(
    user_data: UserCreate,
    service: AuthService = Depends(get_auth_service),  # Gets all 3 DAOs
    db: AsyncSession = Depends(get_db),  # Same session
):
    pass
```

## Error Handling in Injection

### Validation Errors

If injection fails (missing dependency), FastAPI returns 422:

```json
{
  "detail": [
    {
      "loc": ["header", "authorization"],
      "msg": "Field required",
      "type": "missing"
    }
  ]
}
```

### Exception Handling

Services raise domain-specific exceptions that endpoints handle:

```python
@router.post("/schedules")
async def create_schedule(
    schedule_data: ScheduleCreate,
    service: ScheduleService = Depends(get_schedule_service),
    db: AsyncSession = Depends(get_db),
):
    try:
        schedule = await service.create_scheduled_analysis(
            user_id=current_user.id,
            ticker=schedule_data.ticker,
            market=schedule_data.market,
            frequency=schedule_data.frequency,
            db=db,
        )
        return schedule
    except ScheduleRateLimitError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ScheduleError as e:
        logger.error(f"Failed to create schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create schedule")
```

## Dependency Injection Guidelines

### ✅ DO

1. **Inject services not DAOs**
   ```python
   # CORRECT
   service: PortfolioService = Depends(get_portfolio_service)
   ```

2. **Inject database for write operations**
   ```python
   # CORRECT
   db: AsyncSession = Depends(get_db)
   ```

3. **Create factory functions for complex services**
   ```python
   # CORRECT
   async def get_auth_service(db: AsyncSession) -> AuthService:
       return AuthService(UserDAO(db), WatchlistDAO(db), PortfolioDAO(db))
   ```

4. **Handle service exceptions in endpoints**
   ```python
   # CORRECT
   try:
       result = await service.create_alert(...)
   except AlertValidationError as e:
       raise HTTPException(status_code=400, detail=str(e))
   ```

### ❌ DON'T

1. **Don't inject DAOs directly**
   ```python
   # WRONG
   dao: PortfolioDAO = Depends(get_portfolio_dao)
   ```

2. **Don't create services manually in endpoints**
   ```python
   # WRONG
   service = PortfolioService(PortfolioDAO(db))  # Each request creates new instance
   ```

3. **Don't bypass services to use DAOs**
   ```python
   # WRONG
   portfolio = await portfolio_dao.create(...)  # No business logic
   ```

4. **Don't use DAO sessions directly**
   ```python
   # WRONG
   await service.portfolio_dao.session.commit()  # Access implementation detail
   ```

## Testing with Dependency Injection

### Mocking Services in Tests

```python
from unittest.mock import AsyncMock
import pytest

@pytest.fixture
def mock_portfolio_service():
    service = AsyncMock(spec=PortfolioService)
    service.create_portfolio.return_value = Portfolio(id="...", name="Test")
    return service

async def test_create_portfolio(client, mock_portfolio_service):
    # Override the dependency
    app.dependency_overrides[get_portfolio_service] = lambda: mock_portfolio_service

    response = await client.post("/portfolios", json={"name": "Test"})

    assert response.status_code == 200
    assert response.json()["name"] == "Test"
    mock_portfolio_service.create_portfolio.assert_called_once()

    # Clean up
    app.dependency_overrides.clear()
```

### Dependency Overrides

FastAPI provides `app.dependency_overrides` for testing:

```python
# In test setup
from backend.services.dependencies import get_portfolio_service

@pytest.fixture
def override_dependencies():
    """Override dependencies for testing."""
    mock_service = AsyncMock(spec=PortfolioService)
    mock_service.create_portfolio.return_value = Portfolio(id="...", name="Test")
    app.dependency_overrides[get_portfolio_service] = lambda: mock_service
    yield mock_service
    app.dependency_overrides.clear()
```

## FastAPI Lifecycle

### Request Processing

```
1. Request arrives
2. FastAPI extracts path, query, body parameters
3. Dependency graph is constructed
4. Dependencies are resolved in topological order
5. Endpoint is called with resolved parameters
6. Endpoint returns response
7. Response is serialized and sent
8. Session cleanup happens (via finally block)
```

### Dependency Caching

Within a single request, FastAPI caches dependency results:

```python
@router.get("/test")
async def test_endpoint(
    db1: AsyncSession = Depends(get_db),
    service1: PortfolioService = Depends(get_portfolio_service),
    service2: PortfolioService = Depends(get_portfolio_service),
):
    # db1 is the same session
    # service1 and service2 use the SAME db1 instance
    # This is correct - all DAOs in both services share the session
    pass
```

This caching ensures consistency within a request.

## Common Patterns

### Pattern 1: Simple CRUD

```python
@router.post("/items")
async def create_item(
    data: ItemCreate,
    service: ItemService = Depends(get_item_service),
    db: AsyncSession = Depends(get_db),
):
    item = await service.create_item(data, db)
    return item
```

### Pattern 2: Nested Services

```python
# For services that orchestrate other services
async def get_orchestration_service(
    auth_service: AuthService = Depends(get_auth_service),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> OrchestrationService:
    return OrchestrationService(auth_service, portfolio_service)
```

### Pattern 3: Conditional Injection

```python
# Based on configuration
def get_llm_service() -> LLMService:
    provider = settings.llm_provider
    if provider == "anthropic":
        return AnthropicLLMService()
    elif provider == "openai":
        return OpenAILLMService()
    else:
        raise ValueError(f"Unknown provider: {provider}")

@router.post("/analyze")
async def analyze(
    data: AnalysisRequest,
    llm: LLMService = Depends(get_llm_service),
):
    result = await llm.analyze(data)
    return result
```

## Performance Considerations

### Dependency Resolution Cost

Creating instances has minimal overhead:

```python
# Each request:
1. AsyncSession created from pool (~0.1ms)
2. Service instantiated with DAOs (~0.01ms)
3. Business logic executes (~10-1000ms)
```

The 0.1ms overhead is negligible compared to business logic.

### Connection Pooling

AsyncSession uses connection pooling:

```python
# engine configuration
engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,  # For serverless
    # OR
    # pool_size=10,  # For long-running services
    # max_overflow=20,
)
```

## See Also

- [SERVICES.md](./SERVICES.md) - Services layer documentation
- [docs/ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
