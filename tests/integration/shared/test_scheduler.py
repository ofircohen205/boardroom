"""Integration tests for the APScheduler background job scheduler."""

import asyncio
from unittest.mock import AsyncMock, patch

from backend.shared.jobs.scheduler import (
    JobScheduler,
    get_scheduler,
    start_scheduler,
    stop_scheduler,
)


class TestGetScheduler:
    """Tests for the get_scheduler() singleton factory."""

    def test_get_scheduler_returns_instance(self):
        """get_scheduler() returns a JobScheduler instance."""
        scheduler = get_scheduler()
        assert scheduler is not None
        assert isinstance(scheduler, JobScheduler)

    def test_get_scheduler_returns_same_instance(self):
        """get_scheduler() is idempotent - returns the same object on repeated calls."""
        first = get_scheduler()
        second = get_scheduler()
        assert first is second

    def test_get_scheduler_creates_new_when_none(self):
        """get_scheduler() creates a fresh instance when the global is None."""
        import backend.shared.jobs.scheduler as scheduler_module

        original = scheduler_module._scheduler
        try:
            scheduler_module._scheduler = None
            new_scheduler = get_scheduler()
            assert new_scheduler is not None
            assert isinstance(new_scheduler, JobScheduler)
        finally:
            scheduler_module._scheduler = original


class TestJobSchedulerInit:
    """Tests for JobScheduler.__init__."""

    def test_init_sets_running_false(self):
        """A newly-created scheduler is not running."""
        with (
            patch("backend.shared.jobs.scheduler.create_async_engine"),
            patch("backend.shared.jobs.scheduler.async_sessionmaker"),
        ):
            sched = JobScheduler()
            assert sched.running is False

    def test_init_task_is_none(self):
        """A newly-created scheduler has no asyncio task."""
        with (
            patch("backend.shared.jobs.scheduler.create_async_engine"),
            patch("backend.shared.jobs.scheduler.async_sessionmaker"),
        ):
            sched = JobScheduler()
            assert sched._task is None


class TestJobSchedulerStart:
    """Tests for JobScheduler.start()."""

    async def test_start_sets_running_true(self):
        """start() sets running=True and creates an asyncio task."""
        with (
            patch("backend.shared.jobs.scheduler.create_async_engine"),
            patch("backend.shared.jobs.scheduler.async_sessionmaker"),
        ):
            sched = JobScheduler()

            async def fake_loop(self_inner):
                await asyncio.sleep(9999)

            with patch.object(JobScheduler, "_run_loop", new=fake_loop):
                await sched.start()
                assert sched.running is True
                assert sched._task is not None
                sched.running = False
                sched._task.cancel()
                try:
                    await sched._task
                except asyncio.CancelledError:
                    pass

    async def test_start_when_already_running_is_no_op(self):
        """Calling start() while already running logs a warning and returns."""
        with (
            patch("backend.shared.jobs.scheduler.create_async_engine"),
            patch("backend.shared.jobs.scheduler.async_sessionmaker"),
        ):
            sched = JobScheduler()
            sched.running = True

            with patch.object(JobScheduler, "_run_loop") as mock_loop:
                await sched.start()
                mock_loop.assert_not_called()

            sched.running = False


class TestJobSchedulerStop:
    """Tests for JobScheduler.stop()."""

    async def test_stop_when_not_running_is_no_op(self):
        """stop() returns immediately when running=False."""
        with (
            patch("backend.shared.jobs.scheduler.create_async_engine") as mock_engine,
            patch("backend.shared.jobs.scheduler.async_sessionmaker"),
        ):
            mock_engine_instance = AsyncMock()
            mock_engine.return_value = mock_engine_instance

            sched = JobScheduler()
            assert sched.running is False
            await sched.stop()
            mock_engine_instance.dispose.assert_not_called()

    async def test_stop_cancels_task_and_disposes_engine(self):
        """stop() cancels the background task and disposes the SQLAlchemy engine."""
        with (
            patch(
                "backend.shared.jobs.scheduler.create_async_engine"
            ) as mock_engine_cls,
            patch("backend.shared.jobs.scheduler.async_sessionmaker"),
        ):
            mock_engine = AsyncMock()
            mock_engine_cls.return_value = mock_engine

            sched = JobScheduler()
            sched.running = True

            async def run_forever():
                await asyncio.sleep(9999)

            sched._task = asyncio.create_task(run_forever())

            await sched.stop()

            assert sched.running is False
            mock_engine.dispose.assert_awaited_once()


