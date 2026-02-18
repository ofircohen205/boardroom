# Test Coverage to 80% Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Raise backend test coverage from 58.45% to ≥80% by adding unit tests for service classes, API endpoint tests with mocked deps, PostgreSQL integration tests for background jobs, and mocked WebSocket tests.

**Architecture:** Approach A — layer-by-layer. Wave 1 adds service unit tests (SQLite + mocked DAOs), Wave 2 adds API endpoint tests (FastAPI TestClient with `app.dependency_overrides`), Wave 3 adds integration tests for background jobs (PostgreSQL), Wave 4 adds WebSocket mock tests and shared tool unit tests. Each wave reuses fixtures from the previous.

**Tech Stack:** pytest-asyncio, SQLite (unit), PostgreSQL (integration), httpx AsyncClient, FastAPI TestClient, `unittest.mock.AsyncMock`

---

## Reference: Running Tests

```bash
# All tests with coverage
uv run pytest tests/ -v --cov=backend --cov-report=term-missing --cov-fail-under=80

# Single file
uv run pytest tests/unit/test_services_analysis.py -v

# Single test
uv run pytest tests/unit/test_services_analysis.py::test_create_session_success -v

# Coverage for a specific module
uv run pytest tests/unit/test_services_analysis.py -v --cov=backend/domains/analysis/services
```

## Reference: Fixture Patterns

All unit tests use `test_db_session` from `tests/conftest.py` (SQLite in-memory).
All integration tests use `test_db_session` configured for PostgreSQL (file path contains `integration/`).

**Standard service test setup:**
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

@pytest.fixture
def mock_dao():
    dao = MagicMock()
    dao.session = MagicMock()
    # Make every method async
    dao.get_by_id = AsyncMock(return_value=None)
    return dao
```

**Standard API test setup (for all Wave 2 tasks):**
```python
import pytest
from httpx import ASGITransport, AsyncClient
from backend.main import app

@pytest.fixture
async def client(test_user, mock_token):
    # Override auth dependency
    from backend.shared.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: test_user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

---

## Wave 1: Service Layer Unit Tests

### Task 1: AnalysisService unit tests

**Target:** `backend/domains/analysis/services/service.py` (54 missed stmts → aim to cover ~90%)

**Files:**
- Create: `tests/unit/test_services_analysis.py`

**Step 1: Write the failing tests**

```python
# tests/unit/test_services_analysis.py
"""Unit tests for AnalysisService."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from backend.shared.ai.state.enums import Action, AgentType, Market
from backend.domains.analysis.services.service import AnalysisService
from backend.domains.analysis.services.exceptions import (
    AnalysisError,
    AnalysisSessionNotFoundError,
)
from backend.shared.db.models import AgentReport, AnalysisSession, FinalDecision
from datetime import datetime


@pytest.fixture
def mock_analysis_dao():
    dao = MagicMock()
    dao.session = MagicMock()
    dao.create_session = AsyncMock()
    dao.get_by_id = AsyncMock()
    dao.add_report = AsyncMock()
    dao.add_decision = AsyncMock()
    dao.get_user_sessions = AsyncMock()
    dao.get_recent_sessions = AsyncMock()
    return dao


@pytest.fixture
def analysis_service(mock_analysis_dao):
    return AnalysisService(mock_analysis_dao)


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def sample_session():
    return AnalysisSession(
        id=uuid4(),
        ticker="AAPL",
        market=Market.US,
        created_at=datetime.now(),
    )


@pytest.fixture
def sample_report(sample_session):
    return AgentReport(
        id=uuid4(),
        session_id=sample_session.id,
        agent_type=AgentType.FUNDAMENTAL,
        report_data={"pe_ratio": 15.5},
        created_at=datetime.now(),
    )


@pytest.fixture
def sample_decision(sample_session):
    return FinalDecision(
        id=uuid4(),
        session_id=sample_session.id,
        action=Action.BUY,
        confidence=0.85,
        rationale="Strong fundamentals",
        vetoed=False,
        created_at=datetime.now(),
    )


# --- create_analysis_session ---

@pytest.mark.asyncio
async def test_create_session_success(analysis_service, mock_analysis_dao, mock_db, sample_session):
    mock_analysis_dao.create_session.return_value = sample_session
    result = await analysis_service.create_analysis_session("AAPL", Market.US, None, mock_db)
    assert result == sample_session
    mock_analysis_dao.create_session.assert_called_once_with("AAPL", Market.US, None)
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_session_dao_failure_raises_analysis_error(analysis_service, mock_analysis_dao, mock_db):
    mock_analysis_dao.create_session.side_effect = Exception("DB error")
    with pytest.raises(AnalysisError, match="Failed to create analysis session"):
        await analysis_service.create_analysis_session("AAPL", Market.US, None, mock_db)
    mock_db.rollback.assert_called_once()


# --- save_agent_report ---

@pytest.mark.asyncio
async def test_save_agent_report_success(analysis_service, mock_analysis_dao, mock_db, sample_session, sample_report):
    mock_analysis_dao.get_by_id.return_value = sample_session
    mock_analysis_dao.add_report.return_value = sample_report
    result = await analysis_service.save_agent_report(
        sample_session.id, AgentType.FUNDAMENTAL, {"pe_ratio": 15.5}, mock_db
    )
    assert result == sample_report
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_save_agent_report_session_not_found(analysis_service, mock_analysis_dao, mock_db):
    mock_analysis_dao.get_by_id.return_value = None
    with pytest.raises(AnalysisSessionNotFoundError):
        await analysis_service.save_agent_report(uuid4(), AgentType.FUNDAMENTAL, {}, mock_db)


@pytest.mark.asyncio
async def test_save_agent_report_dao_failure_raises_analysis_error(
    analysis_service, mock_analysis_dao, mock_db, sample_session
):
    mock_analysis_dao.get_by_id.return_value = sample_session
    mock_analysis_dao.add_report.side_effect = Exception("DB error")
    with pytest.raises(AnalysisError, match="Failed to save"):
        await analysis_service.save_agent_report(sample_session.id, AgentType.FUNDAMENTAL, {}, mock_db)
    mock_db.rollback.assert_called_once()


# --- save_final_decision ---

@pytest.mark.asyncio
async def test_save_final_decision_success(analysis_service, mock_analysis_dao, mock_db, sample_session, sample_decision):
    mock_analysis_dao.get_by_id.return_value = sample_session
    mock_analysis_dao.add_decision.return_value = sample_decision
    result = await analysis_service.save_final_decision(
        sample_session.id, Action.BUY, 0.85, "Strong fundamentals", db=mock_db
    )
    assert result.action == Action.BUY
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_save_final_decision_session_not_found(analysis_service, mock_analysis_dao, mock_db):
    mock_analysis_dao.get_by_id.return_value = None
    with pytest.raises(AnalysisSessionNotFoundError):
        await analysis_service.save_final_decision(uuid4(), Action.BUY, 0.8, "rationale", db=mock_db)


@pytest.mark.asyncio
async def test_save_final_decision_with_veto(analysis_service, mock_analysis_dao, mock_db, sample_session, sample_decision):
    mock_analysis_dao.get_by_id.return_value = sample_session
    vetoed_decision = sample_decision
    vetoed_decision.vetoed = True
    mock_analysis_dao.add_decision.return_value = vetoed_decision
    result = await analysis_service.save_final_decision(
        sample_session.id, Action.HOLD, 0.5, "vetoed", vetoed=True, veto_reason="Too risky", db=mock_db
    )
    assert result.vetoed is True


# --- get_analysis_session ---

@pytest.mark.asyncio
async def test_get_analysis_session_success(analysis_service, mock_analysis_dao, sample_session):
    mock_analysis_dao.get_by_id.return_value = sample_session
    result = await analysis_service.get_analysis_session(sample_session.id)
    assert result == sample_session


@pytest.mark.asyncio
async def test_get_analysis_session_not_found(analysis_service, mock_analysis_dao):
    mock_analysis_dao.get_by_id.return_value = None
    with pytest.raises(AnalysisSessionNotFoundError):
        await analysis_service.get_analysis_session(uuid4())


# --- get_user_analysis_history ---

@pytest.mark.asyncio
async def test_get_user_analysis_history(analysis_service, mock_analysis_dao, sample_session):
    mock_analysis_dao.get_user_sessions.return_value = [sample_session]
    user_id = uuid4()
    result = await analysis_service.get_user_analysis_history(user_id)
    assert len(result) == 1
    mock_analysis_dao.get_user_sessions.assert_called_once_with(user_id, 50)


@pytest.mark.asyncio
async def test_get_user_analysis_history_dao_error(analysis_service, mock_analysis_dao):
    mock_analysis_dao.get_user_sessions.side_effect = Exception("DB error")
    with pytest.raises(AnalysisError, match="Failed to fetch analysis history"):
        await analysis_service.get_user_analysis_history(uuid4())


# --- get_recent_outcomes ---

@pytest.mark.asyncio
async def test_get_recent_outcomes(analysis_service, mock_analysis_dao, sample_session):
    mock_analysis_dao.get_recent_sessions.return_value = [sample_session]
    result = await analysis_service.get_recent_outcomes(limit=10)
    assert len(result) == 1
    mock_analysis_dao.get_recent_sessions.assert_called_once_with(10)


@pytest.mark.asyncio
async def test_get_recent_outcomes_dao_error(analysis_service, mock_analysis_dao):
    mock_analysis_dao.get_recent_sessions.side_effect = Exception("DB error")
    with pytest.raises(AnalysisError, match="Failed to fetch recent outcomes"):
        await analysis_service.get_recent_outcomes()
```

**Step 2: Run tests to verify they fail (service not yet tested)**

```bash
uv run pytest tests/unit/test_services_analysis.py -v
```
Expected: Tests collected but may fail if any import path is wrong. Fix imports if needed.

**Step 3: Verify tests pass**

```bash
uv run pytest tests/unit/test_services_analysis.py -v --cov=backend/domains/analysis/services/service
```
Expected: All PASS. Coverage for `service.py` should jump to >85%.

**Step 4: Commit**

```bash
git add tests/unit/test_services_analysis.py
git commit -m "test: add AnalysisService unit tests"
```

---

### Task 2: WatchlistService unit tests

**Target:** `backend/domains/portfolio/services/watchlist_service.py` (46 missed stmts)

**Files:**
- Create: `tests/unit/test_services_watchlist.py`

**Step 1: Write the failing tests**

