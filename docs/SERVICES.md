# Services Layer Architecture

The Services Layer provides the business logic layer between API endpoints and data access objects (DAOs). This document describes the service architecture, patterns, and usage.

## Overview

The services layer encapsulates all business logic, validation, and orchestration of database operations. Each service is a class that:

1. **Accepts DAOs through constructor injection** - Services don't create DAOs themselves
2. **Exposes async methods** for business operations
3. **Inherits from BaseService** - A common abstract base class
4. **Raises domain-specific exceptions** - For error handling in endpoints

## Architecture

```
API Endpoints
    ↓
Services (Business Logic)
    ↓
DAOs (Data Access)
    ↓
Database
```

## Core Services

### AuthService

**Location:** `backend/services/auth/service.py`

**Responsibilities:**
- User registration with validation and default assets
- User login with password verification
- JWT token creation
- User authentication for protected routes

**Methods:**
```python
async def register_user(
    self,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    db: AsyncSession,
) -> tuple[User, str]:
    """Register new user and return (user, access_token)"""

async def login_user(
    self, email: str, password: str, db: AsyncSession
) -> tuple[User, str]:
    """Authenticate user and return (user, access_token)"""

async def authenticate_user(self, email: str) -> Optional[User]:
    """Get user by email (for JWT validation)"""
```

**Example Usage:**
```python
@router.post("/register")
async def register(
    user_data: UserCreate,
    service: AuthService = Depends(get_auth_service),
    db: AsyncSession = Depends(get_db),
):
    user, token = await service.register_user(
        user_data.email,
        user_data.password,
        user_data.first_name,
        user_data.last_name,
        db,
    )
    return Token(access_token=token, token_type="bearer")
```

### PortfolioService

**Location:** `backend/services/portfolio_management/service.py`

**Responsibilities:**
- Portfolio CRUD operations
- Position management (add/update/delete)
- Delegation to WatchlistService for watchlist operations

**Methods:**
```python
async def get_user_portfolios(self, user_id: UUID) -> List[Portfolio]:
    """Get all portfolios for a user"""

async def create_portfolio(
    self, user_id: UUID, name: str, db: AsyncSession
) -> Portfolio:
    """Create new portfolio and default positions"""

async def add_position(
    self,
    portfolio_id: UUID,
    ticker: str,
    market: Market,
    quantity: float,
    avg_entry_price: float,
    sector: str | None,
    db: AsyncSession,
) -> Position:
    """Add position to portfolio"""
```

### WatchlistService

**Location:** `backend/services/watchlist/service.py`

**Responsibilities:**
- Watchlist CRUD operations
- Watchlist item management
- Default watchlist retrieval

**Methods:**
```python
async def get_user_watchlists(self, user_id: UUID) -> List[Watchlist]:
    """Get all watchlists for user"""

async def create_watchlist(
    self, user_id: UUID, name: str, db: AsyncSession
) -> Watchlist:
    """Create new watchlist"""

async def add_to_watchlist(
    self,
    watchlist_id: UUID,
    ticker: str,
    market: Market,
    db: AsyncSession,
) -> WatchlistItem:
    """Add stock to watchlist"""

async def remove_from_watchlist(
    self, watchlist_id: UUID, ticker: str, db: AsyncSession
) -> bool:
    """Remove stock from watchlist"""

async def get_default_watchlist(
    self, user_id: UUID
) -> Optional[Watchlist]:
    """Get user's default watchlist"""
```

### ScheduleService

**Location:** `backend/services/schedules/service.py`

**Responsibilities:**
- Scheduled analysis CRUD
- Rate limiting (max 50 schedules per user)
- Schedule frequency management
- Run time calculation

**Methods:**
```python
async def create_scheduled_analysis(
    self,
    user_id: UUID,
    ticker: str,
    market: Market,
    frequency: str,
    db: AsyncSession,
) -> ScheduledAnalysis:
    """Create scheduled analysis (includes rate limiting)"""

async def get_user_schedules(self, user_id: UUID) -> List[ScheduledAnalysis]:
    """Get all user's schedules"""

async def get_due_schedules(self) -> List[ScheduledAnalysis]:
    """Get schedules ready to run"""

async def update_run_times(
    self,
    schedule_id: UUID,
    last_run: datetime,
    next_run: datetime,
    db: AsyncSession,
) -> ScheduledAnalysis:
    """Update schedule run times"""

async def toggle_schedule(
    self, schedule_id: UUID, active: bool, db: AsyncSession
) -> ScheduledAnalysis:
    """Pause/resume schedule"""

async def delete_schedule(self, schedule_id: UUID, db: AsyncSession) -> bool:
    """Delete schedule"""
```