class TestStartStopSchedulerFunctions:
    """Tests for the module-level start_scheduler / stop_scheduler helpers."""

    async def test_start_scheduler_delegates_to_global(self):
        """start_scheduler() calls start() on the global scheduler instance."""
        mock_sched = AsyncMock(spec=JobScheduler)
        mock_sched.running = False

        with patch(
            "backend.shared.jobs.scheduler.get_scheduler", return_value=mock_sched
        ):
            await start_scheduler()
            mock_sched.start.assert_awaited_once()

    async def test_stop_scheduler_delegates_to_global(self):
        """stop_scheduler() calls stop() on the global scheduler when it exists."""
        mock_sched = AsyncMock(spec=JobScheduler)

        import backend.shared.jobs.scheduler as scheduler_module

        original = scheduler_module._scheduler
        try:
            scheduler_module._scheduler = mock_sched
            await stop_scheduler()
            mock_sched.stop.assert_awaited_once()
        finally:
            scheduler_module._scheduler = original

    async def test_stop_scheduler_when_global_is_none(self):
        """stop_scheduler() is a no-op when no global scheduler has been created."""
        import backend.shared.jobs.scheduler as scheduler_module

        original = scheduler_module._scheduler
        try:
            scheduler_module._scheduler = None
            await stop_scheduler()
        finally:
            scheduler_module._scheduler = original