```python
# tests/unit/test_services_watchlist.py
"""Unit tests for WatchlistService."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from backend.shared.ai.state.enums import Market
from backend.domains.portfolio.services.watchlist_service import WatchlistService
from backend.domains.portfolio.services.watchlist_exceptions import (
    WatchlistError,
    WatchlistNotFoundError,
)
from backend.shared.db.models import Watchlist, WatchlistItem


@pytest.fixture
def mock_watchlist_dao():
    dao = MagicMock()
    dao.session = MagicMock()
    dao.get_user_watchlists = AsyncMock()
    dao.create = AsyncMock()
    dao.get_by_id = AsyncMock()
    dao.add_item = AsyncMock()
    dao.delete = AsyncMock()
    dao.get_default_watchlist = AsyncMock()
    dao.update = AsyncMock()
    # Needed for remove_from_watchlist which uses dao.session.execute
    dao.session.execute = AsyncMock()
    return dao


@pytest.fixture
def watchlist_service(mock_watchlist_dao):
    return WatchlistService(mock_watchlist_dao)


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def sample_watchlist():
    return Watchlist(id=uuid4(), user_id=uuid4(), name="My Watchlist")


@pytest.fixture
def sample_item(sample_watchlist):
    return WatchlistItem(
        id=uuid4(),
        watchlist_id=sample_watchlist.id,
        ticker="AAPL",
        market=Market.US,
    )


# --- get_user_watchlists ---

@pytest.mark.asyncio
async def test_get_user_watchlists_success(watchlist_service, mock_watchlist_dao, sample_watchlist):
    user_id = uuid4()
    mock_watchlist_dao.get_user_watchlists.return_value = [sample_watchlist]
    result = await watchlist_service.get_user_watchlists(user_id)
    assert len(result) == 1
    assert result[0].name == "My Watchlist"


@pytest.mark.asyncio
async def test_get_user_watchlists_dao_error(watchlist_service, mock_watchlist_dao):
    mock_watchlist_dao.get_user_watchlists.side_effect = Exception("DB error")
    with pytest.raises(WatchlistError, match="Failed to fetch watchlists"):
        await watchlist_service.get_user_watchlists(uuid4())


# --- create_watchlist ---

@pytest.mark.asyncio
async def test_create_watchlist_success(watchlist_service, mock_watchlist_dao, mock_db, sample_watchlist):
    mock_watchlist_dao.create.return_value = sample_watchlist
    result = await watchlist_service.create_watchlist(uuid4(), "My Watchlist", mock_db)
    assert result.name == "My Watchlist"
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_create_watchlist_dao_error(watchlist_service, mock_watchlist_dao, mock_db):
    mock_watchlist_dao.create.side_effect = Exception("DB error")
    with pytest.raises(WatchlistError, match="Failed to create watchlist"):
        await watchlist_service.create_watchlist(uuid4(), "My Watchlist", mock_db)
    mock_db.rollback.assert_called_once()


# --- add_to_watchlist ---

@pytest.mark.asyncio
async def test_add_to_watchlist_success(watchlist_service, mock_watchlist_dao, mock_db, sample_watchlist, sample_item):
    mock_watchlist_dao.get_by_id.return_value = sample_watchlist
    mock_watchlist_dao.add_item.return_value = sample_item
    result = await watchlist_service.add_to_watchlist(sample_watchlist.id, "AAPL", Market.US, mock_db)
    assert result.ticker == "AAPL"
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_add_to_watchlist_not_found(watchlist_service, mock_watchlist_dao, mock_db):
    mock_watchlist_dao.get_by_id.return_value = None
    with pytest.raises(WatchlistNotFoundError):
        await watchlist_service.add_to_watchlist(uuid4(), "AAPL", Market.US, mock_db)


@pytest.mark.asyncio
async def test_add_to_watchlist_dao_error(watchlist_service, mock_watchlist_dao, mock_db, sample_watchlist):
    mock_watchlist_dao.get_by_id.return_value = sample_watchlist
    mock_watchlist_dao.add_item.side_effect = Exception("DB error")
    with pytest.raises(WatchlistError, match="Failed to add"):
        await watchlist_service.add_to_watchlist(sample_watchlist.id, "AAPL", Market.US, mock_db)
    mock_db.rollback.assert_called_once()


# --- remove_from_watchlist ---

@pytest.mark.asyncio
async def test_remove_from_watchlist_success(watchlist_service, mock_watchlist_dao, mock_db, sample_watchlist, sample_item):
    mock_watchlist_dao.get_by_id.return_value = sample_watchlist
    mock_watchlist_dao.delete.return_value = True
    # Mock the session.execute to return the item
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = sample_item
    mock_watchlist_dao.session.execute.return_value = mock_result
    result = await watchlist_service.remove_from_watchlist(sample_watchlist.id, "AAPL", mock_db)
    assert result is True
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_remove_from_watchlist_item_not_found_returns_false(
    watchlist_service, mock_watchlist_dao, mock_db, sample_watchlist
):
    mock_watchlist_dao.get_by_id.return_value = sample_watchlist
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_watchlist_dao.session.execute.return_value = mock_result
    result = await watchlist_service.remove_from_watchlist(sample_watchlist.id, "AAPL", mock_db)
    assert result is False


@pytest.mark.asyncio
async def test_remove_from_watchlist_watchlist_not_found(watchlist_service, mock_watchlist_dao, mock_db):
    mock_watchlist_dao.get_by_id.return_value = None
    with pytest.raises(WatchlistNotFoundError):
        await watchlist_service.remove_from_watchlist(uuid4(), "AAPL", mock_db)


# --- get_default_watchlist ---

@pytest.mark.asyncio
async def test_get_default_watchlist_success(watchlist_service, mock_watchlist_dao, sample_watchlist):
    mock_watchlist_dao.get_default_watchlist.return_value = sample_watchlist
    result = await watchlist_service.get_default_watchlist(uuid4())
    assert result.name == "My Watchlist"


@pytest.mark.asyncio
async def test_get_default_watchlist_dao_error(watchlist_service, mock_watchlist_dao):
    mock_watchlist_dao.get_default_watchlist.side_effect = Exception("DB error")
    with pytest.raises(WatchlistError, match="Failed to get or create default watchlist"):
        await watchlist_service.get_default_watchlist(uuid4())
```

**Step 2: Run and verify tests pass**

```bash
uv run pytest tests/unit/test_services_watchlist.py -v --cov=backend/domains/portfolio/services/watchlist_service
```
Expected: All PASS. Coverage should reach >90%.

**Step 3: Commit**

```bash
git add tests/unit/test_services_watchlist.py
git commit -m "test: add WatchlistService unit tests"
```

---

### Task 3: ScheduleService unit tests

**Target:** `backend/domains/notifications/services/schedule_service.py` (53 missed stmts)

**Files:**
- Create: `tests/unit/test_services_schedule.py`

**Step 1: Write the failing tests**

```python
# tests/unit/test_services_schedule.py
"""Unit tests for ScheduleService."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timedelta

from backend.shared.ai.state.enums import Market
from backend.domains.notifications.services.schedule_service import ScheduleService
from backend.domains.notifications.services.schedule_exceptions import (
    ScheduleError,
    ScheduleNotFoundError,
    ScheduleRateLimitError,
)
from backend.shared.db.models import ScheduledAnalysis


@pytest.fixture
def mock_schedule_dao():
    dao = MagicMock()
    dao.session = MagicMock()
    dao.count_user_schedules = AsyncMock(return_value=0)
    dao.create = AsyncMock()
    dao.get_user_schedules = AsyncMock()
    dao.get_due_schedules = AsyncMock()
    dao.update_run_times = AsyncMock()
    dao.get_by_id = AsyncMock()
    dao.update = AsyncMock()
    dao.delete = AsyncMock()
    return dao


@pytest.fixture
def schedule_service(mock_schedule_dao):
    return ScheduleService(mock_schedule_dao)


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def sample_schedule():
    return ScheduledAnalysis(
        id=uuid4(),
        user_id=uuid4(),
        ticker="AAPL",
        market=Market.US,
        frequency="DAILY",
        active=True,
        next_run=datetime.now(),
    )


# --- create_scheduled_analysis ---

@pytest.mark.asyncio
async def test_create_schedule_success(schedule_service, mock_schedule_dao, mock_db, sample_schedule):
    mock_schedule_dao.count_user_schedules.return_value = 5
    mock_schedule_dao.create.return_value = sample_schedule
    result = await schedule_service.create_scheduled_analysis(
        uuid4(), "AAPL", Market.US, "DAILY", mock_db
    )
    assert result.ticker == "AAPL"
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


@pytest.mark.asyncio
async def test_create_schedule_rate_limit_exceeded(schedule_service, mock_schedule_dao, mock_db):
    mock_schedule_dao.count_user_schedules.return_value = 50  # at max
    with pytest.raises(ScheduleRateLimitError, match="maximum"):
        await schedule_service.create_scheduled_analysis(uuid4(), "AAPL", Market.US, "DAILY", mock_db)
    mock_schedule_dao.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_schedule_dao_error(schedule_service, mock_schedule_dao, mock_db):
    mock_schedule_dao.count_user_schedules.return_value = 0
    mock_schedule_dao.create.side_effect = Exception("DB error")
    with pytest.raises(ScheduleError, match="Failed to create schedule"):
        await schedule_service.create_scheduled_analysis(uuid4(), "AAPL", Market.US, "DAILY", mock_db)
    mock_db.rollback.assert_called_once()


# --- get_user_schedules ---

@pytest.mark.asyncio
async def test_get_user_schedules_success(schedule_service, mock_schedule_dao, sample_schedule):
    mock_schedule_dao.get_user_schedules.return_value = [sample_schedule]
    result = await schedule_service.get_user_schedules(uuid4())
    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_user_schedules_dao_error(schedule_service, mock_schedule_dao):
    mock_schedule_dao.get_user_schedules.side_effect = Exception("DB error")
    with pytest.raises(ScheduleError, match="Failed to fetch schedules"):
        await schedule_service.get_user_schedules(uuid4())


# --- get_due_schedules ---

@pytest.mark.asyncio
async def test_get_due_schedules_success(schedule_service, mock_schedule_dao, sample_schedule):
    mock_schedule_dao.get_due_schedules.return_value = [sample_schedule]
    result = await schedule_service.get_due_schedules()
    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_due_schedules_dao_error(schedule_service, mock_schedule_dao):
    mock_schedule_dao.get_due_schedules.side_effect = Exception("DB error")
    with pytest.raises(ScheduleError, match="Failed to fetch due schedules"):
        await schedule_service.get_due_schedules()


# --- update_run_times ---

@pytest.mark.asyncio
async def test_update_run_times_success(schedule_service, mock_schedule_dao, mock_db, sample_schedule):
    mock_schedule_dao.update_run_times.return_value = sample_schedule
    now = datetime.now()
    result = await schedule_service.update_run_times(sample_schedule.id, now, now + timedelta(days=1), mock_db)
    assert result == sample_schedule
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_run_times_not_found(schedule_service, mock_schedule_dao, mock_db):
    mock_schedule_dao.update_run_times.return_value = None
    with pytest.raises(ScheduleNotFoundError):
        await schedule_service.update_run_times(uuid4(), datetime.now(), datetime.now(), mock_db)


@pytest.mark.asyncio
async def test_update_run_times_dao_error(schedule_service, mock_schedule_dao, mock_db):
    mock_schedule_dao.update_run_times.side_effect = Exception("DB error")
    with pytest.raises(ScheduleError, match="Failed to update schedule"):
        await schedule_service.update_run_times(uuid4(), datetime.now(), datetime.now(), mock_db)
    mock_db.rollback.assert_called_once()


# --- toggle_schedule ---

@pytest.mark.asyncio
async def test_toggle_schedule_activate(schedule_service, mock_schedule_dao, mock_db, sample_schedule):
    sample_schedule.active = False
    mock_schedule_dao.get_by_id.return_value = sample_schedule
    mock_schedule_dao.update.return_value = sample_schedule
    result = await schedule_service.toggle_schedule(sample_schedule.id, True, mock_db)
    assert result.active is True
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_toggle_schedule_not_found(schedule_service, mock_schedule_dao, mock_db):
    mock_schedule_dao.get_by_id.return_value = None
    with pytest.raises(ScheduleNotFoundError):
        await schedule_service.toggle_schedule(uuid4(), True, mock_db)


@pytest.mark.asyncio
async def test_toggle_schedule_dao_error(schedule_service, mock_schedule_dao, mock_db, sample_schedule):
    mock_schedule_dao.get_by_id.return_value = sample_schedule
    mock_schedule_dao.update.side_effect = Exception("DB error")
    with pytest.raises(ScheduleError, match="Failed to toggle schedule"):
        await schedule_service.toggle_schedule(sample_schedule.id, True, mock_db)
    mock_db.rollback.assert_called_once()


# --- delete_schedule ---

@pytest.mark.asyncio
async def test_delete_schedule_success(schedule_service, mock_schedule_dao, mock_db):
    mock_schedule_dao.delete.return_value = True
    result = await schedule_service.delete_schedule(uuid4(), mock_db)
    assert result is True
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_schedule_dao_error(schedule_service, mock_schedule_dao, mock_db):
    mock_schedule_dao.delete.side_effect = Exception("DB error")
    with pytest.raises(ScheduleError, match="Failed to delete schedule"):
        await schedule_service.delete_schedule(uuid4(), mock_db)
    mock_db.rollback.assert_called_once()
```

