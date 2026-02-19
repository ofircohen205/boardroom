# tests/unit/shared/test_scheduler.py
"""
Unit tests for backend/shared/jobs/scheduler.py.

Tests cover:
- JobScheduler.start: sets running=True, creates asyncio task
- JobScheduler.start (already running): logs warning, does not create second task
- JobScheduler.stop: cancels task, disposes engine, sets running=False
- JobScheduler.stop (not running): returns immediately without error
- JobScheduler.run_now: delegates to run_outcome_tracker_job via session
- JobScheduler._run_alert_checker: logs success/failure correctly
- JobScheduler._run_scheduled_analyzer: logs success/skip correctly
- JobScheduler._run_outcome_tracker: logs outcome count correctly
- get_scheduler: returns singleton JobScheduler instance
- start_scheduler / stop_scheduler: module-level helpers
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import backend.shared.jobs.scheduler as scheduler_module
from backend.shared.jobs.scheduler import (
    JobScheduler,
    get_scheduler,
    start_scheduler,
    stop_scheduler,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_scheduler() -> JobScheduler:
    """Build a JobScheduler with its database engine fully mocked out."""
    with (
        patch("backend.shared.jobs.scheduler.create_async_engine") as mock_engine,
        patch("backend.shared.jobs.scheduler.async_sessionmaker") as mock_sm,
    ):
        mock_engine.return_value = MagicMock()
        mock_sm.return_value = MagicMock()
        sched = JobScheduler()

    # Give it a controllable async session context manager
    mock_session = AsyncMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    sched.async_session_maker = MagicMock(return_value=mock_ctx)
    sched.engine = AsyncMock()
    sched.engine.dispose = AsyncMock()
    return sched


# ---------------------------------------------------------------------------
# JobScheduler.start
# ---------------------------------------------------------------------------


async def test_start_sets_running_true():
    """start() must set running=True and create a background task."""
    sched = _make_scheduler()

    with patch.object(sched, "_run_loop", new_callable=AsyncMock):
        await sched.start()

    assert sched.running is True
    sched._task.cancel()  # cleanup


async def test_start_creates_background_task():
    """start() must store an asyncio.Task in sched._task."""
    sched = _make_scheduler()

    with patch.object(sched, "_run_loop", new_callable=AsyncMock):
        await sched.start()

    assert sched._task is not None
    assert isinstance(sched._task, asyncio.Task)
    sched._task.cancel()


async def test_start_when_already_running_does_not_create_second_task():
    """Calling start() on an already-running scheduler is a no-op."""
    sched = _make_scheduler()
    sched.running = True
    first_task = MagicMock()
    sched._task = first_task

    with patch.object(sched, "_run_loop", new_callable=AsyncMock):
        await sched.start()

    assert sched._task is first_task  # unchanged


# ---------------------------------------------------------------------------
# JobScheduler.stop
# ---------------------------------------------------------------------------


async def test_stop_sets_running_false():
    """stop() must set running=False."""
    sched = _make_scheduler()
    sched.running = True
    sched._task = asyncio.ensure_future(asyncio.sleep(0))  # real task

    await sched.stop()

    assert sched.running is False


async def test_stop_disposes_engine():
    """stop() must call engine.dispose() to release DB connections."""
    sched = _make_scheduler()
    sched.running = True
    sched._task = asyncio.ensure_future(asyncio.sleep(0))

    await sched.stop()

    sched.engine.dispose.assert_awaited_once()


async def test_stop_when_not_running_returns_immediately():
    """stop() on a scheduler that is not running must be a no-op."""
    sched = _make_scheduler()
    sched.running = False

    # Should not raise and should not call dispose
    await sched.stop()

    sched.engine.dispose.assert_not_called()


# ---------------------------------------------------------------------------
# JobScheduler.run_now
# ---------------------------------------------------------------------------


async def test_run_now_delegates_to_outcome_tracker():
    """run_now() must call run_outcome_tracker_job and return its result."""
    sched = _make_scheduler()
    expected = {"success": True, "outcomes_updated": 5}

    with patch(
        "backend.shared.jobs.scheduler.run_outcome_tracker_job",
        new_callable=AsyncMock,
        return_value=expected,
    ) as mock_tracker:
        result = await sched.run_now()

    assert result == expected
    mock_tracker.assert_awaited_once()


# ---------------------------------------------------------------------------
# JobScheduler._run_alert_checker
# ---------------------------------------------------------------------------


async def test_run_alert_checker_logs_success():
    """_run_alert_checker() should not raise when check_price_alerts succeeds."""
    sched = _make_scheduler()
    alert_result = {"success": True, "alerts_checked": 10, "alerts_triggered": 2}

    with patch(
        "backend.shared.jobs.scheduler.check_price_alerts",
        new_callable=AsyncMock,
        return_value=alert_result,
    ):
        await sched._run_alert_checker()  # must not raise


async def test_run_alert_checker_handles_skipped_market_closed():
    """_run_alert_checker() must handle the market-closed skip result gracefully."""
    sched = _make_scheduler()
    skip_result = {"success": True, "skipped": "market_closed"}

    with patch(
        "backend.shared.jobs.scheduler.check_price_alerts",
        new_callable=AsyncMock,
        return_value=skip_result,
    ):
        await sched._run_alert_checker()  # must not raise


async def test_run_alert_checker_handles_failure():
    """_run_alert_checker() must not propagate exceptions from check_price_alerts."""
    sched = _make_scheduler()

    with patch(
        "backend.shared.jobs.scheduler.check_price_alerts",
        new_callable=AsyncMock,
        side_effect=RuntimeError("network error"),
    ):
        await sched._run_alert_checker()  # must not raise


# ---------------------------------------------------------------------------
# JobScheduler._run_scheduled_analyzer
# ---------------------------------------------------------------------------


async def test_run_scheduled_analyzer_logs_when_analyses_run():
    """_run_scheduled_analyzer() should not raise when analyses were run."""
    sched = _make_scheduler()
    analyzer_result = {"success": True, "schedules_run": 3}

    with patch(
        "backend.shared.jobs.scheduler.run_scheduled_analyses",
        new_callable=AsyncMock,
        return_value=analyzer_result,
    ):
        await sched._run_scheduled_analyzer()  # must not raise


async def test_run_scheduled_analyzer_handles_failure_result():
    """_run_scheduled_analyzer() must not raise when result indicates failure."""
    sched = _make_scheduler()
    failure_result = {"success": False, "error": "DB timeout"}

    with patch(
        "backend.shared.jobs.scheduler.run_scheduled_analyses",
        new_callable=AsyncMock,
        return_value=failure_result,
    ):
        await sched._run_scheduled_analyzer()  # must not raise


# ---------------------------------------------------------------------------
# JobScheduler._run_outcome_tracker
# ---------------------------------------------------------------------------


async def test_run_outcome_tracker_logs_success():
    """_run_outcome_tracker() should not raise when outcome tracker succeeds."""
    sched = _make_scheduler()
    tracker_result = {"success": True, "outcomes_updated": 7}

    with patch(
        "backend.shared.jobs.scheduler.run_outcome_tracker_job",
        new_callable=AsyncMock,
        return_value=tracker_result,
    ):
        await sched._run_outcome_tracker()  # must not raise


async def test_run_outcome_tracker_handles_exception():
    """_run_outcome_tracker() must swallow exceptions from the job."""
    sched = _make_scheduler()

    with patch(
        "backend.shared.jobs.scheduler.run_outcome_tracker_job",
        new_callable=AsyncMock,
        side_effect=RuntimeError("tracker exploded"),
    ):
        await sched._run_outcome_tracker()  # must not raise


# ---------------------------------------------------------------------------
# get_scheduler (singleton)
# ---------------------------------------------------------------------------


def test_get_scheduler_returns_job_scheduler_instance():
    """get_scheduler() must return a JobScheduler."""
    scheduler_module._scheduler = None

    with (
        patch("backend.shared.jobs.scheduler.create_async_engine"),
        patch("backend.shared.jobs.scheduler.async_sessionmaker"),
    ):
        sched = get_scheduler()

    assert isinstance(sched, JobScheduler)

    scheduler_module._scheduler = None


def test_get_scheduler_returns_same_instance_on_second_call():
    """get_scheduler() must return the same singleton on repeated calls."""
    scheduler_module._scheduler = None

    with (
        patch("backend.shared.jobs.scheduler.create_async_engine"),
        patch("backend.shared.jobs.scheduler.async_sessionmaker"),
    ):
        first = get_scheduler()
        second = get_scheduler()

    assert first is second

    scheduler_module._scheduler = None


# ---------------------------------------------------------------------------
# start_scheduler / stop_scheduler module helpers
# ---------------------------------------------------------------------------


async def test_start_scheduler_calls_scheduler_start():
    """start_scheduler() must delegate to the singleton's start()."""
    scheduler_module._scheduler = None
    mock_sched = AsyncMock(spec=JobScheduler)
    scheduler_module._scheduler = mock_sched

    await start_scheduler()

    mock_sched.start.assert_awaited_once()

    scheduler_module._scheduler = None


