# tests/unit/test_services_schedule.py
"""Unit tests for ScheduleService."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.domains.notifications.services.schedule_exceptions import (
    ScheduleError,
    ScheduleNotFoundError,
    ScheduleRateLimitError,
)
from backend.domains.notifications.services.schedule_service import ScheduleService
from backend.shared.ai.state.enums import Market
from backend.shared.db.models import ScheduledAnalysis
from backend.shared.services.base import BaseService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
def mock_db():
    db = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def schedule_service(mock_schedule_dao):
    return ScheduleService(mock_schedule_dao)


@pytest.fixture
def sample_schedule():
    return ScheduledAnalysis(
        id=uuid4(),
        user_id=uuid4(),
        ticker="AAPL",
        market=Market.US,
        frequency="daily",
        active=True,
        created_at=datetime.now(),
    )


# ---------------------------------------------------------------------------
# Service initialisation
# ---------------------------------------------------------------------------


def test_dao_stored_on_service(mock_schedule_dao):
    """Constructor stores the DAO on the service instance."""
    service = ScheduleService(mock_schedule_dao)
    assert service.schedule_dao is mock_schedule_dao


def test_inherits_from_base_service(mock_schedule_dao):
    """ScheduleService inherits from BaseService."""
    service = ScheduleService(mock_schedule_dao)
    assert isinstance(service, BaseService)


def test_max_schedules_constant():
    """MAX_SCHEDULES_PER_USER constant is 50."""
    assert ScheduleService.MAX_SCHEDULES_PER_USER == 50


# ---------------------------------------------------------------------------
# create_scheduled_analysis
# ---------------------------------------------------------------------------


async def test_create_scheduled_analysis_success(
    schedule_service, mock_schedule_dao, mock_db, sample_schedule
):
    """Happy path: count < MAX, schedule created, db committed and refreshed."""
    user_id = uuid4()
    mock_schedule_dao.count_user_schedules.return_value = 0
    mock_schedule_dao.create.return_value = sample_schedule

    result = await schedule_service.create_scheduled_analysis(
        user_id=user_id,
        ticker="AAPL",
        market=Market.US,
        frequency="daily",
        db=mock_db,
    )

    assert result is sample_schedule
    mock_schedule_dao.count_user_schedules.assert_awaited_once_with(user_id)
    mock_schedule_dao.create.assert_awaited_once()
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once_with(sample_schedule)


async def test_create_scheduled_analysis_at_limit_minus_one(
    schedule_service, mock_schedule_dao, mock_db, sample_schedule
):
    """Count of 49 (one below MAX) allows creation."""
    mock_schedule_dao.count_user_schedules.return_value = 49
    mock_schedule_dao.create.return_value = sample_schedule

    result = await schedule_service.create_scheduled_analysis(
        user_id=uuid4(),
        ticker="TSLA",
        market=Market.US,
        frequency="weekly",
        db=mock_db,
    )

    assert result is sample_schedule
    mock_schedule_dao.create.assert_awaited_once()


async def test_create_scheduled_analysis_rate_limit_exact(
    schedule_service, mock_schedule_dao, mock_db
):
    """Count == MAX (50) raises ScheduleRateLimitError; create is NOT called."""
    mock_schedule_dao.count_user_schedules.return_value = 50

    with pytest.raises(ScheduleRateLimitError):
        await schedule_service.create_scheduled_analysis(
            user_id=uuid4(),
            ticker="AAPL",
            market=Market.US,
            frequency="daily",
            db=mock_db,
        )

    mock_schedule_dao.create.assert_not_awaited()
    mock_db.commit.assert_not_awaited()
    mock_db.rollback.assert_not_awaited()


async def test_create_scheduled_analysis_rate_limit_exceeded(
    schedule_service, mock_schedule_dao, mock_db
):
    """Count > MAX (51) also raises ScheduleRateLimitError; create is NOT called."""
    mock_schedule_dao.count_user_schedules.return_value = 51

    with pytest.raises(ScheduleRateLimitError):
        await schedule_service.create_scheduled_analysis(
            user_id=uuid4(),
            ticker="AAPL",
            market=Market.US,
            frequency="daily",
            db=mock_db,
        )

    mock_schedule_dao.create.assert_not_awaited()


async def test_create_scheduled_analysis_rate_limit_error_message(
    schedule_service, mock_schedule_dao, mock_db
):
    """ScheduleRateLimitError message includes the max schedule count."""
    mock_schedule_dao.count_user_schedules.return_value = 50

    with pytest.raises(ScheduleRateLimitError, match="50"):
        await schedule_service.create_scheduled_analysis(
            user_id=uuid4(),
            ticker="AAPL",
            market=Market.US,
            frequency="daily",
            db=mock_db,
        )


async def test_create_scheduled_analysis_dao_error_raises_schedule_error(
    schedule_service, mock_schedule_dao, mock_db
):
    """DAO create failure triggers rollback and wraps as ScheduleError."""
    mock_schedule_dao.count_user_schedules.return_value = 0
    mock_schedule_dao.create.side_effect = RuntimeError("DB write failed")

    with pytest.raises(ScheduleError, match="Failed to create schedule for AAPL"):
        await schedule_service.create_scheduled_analysis(
            user_id=uuid4(),
            ticker="AAPL",
            market=Market.US,
            frequency="daily",
            db=mock_db,
        )

    mock_db.rollback.assert_awaited_once()
    mock_db.commit.assert_not_awaited()


async def test_create_scheduled_analysis_dao_error_includes_ticker(
    schedule_service, mock_schedule_dao, mock_db
):
    """Error message includes the ticker symbol."""
    mock_schedule_dao.count_user_schedules.return_value = 0
    mock_schedule_dao.create.side_effect = Exception("timeout")

    with pytest.raises(ScheduleError, match="MSFT"):
        await schedule_service.create_scheduled_analysis(
            user_id=uuid4(),
            ticker="MSFT",
            market=Market.US,
            frequency="daily",
            db=mock_db,
        )


async def test_create_scheduled_analysis_passes_active_true(
    schedule_service, mock_schedule_dao, mock_db, sample_schedule
):
    """create is always called with active=True."""
    mock_schedule_dao.count_user_schedules.return_value = 0
    mock_schedule_dao.create.return_value = sample_schedule

    await schedule_service.create_scheduled_analysis(
        user_id=uuid4(),
        ticker="AAPL",
        market=Market.US,
        frequency="daily",
        db=mock_db,
    )

    call_kwargs = mock_schedule_dao.create.call_args.kwargs
    assert call_kwargs["active"] is True


async def test_create_scheduled_analysis_tase_market(
    schedule_service, mock_schedule_dao, mock_db, sample_schedule
):
    """TASE market is accepted without error."""
    mock_schedule_dao.count_user_schedules.return_value = 0
    mock_schedule_dao.create.return_value = sample_schedule

    result = await schedule_service.create_scheduled_analysis(
        user_id=uuid4(),
        ticker="TEVA",
        market=Market.TASE,
        frequency="daily",
        db=mock_db,
    )

    assert result is sample_schedule
    call_kwargs = mock_schedule_dao.create.call_args.kwargs
    assert call_kwargs["market"] == Market.TASE


async def test_create_scheduled_analysis_count_error_is_wrapped(
    schedule_service, mock_schedule_dao, mock_db
):
    """Exception from count_user_schedules triggers rollback and wraps as ScheduleError."""
    mock_schedule_dao.count_user_schedules.side_effect = RuntimeError(
        "count query failed"
    )

    with pytest.raises(ScheduleError):
        await schedule_service.create_scheduled_analysis(
            user_id=uuid4(),
            ticker="AAPL",
            market=Market.US,
            frequency="daily",
            db=mock_db,
        )

    mock_db.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# get_user_schedules
# ---------------------------------------------------------------------------


async def test_get_user_schedules_success(
    schedule_service, mock_schedule_dao, sample_schedule
):
    """Happy path: schedules returned from DAO."""
    user_id = uuid4()
    mock_schedule_dao.get_user_schedules.return_value = [sample_schedule]

    result = await schedule_service.get_user_schedules(user_id)

    assert result == [sample_schedule]
    mock_schedule_dao.get_user_schedules.assert_awaited_once_with(user_id)


async def test_get_user_schedules_empty(schedule_service, mock_schedule_dao):
    """Empty list is returned when user has no schedules."""
    user_id = uuid4()
    mock_schedule_dao.get_user_schedules.return_value = []

    result = await schedule_service.get_user_schedules(user_id)

    assert result == []


async def test_get_user_schedules_multiple(schedule_service, mock_schedule_dao):
    """Multiple schedules are returned correctly."""
    user_id = uuid4()
    schedules = [
        ScheduledAnalysis(
            id=uuid4(),
            user_id=user_id,
            ticker="AAPL",
            market=Market.US,
            frequency="daily",
            active=True,
            created_at=datetime.now(),
        ),
        ScheduledAnalysis(
            id=uuid4(),
            user_id=user_id,
            ticker="TSLA",
            market=Market.US,
            frequency="weekly",
            active=True,
            created_at=datetime.now(),
        ),
    ]
    mock_schedule_dao.get_user_schedules.return_value = schedules

    result = await schedule_service.get_user_schedules(user_id)

    assert len(result) == 2


async def test_get_user_schedules_dao_error(schedule_service, mock_schedule_dao):
    """Exception from DAO is wrapped as ScheduleError."""
    user_id = uuid4()
    mock_schedule_dao.get_user_schedules.side_effect = RuntimeError("query failed")

    with pytest.raises(ScheduleError, match="Failed to fetch schedules"):
        await schedule_service.get_user_schedules(user_id)


async def test_get_user_schedules_error_includes_user_id(
    schedule_service, mock_schedule_dao
):
    """Error message includes the user_id."""
    user_id = uuid4()
    mock_schedule_dao.get_user_schedules.side_effect = RuntimeError("timeout")

    with pytest.raises(ScheduleError, match=str(user_id)):
        await schedule_service.get_user_schedules(user_id)


# ---------------------------------------------------------------------------
# get_due_schedules
# ---------------------------------------------------------------------------


async def test_get_due_schedules_success(
    schedule_service, mock_schedule_dao, sample_schedule
):
    """Happy path: due schedules returned from DAO."""
    mock_schedule_dao.get_due_schedules.return_value = [sample_schedule]

    result = await schedule_service.get_due_schedules()

    assert result == [sample_schedule]
    mock_schedule_dao.get_due_schedules.assert_awaited_once()


async def test_get_due_schedules_empty(schedule_service, mock_schedule_dao):
    """Empty list returned when no schedules are due."""
    mock_schedule_dao.get_due_schedules.return_value = []

    result = await schedule_service.get_due_schedules()

    assert result == []


async def test_get_due_schedules_multiple(schedule_service, mock_schedule_dao):
    """Multiple due schedules are returned correctly."""
    schedules = [
        ScheduledAnalysis(
            id=uuid4(),
            user_id=uuid4(),
            ticker="AAPL",
            market=Market.US,
            frequency="daily",
            active=True,
            created_at=datetime.now(),
        ),
        ScheduledAnalysis(
            id=uuid4(),
            user_id=uuid4(),
            ticker="GOOGL",
            market=Market.US,
            frequency="on_change",
            active=True,
            created_at=datetime.now(),
        ),
    ]
    mock_schedule_dao.get_due_schedules.return_value = schedules

    result = await schedule_service.get_due_schedules()

    assert len(result) == 2


async def test_get_due_schedules_dao_error(schedule_service, mock_schedule_dao):
    """Exception from DAO is wrapped as ScheduleError."""
    mock_schedule_dao.get_due_schedules.side_effect = RuntimeError("connection lost")

    with pytest.raises(ScheduleError, match="Failed to fetch due schedules"):
        await schedule_service.get_due_schedules()


async def test_get_due_schedules_error_wraps_original_message(
    schedule_service, mock_schedule_dao
):
    """The ScheduleError wraps the original exception message."""
    mock_schedule_dao.get_due_schedules.side_effect = Exception("specific db error")

    with pytest.raises(ScheduleError, match="specific db error"):
        await schedule_service.get_due_schedules()


# ---------------------------------------------------------------------------
# update_run_times
# ---------------------------------------------------------------------------


async def test_update_run_times_success(
    schedule_service, mock_schedule_dao, mock_db, sample_schedule
):
    """Happy path: schedule found, updated, db committed."""
    schedule_id = uuid4()
    last_run = datetime.now()
    next_run = datetime.now() + timedelta(days=1)
    mock_schedule_dao.update_run_times.return_value = sample_schedule

    result = await schedule_service.update_run_times(
        schedule_id=schedule_id,
        last_run=last_run,
        next_run=next_run,
        db=mock_db,
    )

    assert result is sample_schedule
    mock_schedule_dao.update_run_times.assert_awaited_once_with(
        schedule_id, last_run, next_run
    )
    mock_db.commit.assert_awaited_once()
    mock_db.rollback.assert_not_awaited()


async def test_update_run_times_not_found_raises_schedule_not_found_error(
    schedule_service, mock_schedule_dao, mock_db
):
    """DAO returns None → ScheduleNotFoundError is raised."""
    schedule_id = uuid4()
    mock_schedule_dao.update_run_times.return_value = None

    with pytest.raises(ScheduleNotFoundError):
        await schedule_service.update_run_times(
            schedule_id=schedule_id,
            last_run=datetime.now(),
            next_run=datetime.now() + timedelta(days=1),
            db=mock_db,
        )


async def test_update_run_times_not_found_error_message(
    schedule_service, mock_schedule_dao, mock_db
):
    """ScheduleNotFoundError message includes the schedule_id."""
    schedule_id = uuid4()
    mock_schedule_dao.update_run_times.return_value = None

    with pytest.raises(ScheduleNotFoundError, match=str(schedule_id)):
        await schedule_service.update_run_times(
            schedule_id=schedule_id,
            last_run=datetime.now(),
            next_run=datetime.now() + timedelta(days=1),
            db=mock_db,
        )


async def test_update_run_times_not_found_does_not_commit(
    schedule_service, mock_schedule_dao, mock_db
):
    """When schedule is not found, commit is not called."""
    mock_schedule_dao.update_run_times.return_value = None

    with pytest.raises(ScheduleNotFoundError):
        await schedule_service.update_run_times(
            schedule_id=uuid4(),
            last_run=datetime.now(),
            next_run=datetime.now() + timedelta(days=1),
            db=mock_db,
        )

    mock_db.commit.assert_not_awaited()


async def test_update_run_times_not_found_propagates_as_is(
    schedule_service, mock_schedule_dao, mock_db
):
    """ScheduleNotFoundError propagates without being wrapped in ScheduleError."""
    mock_schedule_dao.update_run_times.return_value = None

    caught = None
    try:
        await schedule_service.update_run_times(
            schedule_id=uuid4(),
            last_run=datetime.now(),
            next_run=datetime.now() + timedelta(days=1),
            db=mock_db,
        )
    except ScheduleNotFoundError as e:
        caught = e

    assert caught is not None
    assert type(caught) is ScheduleNotFoundError


async def test_update_run_times_dao_error_triggers_rollback(
    schedule_service, mock_schedule_dao, mock_db
):
    """DAO exception triggers rollback and wraps as ScheduleError."""
    mock_schedule_dao.update_run_times.side_effect = RuntimeError(
        "constraint violation"
    )

    with pytest.raises(ScheduleError, match="Failed to update schedule"):
        await schedule_service.update_run_times(
            schedule_id=uuid4(),
            last_run=datetime.now(),
            next_run=datetime.now() + timedelta(days=1),
            db=mock_db,
        )

    mock_db.rollback.assert_awaited_once()
    mock_db.commit.assert_not_awaited()


async def test_update_run_times_dao_error_includes_schedule_id(
    schedule_service, mock_schedule_dao, mock_db
):
    """Error message includes the schedule_id."""
    schedule_id = uuid4()
    mock_schedule_dao.update_run_times.side_effect = Exception("timeout")

    with pytest.raises(ScheduleError, match=str(schedule_id)):
        await schedule_service.update_run_times(
            schedule_id=schedule_id,
            last_run=datetime.now(),
            next_run=datetime.now() + timedelta(days=1),
            db=mock_db,
        )


# ---------------------------------------------------------------------------
# toggle_schedule
# ---------------------------------------------------------------------------


async def test_toggle_schedule_activate_success(
    schedule_service, mock_schedule_dao, mock_db, sample_schedule
):
    """Happy path (active=True): schedule found, updated, db committed."""
    schedule_id = uuid4()
    updated_schedule = ScheduledAnalysis(
        id=schedule_id,
        user_id=uuid4(),
        ticker="AAPL",
        market=Market.US,
        frequency="daily",
        active=True,
        created_at=datetime.now(),
    )
    mock_schedule_dao.get_by_id.return_value = sample_schedule
    mock_schedule_dao.update.return_value = updated_schedule

    result = await schedule_service.toggle_schedule(
        schedule_id=schedule_id,
        active=True,
        db=mock_db,
    )

    assert result is updated_schedule
    mock_schedule_dao.get_by_id.assert_awaited_once_with(schedule_id)
    mock_schedule_dao.update.assert_awaited_once()
    mock_db.commit.assert_awaited_once()
    mock_db.rollback.assert_not_awaited()


async def test_toggle_schedule_deactivate_success(
    schedule_service, mock_schedule_dao, mock_db, sample_schedule
):
    """Happy path (active=False): schedule found, updated, db committed."""
    schedule_id = uuid4()
    updated_schedule = ScheduledAnalysis(
        id=schedule_id,
        user_id=uuid4(),
        ticker="AAPL",
        market=Market.US,
        frequency="daily",
        active=False,
        created_at=datetime.now(),
    )
    mock_schedule_dao.get_by_id.return_value = sample_schedule
    mock_schedule_dao.update.return_value = updated_schedule

    result = await schedule_service.toggle_schedule(
        schedule_id=schedule_id,
        active=False,
        db=mock_db,
    )

    assert result is updated_schedule
    assert sample_schedule.active is False  # active flag was set before update


async def test_toggle_schedule_sets_active_flag_on_object(
    schedule_service, mock_schedule_dao, mock_db, sample_schedule
):
    """The active attribute is set on the retrieved schedule object before update."""
    sample_schedule.active = True
    mock_schedule_dao.get_by_id.return_value = sample_schedule
    mock_schedule_dao.update.return_value = sample_schedule

    await schedule_service.toggle_schedule(
        schedule_id=uuid4(),
        active=False,
        db=mock_db,
    )

    assert sample_schedule.active is False


async def test_toggle_schedule_not_found_raises_schedule_not_found_error(
    schedule_service, mock_schedule_dao, mock_db
):
    """DAO returns None → ScheduleNotFoundError is raised."""
    mock_schedule_dao.get_by_id.return_value = None

    with pytest.raises(ScheduleNotFoundError):
        await schedule_service.toggle_schedule(
            schedule_id=uuid4(),
            active=True,
            db=mock_db,
        )


async def test_toggle_schedule_not_found_error_message(
    schedule_service, mock_schedule_dao, mock_db
):
    """ScheduleNotFoundError message includes the schedule_id."""
    schedule_id = uuid4()
    mock_schedule_dao.get_by_id.return_value = None

    with pytest.raises(ScheduleNotFoundError, match=str(schedule_id)):
        await schedule_service.toggle_schedule(
            schedule_id=schedule_id,
            active=True,
            db=mock_db,
        )


async def test_toggle_schedule_not_found_does_not_commit(
    schedule_service, mock_schedule_dao, mock_db
):
    """When schedule is not found, commit and update are not called."""
    mock_schedule_dao.get_by_id.return_value = None

    with pytest.raises(ScheduleNotFoundError):
        await schedule_service.toggle_schedule(
            schedule_id=uuid4(),
            active=True,
            db=mock_db,
        )

    mock_db.commit.assert_not_awaited()
    mock_schedule_dao.update.assert_not_awaited()


async def test_toggle_schedule_not_found_propagates_as_is(
    schedule_service, mock_schedule_dao, mock_db
):
    """ScheduleNotFoundError propagates without being wrapped in ScheduleError."""
    mock_schedule_dao.get_by_id.return_value = None

    caught = None
    try:
        await schedule_service.toggle_schedule(
            schedule_id=uuid4(),
            active=True,
            db=mock_db,
        )
    except ScheduleNotFoundError as e:
        caught = e

    assert caught is not None
    assert type(caught) is ScheduleNotFoundError


async def test_toggle_schedule_dao_update_error_triggers_rollback(
    schedule_service, mock_schedule_dao, mock_db, sample_schedule
):
    """DAO update failure triggers rollback and wraps as ScheduleError."""
    mock_schedule_dao.get_by_id.return_value = sample_schedule
    mock_schedule_dao.update.side_effect = RuntimeError("update failed")

    with pytest.raises(ScheduleError, match="Failed to toggle schedule"):
        await schedule_service.toggle_schedule(
            schedule_id=uuid4(),
            active=True,
            db=mock_db,
        )

    mock_db.rollback.assert_awaited_once()
    mock_db.commit.assert_not_awaited()


async def test_toggle_schedule_dao_get_error_triggers_rollback(
    schedule_service, mock_schedule_dao, mock_db
):
    """DAO get_by_id failure triggers rollback and wraps as ScheduleError."""
    mock_schedule_dao.get_by_id.side_effect = RuntimeError("connection reset")

    with pytest.raises(ScheduleError):
        await schedule_service.toggle_schedule(
            schedule_id=uuid4(),
            active=True,
            db=mock_db,
        )

    mock_db.rollback.assert_awaited_once()


async def test_toggle_schedule_dao_error_includes_schedule_id(
    schedule_service, mock_schedule_dao, mock_db
):
    """Error message includes the schedule_id."""
    schedule_id = uuid4()
    mock_schedule_dao.get_by_id.side_effect = Exception("timeout")

    with pytest.raises(ScheduleError, match=str(schedule_id)):
        await schedule_service.toggle_schedule(
            schedule_id=schedule_id,
            active=True,
            db=mock_db,
        )


# ---------------------------------------------------------------------------
# delete_schedule
# ---------------------------------------------------------------------------


async def test_delete_schedule_success_returns_true(
    schedule_service, mock_schedule_dao, mock_db
):
    """Happy path: DAO returns True, db committed."""
    schedule_id = uuid4()
    mock_schedule_dao.delete.return_value = True

    result = await schedule_service.delete_schedule(
        schedule_id=schedule_id,
        db=mock_db,
    )

    assert result is True
    mock_schedule_dao.delete.assert_awaited_once_with(schedule_id)
    mock_db.commit.assert_awaited_once()
    mock_db.rollback.assert_not_awaited()


async def test_delete_schedule_not_found_returns_false(
    schedule_service, mock_schedule_dao, mock_db
):
    """DAO returns False (not found), db still committed."""
    mock_schedule_dao.delete.return_value = False

    result = await schedule_service.delete_schedule(
        schedule_id=uuid4(),
        db=mock_db,
    )

    assert result is False
    mock_db.commit.assert_awaited_once()


async def test_delete_schedule_dao_error_triggers_rollback(
    schedule_service, mock_schedule_dao, mock_db
):
    """DAO delete failure triggers rollback and wraps as ScheduleError."""
    schedule_id = uuid4()
    mock_schedule_dao.delete.side_effect = RuntimeError("foreign key violation")

    with pytest.raises(ScheduleError, match="Failed to delete schedule"):
        await schedule_service.delete_schedule(
            schedule_id=schedule_id,
            db=mock_db,
        )

    mock_db.rollback.assert_awaited_once()
    mock_db.commit.assert_not_awaited()


async def test_delete_schedule_dao_error_includes_schedule_id(
    schedule_service, mock_schedule_dao, mock_db
):
    """Error message includes the schedule_id."""
    schedule_id = uuid4()
    mock_schedule_dao.delete.side_effect = Exception("timeout")

    with pytest.raises(ScheduleError, match=str(schedule_id)):
        await schedule_service.delete_schedule(
            schedule_id=schedule_id,
            db=mock_db,
        )


async def test_delete_schedule_wraps_original_exception_message(
    schedule_service, mock_schedule_dao, mock_db
):
    """The ScheduleError wraps the original exception message."""
    mock_schedule_dao.delete.side_effect = Exception("unique constraint violation")

    with pytest.raises(ScheduleError, match="unique constraint violation"):
        await schedule_service.delete_schedule(
            schedule_id=uuid4(),
            db=mock_db,
        )