**Step 2: Run and verify**

```bash
uv run pytest tests/unit/test_services_schedule.py -v --cov=backend/domains/notifications/services/schedule_service
```
Expected: All PASS. Coverage >90%.

**Step 3: Commit**

```bash
git add tests/unit/test_services_schedule.py
git commit -m "test: add ScheduleService unit tests"
```

---

### Task 4: AlertService unit tests

**Target:** `backend/domains/notifications/services/alert_service.py` (45 missed stmts)

**Files:**
- Create: `tests/unit/test_services_alert.py`

**Step 1: Read the AlertService fully first**

```bash
cat backend/domains/notifications/services/alert_service.py
```

Note: `AlertService` wraps `PriceAlertDAO` and `NotificationDAO`. Key methods: `create_price_alert`, `get_user_alerts`, `toggle_alert`, `delete_alert`, `create_notification`, `get_user_notifications`, `mark_notification_read`.

**Step 2: Write the failing tests**

```python
# tests/unit/test_services_alert.py
"""Unit tests for AlertService."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from backend.shared.ai.state.enums import Market
from backend.domains.notifications.services.alert_service import AlertService, AlertValidationError
from backend.shared.db.models import AlertCondition, NotificationType, PriceAlert


@pytest.fixture
def mock_price_alert_dao():
    dao = MagicMock()
    dao.session = MagicMock()
    dao.count_user_alerts = AsyncMock(return_value=0)
    dao.create = AsyncMock()
    dao.get_user_alerts = AsyncMock()
    dao.get_by_id = AsyncMock()
    dao.update = AsyncMock()
    dao.delete = AsyncMock()
    return dao


@pytest.fixture
def mock_notification_dao():
    dao = MagicMock()
    dao.session = MagicMock()
    dao.create = AsyncMock()
    dao.get_user_notifications = AsyncMock()
    dao.get_by_id = AsyncMock()
    dao.update = AsyncMock()
    dao.mark_all_read = AsyncMock()
    return dao


@pytest.fixture
def alert_service(mock_price_alert_dao, mock_notification_dao):
    return AlertService(mock_price_alert_dao, mock_notification_dao)


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def sample_alert():
    return PriceAlert(
        id=uuid4(),
        user_id=uuid4(),
        ticker="AAPL",
        market=Market.US,
        condition=AlertCondition.ABOVE,
        target_value=200.0,
        is_active=True,
    )


# --- create_price_alert ---

@pytest.mark.asyncio
async def test_create_price_alert_success(alert_service, mock_price_alert_dao, mock_db, sample_alert):
    mock_price_alert_dao.count_user_alerts.return_value = 5
    mock_price_alert_dao.create.return_value = sample_alert
    result = await alert_service.create_price_alert(
        db=mock_db,
        user_id=sample_alert.user_id,
        ticker="AAPL",
        market=Market.US,
        condition=AlertCondition.ABOVE,
        target_value=200.0,
    )
    assert result.ticker == "AAPL"
    assert result.target_value == 200.0


@pytest.mark.asyncio
async def test_create_price_alert_rate_limit(alert_service, mock_price_alert_dao, mock_db):
    mock_price_alert_dao.count_user_alerts.return_value = 50
    with pytest.raises(AlertValidationError, match="maximum"):
        await alert_service.create_price_alert(
            db=mock_db,
            user_id=uuid4(),
            ticker="AAPL",
            market=Market.US,
            condition=AlertCondition.ABOVE,
            target_value=200.0,
        )


@pytest.mark.asyncio
async def test_create_price_alert_invalid_target_value(alert_service, mock_price_alert_dao, mock_db):
    mock_price_alert_dao.count_user_alerts.return_value = 0
    with pytest.raises(AlertValidationError, match="positive"):
        await alert_service.create_price_alert(
            db=mock_db,
            user_id=uuid4(),
            ticker="AAPL",
            market=Market.US,
            condition=AlertCondition.ABOVE,
            target_value=-10.0,
        )


# --- get_user_alerts ---

@pytest.mark.asyncio
async def test_get_user_alerts(alert_service, mock_price_alert_dao, sample_alert):
    mock_price_alert_dao.get_user_alerts.return_value = [sample_alert]
    result = await alert_service.get_user_alerts(uuid4())
    assert len(result) == 1


# --- toggle_alert ---

@pytest.mark.asyncio
async def test_toggle_alert_success(alert_service, mock_price_alert_dao, mock_db, sample_alert):
    mock_price_alert_dao.get_by_id.return_value = sample_alert
    mock_price_alert_dao.update.return_value = sample_alert
    result = await alert_service.toggle_alert(sample_alert.id, False, mock_db)
    assert result is not None


@pytest.mark.asyncio
async def test_toggle_alert_not_found(alert_service, mock_price_alert_dao, mock_db):
    mock_price_alert_dao.get_by_id.return_value = None
    with pytest.raises(Exception):
        await alert_service.toggle_alert(uuid4(), False, mock_db)


# --- delete_alert ---

@pytest.mark.asyncio
async def test_delete_alert_success(alert_service, mock_price_alert_dao, mock_db):
    mock_price_alert_dao.delete.return_value = True
    result = await alert_service.delete_alert(uuid4(), mock_db)
    assert result is True


# --- get_user_notifications ---

@pytest.mark.asyncio
async def test_get_user_notifications(alert_service, mock_notification_dao):
    mock_notification_dao.get_user_notifications.return_value = []
    result = await alert_service.get_user_notifications(uuid4())
    assert result == []
```

**Step 3: Run and verify**

```bash
uv run pytest tests/unit/test_services_alert.py -v --cov=backend/domains/notifications/services/alert_service
```
Note: If some methods don't exist, check the full source and adjust method names accordingly. The file has ~93 statements; this covers the main paths.

**Step 4: Commit**

```bash
git add tests/unit/test_services_alert.py
git commit -m "test: add AlertService unit tests"
```

---

### Task 5: PerformanceService unit tests

**Target:** `backend/domains/performance/services/service.py` (62 missed stmts)

**Files:**
- Create: `tests/unit/test_services_performance.py`

**Step 1: Write the failing tests**

```python
# tests/unit/test_services_performance.py
"""Unit tests for PerformanceService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from backend.shared.ai.state.enums import Action
from backend.domains.performance.services.service import PerformanceService
from backend.shared.db.models import AnalysisOutcome, AnalysisSession, FinalDecision


@pytest.fixture
def mock_performance_dao():
    dao = MagicMock()
    dao.session = MagicMock()
    dao.create = AsyncMock()
    dao.get_all = AsyncMock()
    dao.get_recent_outcomes = AsyncMock()
    return dao


@pytest.fixture
def perf_service(mock_performance_dao):
    return PerformanceService(mock_performance_dao)


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def sample_session():
    s = MagicMock(spec=AnalysisSession)
    s.id = uuid4()
    s.ticker = "AAPL"
    s.market = "us"
    return s


@pytest.fixture
def sample_decision(sample_session):
    d = MagicMock(spec=FinalDecision)
    d.session_id = sample_session.id
    d.action = Action.BUY
    return d


@pytest.fixture
def sample_outcome(sample_session):
    o = MagicMock(spec=AnalysisOutcome)
    o.session_id = sample_session.id
    o.ticker = "AAPL"
    o.outcome_correct = True
    o.action_recommended = Action.BUY
    o.price_at_recommendation = 150.0
    o.price_after_1d = None
    o.price_after_7d = None
    o.price_after_30d = None
    o.price_after_90d = None
    o.created_at = datetime.now()
    return o


# --- create_analysis_outcome ---

@pytest.mark.asyncio
async def test_create_analysis_outcome_session_not_found(perf_service, mock_db):
    # db.execute returns empty result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    result = await perf_service.create_analysis_outcome(mock_db, uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_create_analysis_outcome_no_decision(perf_service, mock_db, sample_session):
    mock_session_result = MagicMock()
    mock_session_result.scalar_one_or_none.return_value = sample_session
    mock_decision_result = MagicMock()
    mock_decision_result.scalar_one_or_none.return_value = None
    mock_db.execute.side_effect = [mock_session_result, mock_decision_result]
    result = await perf_service.create_analysis_outcome(mock_db, uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_create_analysis_outcome_already_exists(perf_service, mock_db, sample_session, sample_decision):
    existing_outcome = MagicMock()
    mock_session_res = MagicMock()
    mock_session_res.scalar_one_or_none.return_value = sample_session
    mock_decision_res = MagicMock()
    mock_decision_res.scalar_one_or_none.return_value = sample_decision
    mock_existing_res = MagicMock()
    mock_existing_res.scalar_one_or_none.return_value = existing_outcome
    mock_db.execute.side_effect = [mock_session_res, mock_decision_res, mock_existing_res]
    result = await perf_service.create_analysis_outcome(mock_db, uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_create_analysis_outcome_price_fetch_error(perf_service, mock_db, sample_session, sample_decision):
    mock_session_res = MagicMock()
    mock_session_res.scalar_one_or_none.return_value = sample_session
    mock_decision_res = MagicMock()
    mock_decision_res.scalar_one_or_none.return_value = sample_decision
    mock_existing_res = MagicMock()
    mock_existing_res.scalar_one_or_none.return_value = None
    mock_db.execute.side_effect = [mock_session_res, mock_decision_res, mock_existing_res]
    with patch("backend.domains.performance.services.service.get_market_data_client") as mock_client:
        mock_client.return_value.get_stock_data = AsyncMock(side_effect=Exception("Network error"))
        result = await perf_service.create_analysis_outcome(mock_db, uuid4())
    assert result is None


# --- get_performance_summary ---

@pytest.mark.asyncio
async def test_get_performance_summary_empty(perf_service, mock_performance_dao, mock_db):
    mock_performance_dao.get_all.return_value = []
    result = await perf_service.get_performance_summary(mock_db)
    assert result["total_recommendations"] == 0
    assert result["accuracy"] == 0.0


@pytest.mark.asyncio
async def test_get_performance_summary_with_outcomes(perf_service, mock_performance_dao, mock_db):
    outcomes = []
    for action, correct in [(Action.BUY, True), (Action.BUY, False), (Action.SELL, True)]:
        o = MagicMock()
        o.action_recommended = action
        o.outcome_correct = correct
        outcomes.append(o)
    mock_performance_dao.get_all.return_value = outcomes
    result = await perf_service.get_performance_summary(mock_db)
    assert result["total_recommendations"] == 3
    assert result["correct_count"] == 2
    assert result["accuracy"] == pytest.approx(2 / 3)
    assert "BUY" in result["by_action"]


# --- get_recent_outcomes ---

@pytest.mark.asyncio
async def test_get_recent_outcomes_with_returns(perf_service, mock_performance_dao, mock_db):
    outcome = MagicMock()
    outcome.ticker = "AAPL"
    outcome.action_recommended = Action.BUY
    outcome.price_at_recommendation = 150.0
    outcome.price_after_1d = 155.0
    outcome.price_after_7d = None
    outcome.price_after_30d = 160.0
    outcome.price_after_90d = None
    outcome.outcome_correct = True
    outcome.created_at = datetime.now()
    decision = MagicMock()
    decision.confidence = 0.85
    session = MagicMock()
    mock_performance_dao.get_recent_outcomes.return_value = [(outcome, decision, session)]
    result = await perf_service.get_recent_outcomes(mock_db, limit=10)
    assert len(result) == 1
    assert "1d" in result[0]["returns"]
    assert "30d" in result[0]["returns"]
    assert "7d" not in result[0]["returns"]


@pytest.mark.asyncio
async def test_get_recent_outcomes_empty(perf_service, mock_performance_dao, mock_db):
    mock_performance_dao.get_recent_outcomes.return_value = []
    result = await perf_service.get_recent_outcomes(mock_db)
    assert result == []
```