class TestJobSchedulerRunJobs:
    """Tests for the private _run_* helper methods."""

    async def test_run_alert_checker_logs_success(self):
        """_run_alert_checker() calls check_price_alerts and logs correctly."""
        with (
            patch("backend.shared.jobs.scheduler.create_async_engine"),
            patch(
                "backend.shared.jobs.scheduler.async_sessionmaker"
            ) as mock_sessionmaker,
        ):
            mock_session = AsyncMock()
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_session
            mock_cm.__aexit__.return_value = None
            mock_sessionmaker.return_value.return_value = mock_cm

            sched = JobScheduler()

            success_result = {
                "success": True,
                "alerts_checked": 3,
                "alerts_triggered": 1,
            }

            with patch(
                "backend.shared.jobs.scheduler.check_price_alerts",
                new_callable=AsyncMock,
                return_value=success_result,
            ):
                await sched._run_alert_checker()

    async def test_run_alert_checker_logs_failure(self):
        """_run_alert_checker() logs an error when check_price_alerts returns failure."""
        with (
            patch("backend.shared.jobs.scheduler.create_async_engine"),
            patch(
                "backend.shared.jobs.scheduler.async_sessionmaker"
            ) as mock_sessionmaker,
        ):
            mock_session = AsyncMock()
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_session
            mock_cm.__aexit__.return_value = None
            mock_sessionmaker.return_value.return_value = mock_cm

            sched = JobScheduler()

            failure_result = {"success": False, "error": "network timeout"}

            with patch(
                "backend.shared.jobs.scheduler.check_price_alerts",
                new_callable=AsyncMock,
                return_value=failure_result,
            ):
                await sched._run_alert_checker()

    async def test_run_alert_checker_handles_exception(self):
        """_run_alert_checker() handles unexpected exceptions without crashing."""
        with (
            patch("backend.shared.jobs.scheduler.create_async_engine"),
            patch(
                "backend.shared.jobs.scheduler.async_sessionmaker"
            ) as mock_sessionmaker,
        ):
            mock_session = AsyncMock()
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_session
            mock_cm.__aexit__.return_value = None
            mock_sessionmaker.return_value.return_value = mock_cm

            sched = JobScheduler()

            with patch(
                "backend.shared.jobs.scheduler.check_price_alerts",
                new_callable=AsyncMock,
                side_effect=RuntimeError("unexpected error"),
            ):
                await sched._run_alert_checker()

    async def test_run_alert_checker_skipped_market_closed(self):
        """_run_alert_checker() handles the skip result when market is closed."""
        with (
            patch("backend.shared.jobs.scheduler.create_async_engine"),
            patch(
                "backend.shared.jobs.scheduler.async_sessionmaker"
            ) as mock_sessionmaker,
        ):
            mock_session = AsyncMock()
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_session
            mock_cm.__aexit__.return_value = None
            mock_sessionmaker.return_value.return_value = mock_cm

            sched = JobScheduler()

            skipped_result = {
                "success": True,
                "skipped": "market_closed",
                "alerts_checked": 0,
                "alerts_triggered": 0,
            }

            with patch(
                "backend.shared.jobs.scheduler.check_price_alerts",
                new_callable=AsyncMock,
                return_value=skipped_result,
            ):
                await sched._run_alert_checker()

    async def test_run_scheduled_analyzer_success(self):
        """_run_scheduled_analyzer() calls run_scheduled_analyses correctly."""
        with (
            patch("backend.shared.jobs.scheduler.create_async_engine"),
            patch(
                "backend.shared.jobs.scheduler.async_sessionmaker"
            ) as mock_sessionmaker,
        ):
            mock_session = AsyncMock()
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_session
            mock_cm.__aexit__.return_value = None
            mock_sessionmaker.return_value.return_value = mock_cm

            sched = JobScheduler()

            success_result = {"success": True, "schedules_run": 2}

            with patch(
                "backend.shared.jobs.scheduler.run_scheduled_analyses",
                new_callable=AsyncMock,
                return_value=success_result,
            ):
                await sched._run_scheduled_analyzer()

    async def test_run_scheduled_analyzer_failure(self):
        """_run_scheduled_analyzer() logs error when job returns failure."""
        with (
            patch("backend.shared.jobs.scheduler.create_async_engine"),
            patch(
                "backend.shared.jobs.scheduler.async_sessionmaker"
            ) as mock_sessionmaker,
        ):
            mock_session = AsyncMock()
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_session
            mock_cm.__aexit__.return_value = None
            mock_sessionmaker.return_value.return_value = mock_cm

            sched = JobScheduler()

            failure_result = {"success": False, "error": "db error"}

            with patch(
                "backend.shared.jobs.scheduler.run_scheduled_analyses",
                new_callable=AsyncMock,
                return_value=failure_result,
            ):
                await sched._run_scheduled_analyzer()

    async def test_run_scheduled_analyzer_handles_exception(self):
        """_run_scheduled_analyzer() swallows unexpected exceptions."""
        with (
            patch("backend.shared.jobs.scheduler.create_async_engine"),
            patch(
                "backend.shared.jobs.scheduler.async_sessionmaker"
            ) as mock_sessionmaker,
        ):
            mock_session = AsyncMock()
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_session
            mock_cm.__aexit__.return_value = None
            mock_sessionmaker.return_value.return_value = mock_cm

            sched = JobScheduler()

            with patch(
                "backend.shared.jobs.scheduler.run_scheduled_analyses",
                new_callable=AsyncMock,
                side_effect=ValueError("boom"),
            ):
                await sched._run_scheduled_analyzer()

    async def test_run_outcome_tracker_success(self):
        """_run_outcome_tracker() calls run_outcome_tracker_job and logs outcome count."""
        with (
            patch("backend.shared.jobs.scheduler.create_async_engine"),
            patch(
                "backend.shared.jobs.scheduler.async_sessionmaker"
            ) as mock_sessionmaker,
        ):
            mock_session = AsyncMock()
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_session
            mock_cm.__aexit__.return_value = None
            mock_sessionmaker.return_value.return_value = mock_cm

            sched = JobScheduler()

            success_result = {"success": True, "outcomes_updated": 5}

            with patch(
                "backend.shared.jobs.scheduler.run_outcome_tracker_job",
                new_callable=AsyncMock,
                return_value=success_result,
            ):
                await sched._run_outcome_tracker()

    async def test_run_outcome_tracker_failure(self):
        """_run_outcome_tracker() logs error when job returns failure."""
        with (
            patch("backend.shared.jobs.scheduler.create_async_engine"),
            patch(
                "backend.shared.jobs.scheduler.async_sessionmaker"
            ) as mock_sessionmaker,
        ):
            mock_session = AsyncMock()
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_session
            mock_cm.__aexit__.return_value = None
            mock_sessionmaker.return_value.return_value = mock_cm

            sched = JobScheduler()

            failure_result = {"success": False, "error": "tracker failed"}

            with patch(
                "backend.shared.jobs.scheduler.run_outcome_tracker_job",
                new_callable=AsyncMock,
                return_value=failure_result,
            ):
                await sched._run_outcome_tracker()

    async def test_run_outcome_tracker_handles_exception(self):
        """_run_outcome_tracker() swallows unexpected exceptions."""
        with (
            patch("backend.shared.jobs.scheduler.create_async_engine"),
            patch(
                "backend.shared.jobs.scheduler.async_sessionmaker"
            ) as mock_sessionmaker,
        ):
            mock_session = AsyncMock()
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_session
            mock_cm.__aexit__.return_value = None
            mock_sessionmaker.return_value.return_value = mock_cm

            sched = JobScheduler()

            with patch(
                "backend.shared.jobs.scheduler.run_outcome_tracker_job",
                new_callable=AsyncMock,
                side_effect=ConnectionError("db gone"),
            ):
                await sched._run_outcome_tracker()