### AnalysisService

**Location:** `backend/services/analysis/service.py`

**Responsibilities:**
- Analysis session management
- Agent report storage
- Final decision tracking
- Analysis history retrieval

**Methods:**
```python
async def create_analysis_session(
    self, ticker: str, market: Market, user_id: Optional[UUID], db: AsyncSession
) -> AnalysisSession:
    """Create new analysis session"""

async def save_agent_report(
    self,
    session_id: UUID,
    agent_type: AgentType,
    report_data: dict,
    db: AsyncSession,
) -> AgentReport:
    """Save agent's analysis report"""

async def save_final_decision(
    self,
    session_id: UUID,
    action: Action,
    confidence: float,
    rationale: str,
    vetoed: bool,
    veto_reason: Optional[str],
    db: AsyncSession,
) -> FinalDecision:
    """Save final trading decision"""

async def get_user_analysis_history(
    self, user_id: UUID, limit: int
) -> List[AnalysisSession]:
    """Get user's analysis history"""
```

### AlertService

**Location:** `backend/services/alerts/service.py`

**Responsibilities:**
- Price alert management
- Alert condition validation
- Notification triggering

**Methods:**
```python
async def create_price_alert(
    self,
    db: AsyncSession,
    user_id: UUID,
    ticker: str,
    market: Market,
    condition: AlertCondition,
    target_value: float,
) -> PriceAlert:
    """Create price alert with validation"""

async def delete_alert(self, alert_id: UUID, db: AsyncSession) -> bool:
    """Delete alert"""

async def toggle_alert(
    self, alert_id: UUID, active: bool, db: AsyncSession
) -> PriceAlert:
    """Pause/resume alert"""
```

### PerformanceService

**Location:** `backend/services/performance_tracking/service.py`

**Responsibilities:**
- Analysis outcome tracking
- Performance summary calculation
- Recent outcomes retrieval

**Methods:**
```python
async def create_analysis_outcome(
    self, db: AsyncSession, session_id: UUID
) -> Optional[AnalysisOutcome]:
    """Create outcome record with current price snapshot"""

async def get_performance_summary(
    self, db: AsyncSession
) -> dict:
    """Get overall performance metrics"""

async def get_recent_outcomes(
    self,
    db: AsyncSession,
    limit: int = 20,
    ticker: Optional[str] = None,
) -> list:
    """Get recent outcomes with returns"""
```

### SettingsService

**Location:** `backend/services/settings/service.py`

**Responsibilities:**
- User profile management
- Password change with validation
- LLM provider preferences

**Methods:**
```python
async def update_profile(
    self,
    user_id: UUID,
    db: AsyncSession,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
) -> dict:
    """Update user profile with validation"""

async def change_password(
    self,
    user_id: UUID,
    current_password: str,
    new_password: str,
    db: AsyncSession,
) -> bool:
    """Change password with verification"""
```

## Exception Hierarchy

Services define domain-specific exceptions inheriting from `ServiceError`:

```python
# Base exception
class ServiceError(Exception):
    """Base for all service exceptions"""

# Auth exceptions
class AuthError(ServiceError):
    """Base auth error"""

class UserAlreadyExistsError(AuthError):
    """User already registered"""

class InvalidCredentialsError(AuthError):
    """Login failed"""

# Schedule exceptions
class ScheduleError(ServiceError):
    """Base schedule error"""

class ScheduleRateLimitError(ScheduleError):
    """User exceeded max 50 schedules"""

class ScheduleNotFoundError(ScheduleError):
    """Schedule not found"""

# Alert exceptions
class AlertError(ServiceError):
    """Base alert error"""

class AlertValidationError(AlertError):
    """Invalid alert parameters"""

# Other domain exceptions
class WatchlistError(ServiceError):
class AnalysisError(ServiceError):
class SettingsError(ServiceError):
class PerformanceError(ServiceError):
```