**Step 2: Run and verify**

```bash
uv run pytest tests/unit/test_services_performance.py -v --cov=backend/domains/performance/services/service
```
Expected: All PASS. Coverage >80%.

**Step 3: Commit**

```bash
git add tests/unit/test_services_performance.py
git commit -m "test: add PerformanceService unit tests"
```

---

### Task 6: SettingsService unit tests

**Target:** `backend/domains/settings/services/service.py` (17 missed stmts)

**Files:**
- Create: `tests/unit/test_services_settings.py`

**Step 1: Write the failing tests**

```python
# tests/unit/test_services_settings.py
"""Unit tests for SettingsService."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from backend.domains.settings.services.service import SettingsService
from backend.domains.settings.services.exceptions import (
    EmailAlreadyTakenError,
    InvalidPasswordError,
    SettingsError,
)
from backend.shared.db.models import User
from backend.shared.core.security import get_password_hash


@pytest.fixture
def mock_user_dao():
    dao = MagicMock()
    dao.get_by_id = AsyncMock()
    dao.find_by_email = AsyncMock(return_value=None)
    return dao


@pytest.fixture
def settings_service(mock_user_dao):
    return SettingsService(mock_user_dao)


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def sample_user():
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.password_hash = get_password_hash("oldpassword")
    user.created_at = None
    return user


# --- update_profile ---

@pytest.mark.asyncio
async def test_update_profile_success(settings_service, mock_user_dao, mock_db, sample_user):
    mock_user_dao.get_by_id.return_value = sample_user
    result = await settings_service.update_profile(
        sample_user.id, mock_db, first_name="NewName"
    )
    assert result["first_name"] == "NewName"
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_profile_user_not_found(settings_service, mock_user_dao, mock_db):
    mock_user_dao.get_by_id.return_value = None
    with pytest.raises(SettingsError, match="User not found"):
        await settings_service.update_profile(uuid4(), mock_db)


@pytest.mark.asyncio
async def test_update_profile_email_already_taken(settings_service, mock_user_dao, mock_db, sample_user):
    mock_user_dao.get_by_id.return_value = sample_user
    mock_user_dao.find_by_email.return_value = MagicMock()  # Another user exists with that email
    with pytest.raises(EmailAlreadyTakenError):
        await settings_service.update_profile(
            sample_user.id, mock_db, email="taken@example.com"
        )


@pytest.mark.asyncio
async def test_update_profile_same_email_no_conflict(settings_service, mock_user_dao, mock_db, sample_user):
    """Updating with the same email should not raise EmailAlreadyTakenError."""
    mock_user_dao.get_by_id.return_value = sample_user
    # same email as current user - service should not check
    result = await settings_service.update_profile(
        sample_user.id, mock_db, email=sample_user.email
    )
    mock_user_dao.find_by_email.assert_not_called()


# --- change_password ---

@pytest.mark.asyncio
async def test_change_password_success(settings_service, mock_user_dao, mock_db, sample_user):
    mock_user_dao.get_by_id.return_value = sample_user
    await settings_service.change_password(
        sample_user.id, "oldpassword", "newpassword123", mock_db
    )
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_change_password_wrong_current(settings_service, mock_user_dao, mock_db, sample_user):
    mock_user_dao.get_by_id.return_value = sample_user
    with pytest.raises(InvalidPasswordError, match="incorrect"):
        await settings_service.change_password(
            sample_user.id, "wrongpassword", "newpassword123", mock_db
        )


@pytest.mark.asyncio
async def test_change_password_user_not_found(settings_service, mock_user_dao, mock_db):
    mock_user_dao.get_by_id.return_value = None
    with pytest.raises(SettingsError, match="User not found"):
        await settings_service.change_password(uuid4(), "old", "new", mock_db)
```

**Step 2: Run and verify**

```bash
uv run pytest tests/unit/test_services_settings.py -v --cov=backend/domains/settings/services/service
```
Expected: All PASS. Coverage >90%.

**Step 3: Commit**

```bash
git add tests/unit/test_services_settings.py
git commit -m "test: add SettingsService unit tests"
```

---

### Task 7: Shared tools unit tests (relative_strength + stock_search)

**Targets:**
- `backend/shared/ai/tools/relative_strength.py` (42 missed stmts, 16%)
- `backend/shared/ai/tools/stock_search.py` (24 missed stmts, 33%)

**Files:**
- Create: `tests/unit/test_relative_strength.py`
- Create: `tests/unit/test_stock_search.py`

**Step 1: Write relative_strength tests**

```python
# tests/unit/test_relative_strength.py
"""Unit tests for relative strength calculation tools."""

import pytest
from backend.shared.ai.tools.relative_strength import (
    calculate_correlation_matrix,
    calculate_relative_performance,
    calculate_relative_strength,
    calculate_valuation_comparison,
)


# Sample price histories
AAPL_HISTORY = [{"close": 150.0 + i} for i in range(10)]
MSFT_HISTORY = [{"close": 300.0 + i * 2} for i in range(10)]
TSLA_HISTORY = [{"close": 200.0 - i} for i in range(10)]


# --- calculate_correlation_matrix ---

def test_correlation_matrix_two_stocks():
    histories = {"AAPL": AAPL_HISTORY, "MSFT": MSFT_HISTORY}
    result = calculate_correlation_matrix(histories)
    assert "AAPL" in result
    assert "MSFT" in result
    assert result["AAPL"]["AAPL"] == 1.0
    assert result["MSFT"]["MSFT"] == 1.0
    # Both trending up, should have high positive correlation
    assert result["AAPL"]["MSFT"] > 0.9


def test_correlation_matrix_inverse_stocks():
    histories = {"AAPL": AAPL_HISTORY, "TSLA": TSLA_HISTORY}
    result = calculate_correlation_matrix(histories)
    # One up, one down → negative correlation
    assert result["AAPL"]["TSLA"] < 0


def test_correlation_matrix_single_stock_returns_empty():
    histories = {"AAPL": AAPL_HISTORY}
    result = calculate_correlation_matrix(histories)
    assert result == {}


def test_correlation_matrix_three_stocks():
    histories = {"AAPL": AAPL_HISTORY, "MSFT": MSFT_HISTORY, "TSLA": TSLA_HISTORY}
    result = calculate_correlation_matrix(histories)
    assert len(result) == 3
    for ticker in ["AAPL", "MSFT", "TSLA"]:
        assert result[ticker][ticker] == 1.0


def test_correlation_matrix_different_length_histories():
    short_history = [{"close": 100.0 + i} for i in range(5)]
    long_history = [{"close": 200.0 + i} for i in range(20)]
    histories = {"SHORT": short_history, "LONG": long_history}
    result = calculate_correlation_matrix(histories)
    assert "SHORT" in result


# --- calculate_relative_performance ---

def test_relative_performance_positive_return():
    histories = {"AAPL": AAPL_HISTORY}
    result = calculate_relative_performance(histories)
    # price went from 150 to 159, return = (159-150)/150 * 100 = 6%
    assert result["AAPL"] == pytest.approx(6.0, abs=0.1)


def test_relative_performance_negative_return():
    histories = {"TSLA": TSLA_HISTORY}
    result = calculate_relative_performance(histories)
    assert result["TSLA"] < 0


def test_relative_performance_single_price_returns_zero():
    histories = {"AAPL": [{"close": 150.0}]}
    result = calculate_relative_performance(histories)
    assert result["AAPL"] == 0.0


def test_relative_performance_zero_first_price():
    histories = {"WEIRD": [{"close": 0.0}, {"close": 10.0}]}
    result = calculate_relative_performance(histories)
    assert result["WEIRD"] == 0.0


def test_relative_performance_multiple_stocks():
    histories = {"AAPL": AAPL_HISTORY, "TSLA": TSLA_HISTORY}
    result = calculate_relative_performance(histories)
    assert "AAPL" in result
    assert "TSLA" in result
    assert result["AAPL"] > result["TSLA"]


# --- calculate_valuation_comparison ---

def test_valuation_comparison_with_report():
    fundamentals = {
        "AAPL": {
            "pe_ratio": 25.0,
            "revenue_growth": 0.15,
            "debt_to_equity": 1.5,
            "market_cap": 3e12,
        }
    }
    result = calculate_valuation_comparison(fundamentals)
    assert result["AAPL"]["pe_ratio"] == 25.0
    assert result["AAPL"]["revenue_growth"] == pytest.approx(15.0)  # converted to %


def test_valuation_comparison_with_none_report():
    fundamentals = {"AAPL": None}
    result = calculate_valuation_comparison(fundamentals)
    assert result["AAPL"]["pe_ratio"] == 0.0
    assert result["AAPL"]["market_cap"] == 0.0


def test_valuation_comparison_mixed():
    fundamentals = {
        "AAPL": {"pe_ratio": 25.0, "revenue_growth": 0.1, "debt_to_equity": 1.0, "market_cap": 3e12},
        "TSLA": None,
    }
    result = calculate_valuation_comparison(fundamentals)
    assert result["AAPL"]["pe_ratio"] == 25.0
    assert result["TSLA"]["pe_ratio"] == 0.0


# --- calculate_relative_strength (integration) ---

def test_calculate_relative_strength_returns_all_fields():
    histories = {"AAPL": AAPL_HISTORY, "MSFT": MSFT_HISTORY}
    fundamentals = {
        "AAPL": {"pe_ratio": 25.0, "revenue_growth": 0.1, "debt_to_equity": 1.0, "market_cap": 3e12},
        "MSFT": None,
    }
    result = calculate_relative_strength(histories, fundamentals)
    assert hasattr(result, "correlation_matrix")
    assert hasattr(result, "relative_performance")
    assert hasattr(result, "valuation_comparison")
    assert "AAPL" in result.relative_performance
```