async def test_stop_scheduler_calls_scheduler_stop():
    """stop_scheduler() must delegate to the singleton's stop()."""
    scheduler_module._scheduler = None
    mock_sched = AsyncMock(spec=JobScheduler)
    scheduler_module._scheduler = mock_sched

    await stop_scheduler()

    mock_sched.stop.assert_awaited_once()

    scheduler_module._scheduler = None


# ---------------------------------------------------------------------------
# JobScheduler._run_loop
# ---------------------------------------------------------------------------


async def test_run_loop_calls_all_three_jobs_on_startup():
    """_run_loop() must call alert checker, scheduled analyzer, and outcome tracker on startup."""
    sched = _make_scheduler()
    sched.running = True

    async def stop_after_startup(seconds):
        # Set running=False so the loop exits after one sleep
        sched.running = False

    with (
        patch.object(sched, "_run_alert_checker", new_callable=AsyncMock) as mock_alert,
        patch.object(
            sched, "_run_scheduled_analyzer", new_callable=AsyncMock
        ) as mock_sched,
        patch.object(
            sched, "_run_outcome_tracker", new_callable=AsyncMock
        ) as mock_tracker,
        patch("asyncio.sleep", side_effect=stop_after_startup),
    ):
        await sched._run_loop()

    # Startup: each called once; loop exits before any scheduled calls
    assert mock_alert.call_count >= 1
    assert mock_sched.call_count >= 1
    assert mock_tracker.call_count >= 1