## Backward Compatibility

All services maintain backward-compatible module-level functions for gradual migration:

```python
# Deprecated: Use AuthService directly
async def register_user(email, password, first_name, last_name, db):
    service = AuthService(UserDAO(db), WatchlistDAO(db), PortfolioDAO(db))
    return await service.register_user(email, password, first_name, last_name, db)
```

These functions are marked as deprecated in docstrings and will be removed in a future version.

## Database Session Management

### Pattern

Services require an `AsyncSession` parameter for methods that perform writes:

```python
async def create_portfolio(
    self, user_id: UUID, name: str, db: AsyncSession
) -> Portfolio:
    portfolio = await self.portfolio_dao.create(user_id=user_id, name=name)
    await db.commit()
    await db.refresh(portfolio)
    return portfolio
```

### Why This Pattern?

1. **Transaction control** - Caller (endpoint) decides when to commit
2. **Consistency** - Related operations can be grouped in single transaction
3. **Testing** - Easy to mock transactions in tests
4. **Testability** - Services don't manage their own sessions

## Best Practices

### 1. Use Dependency Injection in Endpoints

```python
@router.post("/portfolios")
async def create_portfolio(
    name: str,
    service: PortfolioService = Depends(get_portfolio_service),
    db: AsyncSession = Depends(get_db),
):
    return await service.create_portfolio(current_user.id, name, db)
```

### 2. Handle Service Exceptions in Endpoints

```python
try:
    result = await service.create_scheduled_analysis(...)
except ScheduleRateLimitError as e:
    raise HTTPException(status_code=400, detail=str(e))
except ScheduleError as e:
    raise HTTPException(status_code=500, detail="Failed to create schedule")
```

### 3. Keep Business Logic in Services

❌ Don't do validation in endpoints:
```python
# WRONG
@router.post("/alerts")
async def create_alert(data: AlertCreate, db: AsyncSession):
    if data.target_value <= 0:  # Validation in endpoint
        raise HTTPException(status_code=400, detail="Invalid value")
    return await alert_dao.create(...)
```

✅ Do validation in services:
```python
# CORRECT
class AlertService(BaseService):
    async def create_price_alert(self, ..., db: AsyncSession):
        if target_value <= 0:
            raise AlertValidationError("Target value must be positive")
        return await self.alert_dao.create(...)
```

### 4. Document Exception Cases

```python
async def create_price_alert(self, ...) -> PriceAlert:
    """
    Create a price alert.

    Raises:
        AlertValidationError: If target_value is invalid
        AlertError: If creation fails
    """
```

## Testing Services

Services are tested with mocked DAOs:

```python
@pytest.fixture
def mock_portfolio_dao():
    return AsyncMock(spec=PortfolioDAO)

async def test_create_portfolio(mock_portfolio_dao):
    service = PortfolioService(mock_portfolio_dao)
    mock_portfolio_dao.create.return_value = Portfolio(id=..., name="Test")

    result = await service.create_portfolio(user_id, "Test", mock_db)

    assert result.name == "Test"
    mock_portfolio_dao.create.assert_called_once()
```

## Migration Path

Phase 4 completes the refactoring by wiring services into all API endpoints. Future work:

1. **Phase 5** - Add comprehensive test coverage (skip for now)
2. **Phase 6** - Complete (this documentation)
3. **Future** - Optimize DAOs, add caching layer, implement read replicas

## Service Dependency Graph

```
AuthService
  ├── UserDAO
  ├── WatchlistDAO
  └── PortfolioDAO

PortfolioService
  └── PortfolioDAO

WatchlistService
  └── WatchlistDAO

ScheduleService
  └── ScheduledAnalysisDAO

AnalysisService
  └── AnalysisDAO

AlertService
  ├── PriceAlertDAO
  └── NotificationDAO

PerformanceService
  └── PerformanceDAO

SettingsService
  └── UserDAO

EmailService
  └── (no dependencies)
```

## See Also

- [DEPENDENCY_INJECTION.md](./DEPENDENCY_INJECTION.md) - Dependency injection patterns
- [docs/ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture overview
- [CLAUDE.md](../CLAUDE.md#best-practices) - Development best practices