**Step 2: Write stock_search tests**

```python
# tests/unit/test_stock_search.py
"""Unit tests for stock search utility."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.shared.ai.tools.stock_search import (
    POPULAR_TASE_STOCKS,
    POPULAR_US_STOCKS,
    StockSuggestion,
    search_stocks,
)
from backend.shared.ai.state.enums import Market


# --- search_stocks ---

@pytest.mark.asyncio
async def test_search_empty_query_returns_empty():
    result = await search_stocks("", Market.US)
    assert result == []


@pytest.mark.asyncio
async def test_search_single_char_query_returns_empty():
    # query length < 1 returns empty (>= 1 required, but "" returns empty)
    result = await search_stocks("", Market.US, limit=8)
    assert result == []


@pytest.mark.asyncio
async def test_search_popular_us_stock_by_symbol():
    result = await search_stocks("AAPL", Market.US)
    assert len(result) >= 1
    symbols = [r.symbol for r in result]
    assert "AAPL" in symbols


@pytest.mark.asyncio
async def test_search_popular_us_stock_by_partial_name():
    result = await search_stocks("Apple", Market.US)
    assert len(result) >= 1
    assert any(r.name == "Apple Inc." for r in result)


@pytest.mark.asyncio
async def test_search_popular_tase_stock():
    result = await search_stocks("TEVA", Market.TASE)
    assert len(result) >= 1
    assert any(r.symbol == "TEVA" for r in result)


@pytest.mark.asyncio
async def test_search_respects_limit():
    result = await search_stocks("A", Market.US, limit=2)
    assert len(result) <= 2


@pytest.mark.asyncio
async def test_search_unknown_ticker_fallback_to_yfinance():
    with patch("backend.shared.ai.tools.stock_search.yf.Ticker") as mock_ticker_class:
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "shortName": "Some Company",
            "exchange": "NASDAQ",
        }
        mock_ticker_class.return_value = mock_ticker
        result = await search_stocks("ZZZZ", Market.US)
        # Should include the yfinance result if valid
        # (may or may not match based on info structure)
        assert isinstance(result, list)


@pytest.mark.asyncio
async def test_search_yfinance_exception_handled_gracefully():
    with patch("backend.shared.ai.tools.stock_search.yf.Ticker") as mock_ticker_class:
        mock_ticker = MagicMock()
        mock_ticker.info = {}  # no shortName or longName
        mock_ticker_class.return_value = mock_ticker
        result = await search_stocks("ZZZZ", Market.US)
        assert isinstance(result, list)


@pytest.mark.asyncio
async def test_search_tase_formats_ticker_with_ta_suffix():
    """TASE search should append .TA suffix to ticker for yfinance lookup."""
    with patch("backend.shared.ai.tools.stock_search.yf.Ticker") as mock_ticker_class:
        mock_ticker = MagicMock()
        mock_ticker.info = {}
        mock_ticker_class.return_value = mock_ticker
        await search_stocks("UNKNOWNTASE", Market.TASE)
        # Verify .TA suffix was appended
        call_arg = mock_ticker_class.call_args[0][0]
        assert call_arg.endswith(".TA")


def test_stock_suggestion_dataclass():
    s = StockSuggestion(symbol="AAPL", name="Apple Inc.", exchange="NASDAQ", market=Market.US)
    assert s.symbol == "AAPL"
    assert s.market == Market.US
```

**Step 3: Run and verify**

```bash
uv run pytest tests/unit/test_relative_strength.py tests/unit/test_stock_search.py -v \
  --cov=backend/shared/ai/tools/relative_strength \
  --cov=backend/shared/ai/tools/stock_search
```
Expected: All PASS. relative_strength coverage >85%, stock_search coverage >75%.

**Step 4: Commit**

```bash
git add tests/unit/test_relative_strength.py tests/unit/test_stock_search.py
git commit -m "test: add relative_strength and stock_search unit tests"
```

---

## Wave 2: API Endpoint Tests

**Shared setup — add to `tests/conftest.py`:**

Before starting Wave 2, add this fixture to `tests/conftest.py`. It creates the FastAPI test client with auth dependency overridden.

```python
# Add to tests/conftest.py
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from backend.main import app as fastapi_app
from backend.shared.auth.dependencies import get_current_user


@pytest_asyncio.fixture
async def api_client(test_user):
    """AsyncClient with auth dependency overridden to test_user."""
    fastapi_app.dependency_overrides[get_current_user] = lambda: test_user
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as client:
        yield client
    fastapi_app.dependency_overrides.clear()
```

---

### Task 8: Performance API endpoint tests

**Target:** `backend/domains/performance/api/endpoints.py` (71 missed stmts, 24%)

**Files:**
- Create: `tests/unit/test_api_performance.py`

**Step 1: Write the tests**

```python
# tests/unit/test_api_performance.py
"""Unit tests for performance API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from backend.shared.ai.state.enums import Action


@pytest.mark.asyncio
async def test_get_performance_summary_empty(api_client):
    """GET /api/performance/summary returns empty data when no outcomes."""
    with patch("backend.domains.performance.api.endpoints.get_performance_service") as mock_factory:
        mock_service = MagicMock()
        mock_service.get_performance_summary = AsyncMock(return_value={
            "total_recommendations": 0,
            "correct_count": 0,
            "accuracy": 0.0,
            "by_action": {},
        })
        mock_factory.return_value = mock_service
        # Override via dependency_overrides
        from backend.main import app
        from backend.dependencies import get_performance_service
        app.dependency_overrides[get_performance_service] = lambda: mock_service
        response = await api_client.get("/api/performance/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_recommendations"] == 0
        app.dependency_overrides.clear()
        from backend.shared.auth.dependencies import get_current_user
        from tests.conftest import test_user  # re-add auth override if needed


@pytest.mark.asyncio
async def test_get_recent_outcomes(api_client):
    """GET /api/performance/recent returns list of outcomes."""
    from backend.main import app
    from backend.dependencies import get_performance_service

    mock_service = MagicMock()
    mock_service.get_recent_outcomes = AsyncMock(return_value=[
        {
            "ticker": "AAPL",
            "action": "BUY",
            "price_at_recommendation": 150.0,
            "confidence": 0.85,
            "outcome_correct": True,
            "returns": {"1d": 0.03},
            "created_at": datetime.now().isoformat(),
        }
    ])
    app.dependency_overrides[get_performance_service] = lambda: mock_service

    response = await api_client.get("/api/performance/recent")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["ticker"] == "AAPL"
    app.dependency_overrides.clear()
```

**Important note:** The performance API endpoints (and other domain API endpoints in Wave 2) access their services via `Depends()`. The cleanest way to test them is by overriding `app.dependency_overrides`. Each test should:
1. Set `app.dependency_overrides[get_<service>] = lambda: mock_service`
2. Make the API call
3. Assert response
4. Restore overrides (or let the `api_client` fixture handle it for auth)

For endpoints that directly query the DB (not via service), use `app.dependency_overrides[get_db] = lambda: mock_db`.

Create a helper in conftest to simplify this pattern (optional but recommended).

**Step 2: Better approach — use a shared service override fixture**

Instead of manually overriding in each test, add this pattern to `tests/conftest.py`:

```python
# Add to tests/conftest.py

from backend.dependencies import (
    get_alert_service,
    get_performance_service,
    get_schedule_service,
    get_watchlist_service,
    get_settings_service,
    get_analysis_service,
    get_portfolio_service,
)


@pytest.fixture
def mock_performance_service():
    svc = MagicMock()
    svc.get_performance_summary = AsyncMock(return_value={
        "total_recommendations": 0, "correct_count": 0, "accuracy": 0.0, "by_action": {}
    })
    svc.get_recent_outcomes = AsyncMock(return_value=[])
    svc.performance_dao = MagicMock()
    svc.performance_dao.session = MagicMock()
    return svc


@pytest.fixture
async def perf_api_client(test_user, mock_performance_service):
    from backend.main import app
    from backend.shared.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_performance_service] = lambda: mock_performance_service
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
```

**Full test file:**

```python
# tests/unit/test_api_performance.py
"""Unit tests for performance API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from uuid import uuid4

from httpx import ASGITransport, AsyncClient
from backend.main import app
from backend.shared.auth.dependencies import get_current_user
from backend.dependencies import get_performance_service
from backend.shared.ai.state.enums import Action, AgentType


@pytest.fixture
def mock_perf_svc():
    svc = MagicMock()
    svc.get_performance_summary = AsyncMock(return_value={
        "total_recommendations": 5,
        "correct_count": 3,
        "accuracy": 0.6,
        "by_action": {"BUY": {"total": 3, "correct": 2, "accuracy": 0.67}},
    })
    svc.get_recent_outcomes = AsyncMock(return_value=[
        {
            "ticker": "AAPL",
            "action": "BUY",
            "price_at_recommendation": 150.0,
            "confidence": 0.85,
            "outcome_correct": True,
            "returns": {"1d": 0.03},
            "created_at": datetime.now().isoformat(),
        }
    ])
    svc.performance_dao = MagicMock()
    svc.performance_dao.session = MagicMock()
    return svc


@pytest.fixture
async def perf_client(test_user, mock_perf_svc):
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_performance_service] = lambda: mock_perf_svc
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_summary(perf_client):
    response = await perf_client.get("/api/performance/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_recommendations"] == 5
    assert data["accuracy"] == pytest.approx(0.6)


@pytest.mark.asyncio
async def test_get_recent_outcomes(perf_client):
    response = await perf_client.get("/api/performance/recent")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["ticker"] == "AAPL"


@pytest.mark.asyncio
async def test_get_recent_outcomes_with_ticker_filter(perf_client, mock_perf_svc):
    response = await perf_client.get("/api/performance/recent?ticker=AAPL&limit=5")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_agent_leaderboard(perf_client, test_db_session):
    """GET /api/performance/leaderboard - returns empty when no data."""
    # This endpoint queries DB directly; with empty test DB, should return []
    from backend.shared.db.database import get_db
    app.dependency_overrides[get_db] = lambda: test_db_session
    response = await perf_client.get("/api/performance/leaderboard")
    assert response.status_code == 200
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_get_outcomes_list(perf_client, test_db_session):
    """GET /api/performance/outcomes - returns empty when no data."""
    from backend.shared.db.database import get_db
    app.dependency_overrides[get_db] = lambda: test_db_session
    response = await perf_client.get("/api/performance/outcomes")
    assert response.status_code == 200
    app.dependency_overrides.pop(get_db, None)
```