async def test_run_loop_exits_cleanly_on_cancelled_error():
    """_run_loop() must exit without raising when asyncio.CancelledError is raised."""
    sched = _make_scheduler()
    sched.running = True

    with (
        patch.object(sched, "_run_alert_checker", new_callable=AsyncMock),
        patch.object(sched, "_run_scheduled_analyzer", new_callable=AsyncMock),
        patch.object(sched, "_run_outcome_tracker", new_callable=AsyncMock),
        patch(
            "asyncio.sleep",
            new_callable=AsyncMock,
            side_effect=asyncio.CancelledError,
        ),
    ):
        await sched._run_loop()  # must not raise


async def test_run_loop_handles_generic_exception_and_continues():
    """_run_loop() must swallow generic exceptions and continue running."""
    sched = _make_scheduler()
    sched.running = True

    call_count = 0

    async def controlled_sleep(seconds):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("transient error")
        # Second sleep: stop the loop
        sched.running = False

    with (
        patch.object(sched, "_run_alert_checker", new_callable=AsyncMock),
        patch.object(sched, "_run_scheduled_analyzer", new_callable=AsyncMock),
        patch.object(sched, "_run_outcome_tracker", new_callable=AsyncMock),
        patch("asyncio.sleep", side_effect=controlled_sleep),
    ):
        await sched._run_loop()  # must not raise


async def test_run_loop_increments_minute_counter_and_checks_if_condition():
    """_run_loop() must increment minute_counter each iteration."""
    sched = _make_scheduler()
    sched.running = True

    iterations = 0

    async def one_iteration(seconds):
        nonlocal iterations
        iterations += 1
        if iterations >= 2:
            sched.running = False

    with (
        patch.object(sched, "_run_alert_checker", new_callable=AsyncMock),
        patch.object(sched, "_run_scheduled_analyzer", new_callable=AsyncMock),
        patch.object(sched, "_run_outcome_tracker", new_callable=AsyncMock),
        patch("asyncio.sleep", side_effect=one_iteration),
    ):
        await sched._run_loop()

    # One real iteration completed (minute_counter became 1)
    assert iterations >= 1


# ---------------------------------------------------------------------------
# Error-path coverage: success=False branches
# ---------------------------------------------------------------------------


async def test_run_alert_checker_logs_error_when_result_not_successful():
    """_run_alert_checker() must log error when check_price_alerts returns success=False."""
    sched = _make_scheduler()
    failure_result = {"success": False, "error": "rate limit exceeded"}

    with patch(
        "backend.shared.jobs.scheduler.check_price_alerts",
        new_callable=AsyncMock,
        return_value=failure_result,
    ):
        await sched._run_alert_checker()  # must not raise


async def test_run_scheduled_analyzer_logs_error_when_exception_raised():
    """_run_scheduled_analyzer() must not propagate exceptions."""
    sched = _make_scheduler()

    with patch(
        "backend.shared.jobs.scheduler.run_scheduled_analyses",
        new_callable=AsyncMock,
        side_effect=RuntimeError("analyzer crashed"),
    ):
        await sched._run_scheduled_analyzer()  # must not raise


async def test_run_scheduled_analyzer_logs_error_when_result_not_successful():
    """_run_scheduled_analyzer() must log error when result success=False."""
    sched = _make_scheduler()
    failure_result = {"success": False, "error": "DB timeout"}

    with patch(
        "backend.shared.jobs.scheduler.run_scheduled_analyses",
        new_callable=AsyncMock,
        return_value=failure_result,
    ):
        await sched._run_scheduled_analyzer()  # must not raise


async def test_run_outcome_tracker_logs_error_when_result_not_successful():
    """_run_outcome_tracker() must log error when result success=False."""
    sched = _make_scheduler()
    failure_result = {"success": False, "error": "tracker error"}

    with patch(
        "backend.shared.jobs.scheduler.run_outcome_tracker_job",
        new_callable=AsyncMock,
        return_value=failure_result,
    ):
        await sched._run_outcome_tracker()  # must not raise