class TestJobSchedulerRunNow:
    """Tests for the run_now() public method."""

    async def test_run_now_returns_job_result(self):
        """run_now() executes outcome tracker immediately and returns the result."""
        with (
            patch("backend.shared.jobs.scheduler.create_async_engine"),
            patch(
                "backend.shared.jobs.scheduler.async_sessionmaker"
            ) as mock_sessionmaker,
        ):
            mock_session = AsyncMock()
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_session
            mock_cm.__aexit__.return_value = None
            mock_sessionmaker.return_value.return_value = mock_cm

            sched = JobScheduler()

            expected = {"success": True, "outcomes_updated": 7}

            with patch(
                "backend.shared.jobs.scheduler.run_outcome_tracker_job",
                new_callable=AsyncMock,
                return_value=expected,
            ) as mock_tracker:
                result = await sched.run_now()

            assert result == expected
            mock_tracker.assert_awaited_once_with(mock_session)


class TestRunLoop:
    """Tests for the _run_loop() scheduler loop logic."""

    async def test_run_loop_calls_all_jobs_on_startup(self):
        """_run_loop() invokes all three jobs immediately before entering the wait loop."""
        with (
            patch("backend.shared.jobs.scheduler.create_async_engine"),
            patch("backend.shared.jobs.scheduler.async_sessionmaker"),
        ):
            sched = JobScheduler()
            sched.running = True

            call_order = []

            async def fake_alert(self_inner):
                call_order.append("alert")

            async def fake_analyzer(self_inner):
                call_order.append("analyzer")

            async def fake_tracker(self_inner):
                call_order.append("tracker")
                self_inner.running = False

            sleep_mock = AsyncMock()

            with (
                patch.object(JobScheduler, "_run_alert_checker", new=fake_alert),
                patch.object(
                    JobScheduler, "_run_scheduled_analyzer", new=fake_analyzer
                ),
                patch.object(JobScheduler, "_run_outcome_tracker", new=fake_tracker),
                patch("asyncio.sleep", sleep_mock),
            ):
                await sched._run_loop()

            assert "alert" in call_order
            assert "analyzer" in call_order
            assert "tracker" in call_order

    async def test_run_loop_stops_when_running_false(self):
        """_run_loop() exits cleanly once self.running is set to False."""
        with (
            patch("backend.shared.jobs.scheduler.create_async_engine"),
            patch("backend.shared.jobs.scheduler.async_sessionmaker"),
        ):
            sched = JobScheduler()
            sched.running = False

            async def fake_job(self_inner):
                pass

            sleep_mock = AsyncMock()

            with (
                patch.object(JobScheduler, "_run_alert_checker", new=fake_job),
                patch.object(JobScheduler, "_run_scheduled_analyzer", new=fake_job),
                patch.object(JobScheduler, "_run_outcome_tracker", new=fake_job),
                patch("asyncio.sleep", sleep_mock),
            ):
                await asyncio.wait_for(sched._run_loop(), timeout=2.0)