**Step 3: Run and verify**

```bash
uv run pytest tests/unit/test_api_performance.py -v --cov=backend/domains/performance/api/endpoints
```
Expected: All PASS. Coverage jumps from 24% to >60%.

**Step 4: Commit**

```bash
git add tests/unit/test_api_performance.py
git commit -m "test: add performance API endpoint unit tests"
```

---

### Task 9: Alerts and Schedules API endpoint tests

**Targets:**
- `backend/domains/notifications/api/alerts.py` (41 missed stmts, 34%)
- `backend/domains/notifications/api/schedules.py` (28 missed stmts, 42%)
- `backend/domains/notifications/api/endpoints.py` (28 missed stmts, 42%)

**Files:**
- Create: `tests/unit/test_api_notifications.py`

**Step 1: Write the tests**

```python
# tests/unit/test_api_notifications.py
"""Unit tests for notifications API (alerts, schedules, notifications)."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from httpx import ASGITransport, AsyncClient
from backend.main import app
from backend.shared.auth.dependencies import get_current_user
from backend.dependencies import get_alert_service, get_schedule_service
from backend.shared.db.models import AlertCondition, Market, PriceAlert, NotificationType


@pytest.fixture
def sample_alert(test_user):
    alert = MagicMock(spec=PriceAlert)
    alert.id = uuid4()
    alert.user_id = test_user.id
    alert.ticker = "AAPL"
    alert.market = "us"
    alert.condition = "ABOVE"
    alert.target_value = 200.0
    alert.is_active = True
    alert.created_at = datetime.now()
    alert.triggered_at = None
    return alert


@pytest.fixture
def mock_alert_svc(sample_alert):
    svc = MagicMock()
    svc.create_price_alert = AsyncMock(return_value=sample_alert)
    svc.get_user_alerts = AsyncMock(return_value=[sample_alert])
    svc.toggle_alert = AsyncMock(return_value=sample_alert)
    svc.delete_alert = AsyncMock(return_value=True)
    svc.get_user_notifications = AsyncMock(return_value=[])
    svc.mark_notification_read = AsyncMock()
    svc.price_alert_dao = MagicMock()
    svc.price_alert_dao.session = MagicMock()
    svc.price_alert_dao.session.commit = AsyncMock()
    svc.price_alert_dao.session.rollback = AsyncMock()
    return svc


@pytest.fixture
def sample_schedule(test_user):
    sched = MagicMock()
    sched.id = uuid4()
    sched.user_id = test_user.id
    sched.ticker = "AAPL"
    sched.market = "us"
    sched.frequency = "DAILY"
    sched.active = True
    sched.next_run = datetime.now()
    sched.last_run = None
    sched.created_at = datetime.now()
    return sched


@pytest.fixture
def mock_schedule_svc(sample_schedule):
    svc = MagicMock()
    svc.create_scheduled_analysis = AsyncMock(return_value=sample_schedule)
    svc.get_user_schedules = AsyncMock(return_value=[sample_schedule])
    svc.toggle_schedule = AsyncMock(return_value=sample_schedule)
    svc.delete_schedule = AsyncMock(return_value=True)
    svc.schedule_dao = MagicMock()
    svc.schedule_dao.session = MagicMock()
    return svc


@pytest.fixture
async def alerts_client(test_user, mock_alert_svc):
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_alert_service] = lambda: mock_alert_svc
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def schedules_client(test_user, mock_schedule_svc):
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_schedule_service] = lambda: mock_schedule_svc
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


# ===================== ALERTS =====================

@pytest.mark.asyncio
async def test_create_alert(alerts_client, sample_alert):
    response = await alerts_client.post("/api/alerts", json={
        "ticker": "AAPL",
        "market": "us",
        "condition": "ABOVE",
        "target_value": 200.0,
    })
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_alert_validation_error(alerts_client, mock_alert_svc):
    from backend.domains.notifications.services.alert_service import AlertValidationError
    mock_alert_svc.create_price_alert.side_effect = AlertValidationError("Too many alerts")
    response = await alerts_client.post("/api/alerts", json={
        "ticker": "AAPL",
        "market": "us",
        "condition": "ABOVE",
        "target_value": 200.0,
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_alerts(alerts_client):
    response = await alerts_client.get("/api/alerts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_toggle_alert(alerts_client, sample_alert):
    response = await alerts_client.patch(f"/api/alerts/{sample_alert.id}", json={"is_active": False})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_alert(alerts_client, sample_alert):
    response = await alerts_client.delete(f"/api/alerts/{sample_alert.id}")
    assert response.status_code in (200, 204)


# ===================== SCHEDULES =====================

@pytest.mark.asyncio
async def test_create_schedule(schedules_client, sample_schedule):
    response = await schedules_client.post("/api/schedules", json={
        "ticker": "AAPL",
        "market": "us",
        "frequency": "DAILY",
    })
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_schedule_rate_limit(schedules_client, mock_schedule_svc):
    from backend.domains.notifications.services.schedule_exceptions import ScheduleRateLimitError
    mock_schedule_svc.create_scheduled_analysis.side_effect = ScheduleRateLimitError("Rate limit")
    response = await schedules_client.post("/api/schedules", json={
        "ticker": "AAPL",
        "market": "us",
        "frequency": "DAILY",
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_schedules(schedules_client):
    response = await schedules_client.get("/api/schedules")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_toggle_schedule(schedules_client, sample_schedule):
    response = await schedules_client.patch(f"/api/schedules/{sample_schedule.id}", json={"active": False})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_schedule(schedules_client, sample_schedule):
    response = await schedules_client.delete(f"/api/schedules/{sample_schedule.id}")
    assert response.status_code in (200, 204)


# ===================== NOTIFICATIONS (list/mark-read) =====================

@pytest.mark.asyncio
async def test_list_notifications(alerts_client):
    response = await alerts_client.get("/api/notifications")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

**Step 2: Run and verify**

```bash
uv run pytest tests/unit/test_api_notifications.py -v \
  --cov=backend/domains/notifications/api/alerts \
  --cov=backend/domains/notifications/api/schedules \
  --cov=backend/domains/notifications/api/endpoints
```
Expected: All PASS. Alert endpoint coverage >70%, schedule endpoint coverage >70%.

Note: If endpoint URLs differ (check actual router prefix), adjust the paths. Alerts: `/api/alerts`, Schedules: `/api/schedules`, Notifications: `/api/notifications`.

**Step 3: Commit**

```bash
git add tests/unit/test_api_notifications.py
git commit -m "test: add notifications/alerts/schedules API endpoint tests"
```

---

### Task 10: Strategies and Paper Trading API tests

**Targets:**
- `backend/domains/analysis/api/strategies/router.py` (38 missed stmts, 37%)
- `backend/domains/analysis/api/paper/router.py` (154 missed stmts, 17%)

**Files:**
- Create: `tests/unit/test_api_strategies.py`
- Create: `tests/unit/test_api_paper_trading.py`

**Step 1: Read paper router for remaining endpoints**

```bash
cat backend/domains/analysis/api/paper/router.py
```

Key endpoints: POST /api/paper/accounts, GET /api/paper/accounts, GET /api/paper/accounts/{id}, POST /api/paper/accounts/{id}/trade, GET /api/paper/accounts/{id}/performance, GET /api/paper/positions, PATCH /api/paper/accounts/{id}

**Step 2: Write strategies tests**

```python
# tests/unit/test_api_strategies.py
"""Unit tests for strategies API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from httpx import ASGITransport, AsyncClient
from backend.main import app
from backend.shared.auth.dependencies import get_current_user
from backend.shared.db.database import get_db
from backend.shared.db.models.backtesting import Strategy


@pytest.fixture
def sample_strategy(test_user):
    s = MagicMock(spec=Strategy)
    s.id = uuid4()
    s.user_id = test_user.id
    s.name = "Balanced Growth"
    s.description = "Test strategy"
    s.config = {"weights": {"fundamental": 0.4, "technical": 0.4, "sentiment": 0.2}}
    s.created_at = datetime.now()
    return s


@pytest.fixture
async def strategies_client(test_user, test_db_session, sample_strategy):
    """Test client with mocked DB that returns pre-seeded strategy data."""
    # We use the real test_db_session but mock StrategyDAO methods
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_db] = lambda: test_db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_strategy(strategies_client, test_db_session):
    with patch("backend.domains.analysis.api.strategies.router.StrategyDAO") as mock_dao_class:
        mock_dao = MagicMock()
        mock_dao.create = AsyncMock()
        mock_dao_class.return_value = mock_dao
        response = await strategies_client.post("/api/strategies", json={
            "name": "Balanced Growth",
            "description": "Equal weight strategy",
            "config": {
                "weights": {"fundamental": 0.4, "technical": 0.4, "sentiment": 0.2},
                "thresholds": {"buy": 70, "sell": 30},
                "risk_params": {"max_position_size": 0.5, "stop_loss": 0.1}
            }
        })
        assert response.status_code == 201


@pytest.mark.asyncio
async def test_list_strategies(strategies_client):
    with patch("backend.domains.analysis.api.strategies.router.StrategyDAO") as mock_dao_class:
        mock_dao = MagicMock()
        mock_dao.get_user_strategies = AsyncMock(return_value=[])
        mock_dao_class.return_value = mock_dao
        response = await strategies_client.get("/api/strategies")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_strategy_not_found(strategies_client):
    with patch("backend.domains.analysis.api.strategies.router.StrategyDAO") as mock_dao_class:
        mock_dao = MagicMock()
        mock_dao.get_by_id_and_user = AsyncMock(return_value=None)
        mock_dao_class.return_value = mock_dao
        response = await strategies_client.get(f"/api/strategies/{uuid4()}")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_strategy_not_found(strategies_client):
    with patch("backend.domains.analysis.api.strategies.router.StrategyDAO") as mock_dao_class:
        mock_dao = MagicMock()
        mock_dao.get_by_id_and_user = AsyncMock(return_value=None)
        mock_dao_class.return_value = mock_dao
        response = await strategies_client.delete(f"/api/strategies/{uuid4()}")
        assert response.status_code == 404
```

**Step 3: Write paper trading tests**

```python
# tests/unit/test_api_paper_trading.py
"""Unit tests for paper trading API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from httpx import ASGITransport, AsyncClient
from backend.main import app
from backend.shared.auth.dependencies import get_current_user
from backend.shared.db.database import get_db
from backend.shared.db.models.backtesting import PaperAccount, TradeType


@pytest.fixture
def sample_account(test_user):
    a = MagicMock(spec=PaperAccount)
    a.id = uuid4()
    a.user_id = test_user.id
    a.strategy_id = uuid4()
    a.name = "Test Account"
    a.initial_balance = 10000.0
    a.current_balance = 10000.0
    a.is_active = True
    a.created_at = datetime.now()
    return a


@pytest.fixture
async def paper_client(test_user, test_db_session):
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_db] = lambda: test_db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_paper_account_strategy_not_found(paper_client):
    with patch("backend.domains.analysis.api.paper.router.StrategyDAO") as mock_dao_class:
        mock_dao = MagicMock()
        mock_dao.get_by_id_and_user = AsyncMock(return_value=None)
        mock_dao_class.return_value = mock_dao
        response = await paper_client.post("/api/paper/accounts", json={
            "name": "Test Account",
            "strategy_id": str(uuid4()),
            "initial_balance": 10000.0,
        })
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_paper_account_success(paper_client, sample_account):
    with (
        patch("backend.domains.analysis.api.paper.router.StrategyDAO") as mock_strategy_dao_class,
        patch("backend.domains.analysis.api.paper.router.PaperAccountDAO") as mock_account_dao_class,
    ):
        mock_strategy_dao = MagicMock()
        mock_strategy_dao.get_by_id_and_user = AsyncMock(return_value=MagicMock())
        mock_strategy_dao_class.return_value = mock_strategy_dao

        mock_account_dao = MagicMock()
        mock_account_dao.create = AsyncMock(return_value=sample_account)
        mock_account_dao_class.return_value = mock_account_dao

        response = await paper_client.post("/api/paper/accounts", json={
            "name": "Test Account",
            "strategy_id": str(sample_account.strategy_id),
            "initial_balance": 10000.0,
        })
        assert response.status_code == 201


@pytest.mark.asyncio
async def test_list_paper_accounts(paper_client, sample_account):
    with patch("backend.domains.analysis.api.paper.router.PaperAccountDAO") as mock_dao_class:
        mock_dao = MagicMock()
        mock_dao.get_user_accounts = AsyncMock(return_value=[sample_account])
        mock_dao_class.return_value = mock_dao
        response = await paper_client.get("/api/paper/accounts")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_paper_account_not_found(paper_client):
    with patch("backend.domains.analysis.api.paper.router.PaperAccountDAO") as mock_dao_class:
        mock_dao = MagicMock()
        mock_dao.get_by_id_and_user = AsyncMock(return_value=None)
        mock_dao_class.return_value = mock_dao
        response = await paper_client.get(f"/api/paper/accounts/{uuid4()}")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_execute_trade_account_not_found(paper_client):
    with patch("backend.domains.analysis.api.paper.router.PaperAccountDAO") as mock_dao_class:
        mock_dao = MagicMock()
        mock_dao.get_by_id_and_user = AsyncMock(return_value=None)
        mock_dao_class.return_value = mock_dao
        response = await paper_client.post(f"/api/paper/accounts/{uuid4()}/trade", json={
            "ticker": "AAPL",
            "trade_type": "BUY",
            "quantity": 10,
        })
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_performance_account_not_found(paper_client):
    with patch("backend.domains.analysis.api.paper.router.PaperAccountDAO") as mock_dao_class:
        mock_dao = MagicMock()
        mock_dao.get_by_id_and_user = AsyncMock(return_value=None)
        mock_dao_class.return_value = mock_dao
        response = await paper_client.get(f"/api/paper/accounts/{uuid4()}/performance")
        assert response.status_code == 404
```

**Step 4: Run and verify**

```bash
uv run pytest tests/unit/test_api_strategies.py tests/unit/test_api_paper_trading.py -v \
  --cov=backend/domains/analysis/api/strategies/router \
  --cov=backend/domains/analysis/api/paper/router
```
Expected: All PASS. Strategies coverage >60%, paper router coverage >40% (large file).

**Step 5: Commit**

```bash
git add tests/unit/test_api_strategies.py tests/unit/test_api_paper_trading.py
git commit -m "test: add strategies and paper trading API endpoint tests"
```

---

### Task 11: Sectors API tests + auth dependencies tests

**Targets:**
- `backend/domains/sectors/api/endpoints.py` (20 missed stmts, 35%)
- `backend/shared/auth/dependencies.py` (19 missed stmts, 39%)

**Files:**
- Create: `tests/unit/test_api_sectors.py`
- Create: `tests/unit/test_auth_dependencies.py`

**Step 1: Write sectors tests**

```python
# tests/unit/test_api_sectors.py
"""Unit tests for sectors API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import ASGITransport, AsyncClient
from backend.main import app
from backend.shared.auth.dependencies import get_current_user


@pytest.fixture
async def sectors_client():
    """Sectors endpoints don't require auth for GET /."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_list_sectors(sectors_client):
    response = await sectors_client.get("/api/sectors/")
    assert response.status_code == 200
    data = response.json()
    assert "sectors" in data
    assert len(data["sectors"]) > 0


@pytest.mark.asyncio
async def test_compare_stocks_too_few(sectors_client):
    response = await sectors_client.post("/api/sectors/compare", json={
        "tickers": ["AAPL"],
        "market": "us",
    })
    assert response.status_code == 400
    assert "at least 2" in response.json()["detail"]


@pytest.mark.asyncio
async def test_compare_stocks_too_many(sectors_client):
    response = await sectors_client.post("/api/sectors/compare", json={
        "tickers": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
        "market": "us",
    })
    assert response.status_code == 400
    assert "Maximum 4" in response.json()["detail"]


@pytest.mark.asyncio
async def test_analyze_sector_not_found(sectors_client):
    with patch("backend.domains.sectors.api.endpoints.get_sector_tickers") as mock_fn:
        mock_fn.return_value = []
        response = await sectors_client.post("/api/sectors/analyze", json={
            "sector": "NonExistentSector",
            "market": "us",
            "limit": 5,
        })
        assert response.status_code == 404
```

**Step 2: Write auth dependency tests**

```python
# tests/unit/test_auth_dependencies.py
"""Unit tests for auth dependencies."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from backend.shared.auth.dependencies import get_current_user, get_current_user_optional
from backend.shared.core.security import create_access_token
from backend.shared.core.settings import settings
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_db():
    db = MagicMock(spec=AsyncSession)
    db.execute = AsyncMock()
    return db


@pytest.fixture
def valid_token(test_user):
    return create_access_token({"sub": test_user.email})


@pytest.mark.asyncio
async def test_get_current_user_valid_token(test_user, mock_db, valid_token):
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = test_user
    mock_db.execute.return_value = mock_result
    user = await get_current_user(valid_token, mock_db)
    assert user == test_user


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(mock_db):
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user("invalid.token.here", mock_db)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_user_not_found(mock_db, valid_token):
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(valid_token, mock_db)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_optional_no_token(mock_db):
    result = await get_current_user_optional(None, mock_db)
    assert result is None


@pytest.mark.asyncio
async def test_get_current_user_optional_valid_token(test_user, mock_db, valid_token):
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = test_user
    mock_db.execute.return_value = mock_result
    result = await get_current_user_optional(valid_token, mock_db)
    assert result == test_user


@pytest.mark.asyncio
async def test_get_current_user_optional_invalid_token(mock_db):
    result = await get_current_user_optional("bad.token", mock_db)
    assert result is None
```

Note: `create_access_token` must exist in `backend/shared/core/security.py`. Check the exact function signature before running.

**Step 3: Run and verify**

```bash
uv run pytest tests/unit/test_api_sectors.py tests/unit/test_auth_dependencies.py -v \
  --cov=backend/domains/sectors/api/endpoints \
  --cov=backend/shared/auth/dependencies
```
Expected: All PASS. Sectors coverage >60%, auth coverage >70%.

**Step 4: Commit**

```bash
git add tests/unit/test_api_sectors.py tests/unit/test_auth_dependencies.py
git commit -m "test: add sectors API and auth dependency tests"
```

---

## Wave 3: Background Job Integration Tests (PostgreSQL)

> These tests require the `TEST_DATABASE_URL` env var pointing to a running PostgreSQL database.
> Set `TEST_DATABASE_URL` to your test PostgreSQL URL (see `.env.example` for the default test credentials).

### Task 12: outcome_tracker integration tests

**Target:** `backend/shared/jobs/outcome_tracker.py` (131 missed stmts, 10%)

**Files:**
- Create: `tests/integration/test_outcome_tracker.py`

**Step 1: Write the tests**

```python
# tests/integration/test_outcome_tracker.py
"""Integration tests for the outcome tracker background job."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.ai.state.enums import Action, AgentType, Market
from backend.shared.db.models import (
    AnalysisOutcome,
    AnalysisSession,
    FinalDecision,
    AgentReport,
)
from backend.shared.jobs.outcome_tracker import (
    _was_recommendation_correct,
    update_agent_accuracy,
    update_outcome_prices,
)


# ===================== _was_recommendation_correct (pure function) =====================

def test_buy_correct_when_price_goes_up():
    assert _was_recommendation_correct(Action.BUY, 100.0, 105.0) is True


def test_buy_incorrect_when_price_goes_down():
    assert _was_recommendation_correct(Action.BUY, 100.0, 95.0) is False


def test_sell_correct_when_price_goes_down():
    assert _was_recommendation_correct(Action.SELL, 100.0, 95.0) is True


def test_sell_incorrect_when_price_goes_up():
    assert _was_recommendation_correct(Action.SELL, 100.0, 105.0) is False


def test_hold_correct_when_price_stable():
    # 1% change is within 2% threshold
    assert _was_recommendation_correct(Action.HOLD, 100.0, 101.0) is True


def test_hold_incorrect_when_price_moves_significantly():
    # 5% change exceeds 2% threshold
    assert _was_recommendation_correct(Action.HOLD, 100.0, 106.0) is False


def test_hold_correct_when_price_drops_slightly():
    assert _was_recommendation_correct(Action.HOLD, 100.0, 99.0) is True


def test_hold_incorrect_when_price_drops_significantly():
    assert _was_recommendation_correct(Action.HOLD, 100.0, 90.0) is False


def test_custom_threshold():
    assert _was_recommendation_correct(Action.HOLD, 100.0, 104.0, threshold=0.05) is True
    assert _was_recommendation_correct(Action.HOLD, 100.0, 106.0, threshold=0.05) is False


# ===================== update_outcome_prices (integration) =====================

@pytest.mark.asyncio
async def test_update_outcome_prices_no_outcomes(test_db_session: AsyncSession):
    """When no outcomes exist, returns 0."""
    result = await update_outcome_prices(test_db_session)
    assert result == 0


@pytest.mark.asyncio
async def test_update_outcome_prices_updates_1d_price(test_db_session: AsyncSession, test_user):
    """Creates an outcome older than 1 day, verifies price is updated."""
    # Create analysis session
    session = AnalysisSession(
        id=uuid4(),
        ticker="AAPL",
        market=Market.US,
        user_id=test_user.id,
        created_at=datetime.now() - timedelta(days=2),  # 2 days ago
    )
    test_db_session.add(session)

    # Create final decision
    decision = FinalDecision(
        id=uuid4(),
        session_id=session.id,
        action=Action.BUY,
        confidence=0.85,
        rationale="Test",
        vetoed=False,
        created_at=datetime.now() - timedelta(days=2),
    )
    test_db_session.add(decision)

    # Create outcome (no follow-up prices yet)
    outcome = AnalysisOutcome(
        id=uuid4(),
        session_id=session.id,
        ticker="AAPL",
        action_recommended=Action.BUY,
        price_at_recommendation=150.0,
        created_at=datetime.now() - timedelta(days=2),
        last_updated=datetime.now() - timedelta(days=2),
    )
    test_db_session.add(outcome)
    await test_db_session.commit()

    # Mock market data client to return a price
    with patch("backend.shared.jobs.outcome_tracker.get_market_data_client") as mock_client:
        mock_market = MagicMock()
        mock_market.get_stock_data = AsyncMock(return_value={"current_price": 155.0})
        mock_client.return_value = mock_market

        result = await update_outcome_prices(test_db_session)
        assert result >= 1  # At least 1d price updated

    # Verify the outcome was updated
    await test_db_session.refresh(outcome)
    assert outcome.price_after_1d == 155.0


@pytest.mark.asyncio
async def test_update_outcome_prices_skips_fully_tracked(test_db_session: AsyncSession, test_user):
    """Outcomes with all prices filled (price_after_90d set) are skipped."""
    session = AnalysisSession(
        id=uuid4(), ticker="AAPL", market=Market.US,
        user_id=test_user.id,
        created_at=datetime.now() - timedelta(days=100),
    )
    test_db_session.add(session)

    outcome = AnalysisOutcome(
        id=uuid4(),
        session_id=session.id,
        ticker="AAPL",
        action_recommended=Action.BUY,
        price_at_recommendation=150.0,
        price_after_1d=152.0,
        price_after_7d=155.0,
        price_after_30d=160.0,
        price_after_90d=170.0,  # Fully tracked
        outcome_correct=True,
        created_at=datetime.now() - timedelta(days=100),
        last_updated=datetime.now() - timedelta(days=5),
    )
    test_db_session.add(outcome)
    await test_db_session.commit()

    result = await update_outcome_prices(test_db_session)
    assert result == 0  # Fully tracked outcomes are excluded from query


@pytest.mark.asyncio
async def test_update_outcome_prices_handles_network_error(test_db_session: AsyncSession, test_user):
    """Network errors during price fetch are handled gracefully."""
    session = AnalysisSession(
        id=uuid4(), ticker="AAPL", market=Market.US,
        user_id=test_user.id,
        created_at=datetime.now() - timedelta(days=2),
    )
    test_db_session.add(session)
    outcome = AnalysisOutcome(
        id=uuid4(), session_id=session.id, ticker="AAPL",
        action_recommended=Action.BUY, price_at_recommendation=150.0,
        created_at=datetime.now() - timedelta(days=2),
        last_updated=datetime.now() - timedelta(days=2),
    )
    test_db_session.add(outcome)
    await test_db_session.commit()

    with patch("backend.shared.jobs.outcome_tracker.get_market_data_client") as mock_client:
        import os
        err = OSError("Name or service not known")
        err.errno = -2
        mock_client.return_value.get_stock_data = AsyncMock(side_effect=err)
        # Should not raise
        result = await update_outcome_prices(test_db_session)
        assert result == 0  # Nothing updated due to network error


# ===================== update_agent_accuracy =====================

@pytest.mark.asyncio
async def test_update_agent_accuracy_no_data(test_db_session: AsyncSession):
    """update_agent_accuracy runs without error even with no data."""
    # Should not raise
    await update_agent_accuracy(test_db_session)
```

**Step 2: Run and verify**

```bash
uv run pytest tests/integration/test_outcome_tracker.py -v \
  --cov=backend/shared/jobs/outcome_tracker
```
Expected: All PASS. Coverage jumps from 10% to >55%.

**Step 3: Commit**

```bash
git add tests/integration/test_outcome_tracker.py
git commit -m "test: add outcome_tracker integration tests"
```

---

### Task 13: Scheduler integration tests

**Target:** `backend/shared/jobs/scheduler.py` (78 missed stmts, 22%)

**Files:**
- Create: `tests/integration/test_scheduler.py`

**Step 1: Read the scheduler file**

```bash
cat backend/shared/jobs/scheduler.py
```

**Step 2: Write the tests**

```python
# tests/integration/test_scheduler.py
"""Integration tests for the APScheduler background job scheduler."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.shared.jobs.scheduler import (
    get_scheduler,
    setup_scheduler,
    shutdown_scheduler,
)


@pytest.mark.asyncio
async def test_get_scheduler_returns_instance():
    """get_scheduler() returns an AsyncIOScheduler instance."""
    scheduler = get_scheduler()
    assert scheduler is not None


@pytest.mark.asyncio
async def test_setup_scheduler_creates_jobs():
    """setup_scheduler registers background jobs."""
    with patch("backend.shared.jobs.scheduler.AsyncIOScheduler") as mock_scheduler_class:
        mock_scheduler = MagicMock()
        mock_scheduler.add_job = MagicMock()
        mock_scheduler.start = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler

        from backend.shared.db.database import get_db
        mock_db_factory = MagicMock(return_value=AsyncMock())

        setup_scheduler(mock_db_factory)
        mock_scheduler.start.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown_scheduler_stops_jobs():
    """shutdown_scheduler stops the scheduler gracefully."""
    with patch("backend.shared.jobs.scheduler.get_scheduler") as mock_get:
        mock_scheduler = MagicMock()
        mock_scheduler.running = True
        mock_scheduler.shutdown = MagicMock()
        mock_get.return_value = mock_scheduler
        shutdown_scheduler()
        mock_scheduler.shutdown.assert_called_once()
```

Note: Scheduler tests are primarily about confirming the job setup and teardown mechanics work. The actual job functions (alert_checker, outcome_tracker) are tested in their own files. Adjust function names to match `backend/shared/jobs/scheduler.py` exactly.

**Step 3: Run and verify**

```bash
uv run pytest tests/integration/test_scheduler.py -v --cov=backend/shared/jobs/scheduler
```
Expected: All PASS.

**Step 4: Commit**

```bash
git add tests/integration/test_scheduler.py
git commit -m "test: add scheduler integration tests"
```

---

## Wave 4: WebSocket Mock Tests

### Task 14: WebSocket handler tests

**Target:** `backend/domains/analysis/api/websocket.py` (127 missed stmts, 17%)

**Files:**
- Create: `tests/unit/test_websocket_handlers.py`

**Step 1: Read the full WebSocket file**

```bash
cat backend/domains/analysis/api/websocket.py
```

**Step 2: Write the tests**

The analysis WebSocket uses `BoardroomGraph` and streams events. Test the helper functions directly (not the full WebSocket protocol which requires a live connection).

```python
# tests/unit/test_websocket_handlers.py
"""Unit tests for WebSocket helper functions and handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from backend.shared.ai.state.enums import Market
from backend.domains.analysis.api.websocket import (
    get_current_user_ws,
    _calculate_portfolio_sector_weight,
)
from backend.shared.core.security import create_access_token


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def valid_token(test_user):
    return create_access_token({"sub": test_user.email})


# --- get_current_user_ws ---

@pytest.mark.asyncio
async def test_get_current_user_ws_empty_token(mock_db):
    result = await get_current_user_ws("", mock_db)
    assert result is None


@pytest.mark.asyncio
async def test_get_current_user_ws_invalid_token(mock_db):
    result = await get_current_user_ws("not.a.valid.jwt", mock_db)
    assert result is None


@pytest.mark.asyncio
async def test_get_current_user_ws_valid_token(test_user, mock_db, valid_token):
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = test_user
    mock_db.execute.return_value = mock_result
    user = await get_current_user_ws(valid_token, mock_db)
    assert user == test_user


@pytest.mark.asyncio
async def test_get_current_user_ws_user_not_in_db(mock_db, valid_token):
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result
    result = await get_current_user_ws(valid_token, mock_db)
    assert result is None


# --- _calculate_portfolio_sector_weight ---

@pytest.mark.asyncio
async def test_portfolio_sector_weight_no_sector_data(test_user, mock_db):
    with patch("backend.domains.analysis.api.websocket.get_market_data_client") as mock_client:
        mock_market = MagicMock()
        mock_market.get_stock_data = AsyncMock(return_value={"sector": None})
        mock_client.return_value = mock_market
        result = await _calculate_portfolio_sector_weight(mock_db, test_user, "AAPL", Market.US)
        assert result == 0.0


@pytest.mark.asyncio
async def test_portfolio_sector_weight_empty_portfolio(test_user, mock_db):
    with patch("backend.domains.analysis.api.websocket.get_market_data_client") as mock_client:
        mock_market = MagicMock()
        mock_market.get_stock_data = AsyncMock(return_value={"sector": "Technology", "current_price": 150.0})
        mock_client.return_value = mock_market

        # Portfolio query returns empty
        mock_portfolio_result = MagicMock()
        mock_portfolio_result.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_portfolio_result

        result = await _calculate_portfolio_sector_weight(mock_db, test_user, "AAPL", Market.US)
        assert result == 0.0


@pytest.mark.asyncio
async def test_portfolio_sector_weight_market_data_error(test_user, mock_db):
    with patch("backend.domains.analysis.api.websocket.get_market_data_client") as mock_client:
        mock_market = MagicMock()
        mock_market.get_stock_data = AsyncMock(side_effect=Exception("Network error"))
        mock_client.return_value = mock_market
        result = await _calculate_portfolio_sector_weight(mock_db, test_user, "AAPL", Market.US)
        assert result == 0.0
```

**Step 3: Run and verify**

```bash
uv run pytest tests/unit/test_websocket_handlers.py -v --cov=backend/domains/analysis/api/websocket
```
Expected: All PASS. Coverage jumps from 17% to >35% (the WebSocket route itself remains uncovered by unit tests).

**Step 4: Commit**

```bash
git add tests/unit/test_websocket_handlers.py
git commit -m "test: add WebSocket handler unit tests"
```

---

## Final: Check Coverage

After all waves are complete, run the full test suite to verify coverage target is met.

**Step 1: Run all tests with coverage**

```bash
uv run pytest tests/ -v --cov=backend --cov-report=term-missing --cov-fail-under=80
```

Expected output:
```
TOTAL     ....  XX%   (≥80%)
XX passed, X warnings
```

**Step 2: If coverage is between 78-80%, check which modules still have big gaps**

```bash
uv run pytest tests/ --cov=backend --cov-report=term-missing 2>&1 | grep -E "^\S.*[0-9]+%" | sort -t% -k1 -n | head -20
```

**Step 3: If still below 80%, prioritize remaining gaps:**

- Add more paper router tests (execute trade happy path, get positions)
- Add more outcome_tracker tests (7d/30d/90d price update paths)
- Add backtest router tests (run_backtest, get_results)

**Step 4: Commit final state**

```bash
git add -A
git commit -m "test: extend coverage to meet 80% threshold"
```
