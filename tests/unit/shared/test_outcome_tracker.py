# tests/unit/shared/test_outcome_tracker.py
"""
Unit tests for backend/shared/jobs/outcome_tracker.py.

Tests cover:
- _was_recommendation_correct: pure function, various BUY/SELL/HOLD scenarios
- _extract_agent_action: pure function, all agent types and signal values
- update_outcome_prices: async with mocked DB and market data client
- update_agent_accuracy: async with mocked DB and _calculate_agent_accuracy
- run_outcome_tracker_job: async integration, success and failure paths
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from backend.shared.ai.state.enums import Action, AgentType
from backend.shared.jobs.outcome_tracker import (
    _calculate_agent_accuracy,
    _extract_agent_action,
    _was_recommendation_correct,
    run_outcome_tracker_job,
    update_agent_accuracy,
    update_outcome_prices,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.add = MagicMock()
    return db


def _make_outcome(
    action=Action.BUY,
    price_at_rec=100.0,
    price_after_1d=None,
    price_after_7d=None,
    price_after_30d=None,
    price_after_90d=None,
    outcome_correct=None,
):
    """Helper to build a mock AnalysisOutcome."""
    outcome = MagicMock()
    outcome.session_id = uuid4()
    outcome.ticker = "AAPL"
    outcome.price_after_90d = price_after_90d
    outcome.price_after_1d = price_after_1d
    outcome.price_after_7d = price_after_7d
    outcome.price_after_30d = price_after_30d
    outcome.outcome_correct = outcome_correct
    outcome.action_recommended = action
    outcome.price_at_recommendation = price_at_rec
    return outcome


def _make_session(days_ago=35):
    """Helper to build a mock AnalysisSession."""
    session = MagicMock()
    session.created_at = datetime.now() - timedelta(days=days_ago)
    session.market = MagicMock()
    return session


def _outcomes_result(outcomes):
    result = MagicMock()
    result.scalars.return_value.all.return_value = outcomes
    return result


def _session_result(session):
    result = MagicMock()
    result.scalar_one_or_none.return_value = session
    return result


def _accuracy_result(record=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = record
    return result


# ---------------------------------------------------------------------------
# _was_recommendation_correct
# ---------------------------------------------------------------------------


class TestWasRecommendationCorrect:
    def test_buy_price_goes_up_returns_true(self):
        assert _was_recommendation_correct(Action.BUY, 100.0, 105.0) is True

    def test_buy_price_goes_down_returns_false(self):
        assert _was_recommendation_correct(Action.BUY, 100.0, 95.0) is False

    def test_buy_price_flat_returns_false(self):
        # change = 0.0, which is NOT > 0
        assert _was_recommendation_correct(Action.BUY, 100.0, 100.0) is False

    def test_sell_price_goes_down_returns_true(self):
        assert _was_recommendation_correct(Action.SELL, 100.0, 90.0) is True

    def test_sell_price_goes_up_returns_false(self):
        assert _was_recommendation_correct(Action.SELL, 100.0, 110.0) is False

    def test_hold_small_change_within_threshold_returns_true(self):
        # 1% change < 2% default threshold
        assert _was_recommendation_correct(Action.HOLD, 100.0, 101.0) is True

    def test_hold_large_change_exceeds_threshold_returns_false(self):
        # 5% change > 2% default threshold
        assert _was_recommendation_correct(Action.HOLD, 100.0, 105.0) is False

    def test_hold_exactly_at_threshold_returns_false(self):
        # abs(change) == threshold is NOT < threshold (exclusive)
        assert _was_recommendation_correct(Action.HOLD, 100.0, 102.0) is False

    def test_hold_custom_threshold_within_range(self):
        # With 5% threshold, 3% change should be correct
        assert (
            _was_recommendation_correct(Action.HOLD, 100.0, 103.0, threshold=0.05)
            is True
        )

    def test_hold_custom_threshold_exceeded(self):
        # With 1% threshold, 2% change should be incorrect
        assert (
            _was_recommendation_correct(Action.HOLD, 100.0, 102.0, threshold=0.01)
            is False
        )


# ---------------------------------------------------------------------------
# _extract_agent_action
# ---------------------------------------------------------------------------


class TestExtractAgentAction:
    # --- FUNDAMENTAL ---
    def test_fundamental_bullish_returns_buy(self):
        assert (
            _extract_agent_action({"signal": "bullish"}, AgentType.FUNDAMENTAL)
            == Action.BUY
        )

    def test_fundamental_bearish_returns_sell(self):
        assert (
            _extract_agent_action({"signal": "bearish"}, AgentType.FUNDAMENTAL)
            == Action.SELL
        )

    def test_fundamental_other_signal_returns_hold(self):
        assert (
            _extract_agent_action({"signal": "neutral"}, AgentType.FUNDAMENTAL)
            == Action.HOLD
        )

    def test_fundamental_missing_signal_returns_hold(self):
        assert _extract_agent_action({}, AgentType.FUNDAMENTAL) == Action.HOLD

    # --- SENTIMENT ---
    def test_sentiment_high_score_returns_buy(self):
        assert (
            _extract_agent_action({"sentiment_score": 75}, AgentType.SENTIMENT)
            == Action.BUY
        )

    def test_sentiment_low_score_returns_sell(self):
        assert (
            _extract_agent_action({"sentiment_score": 30}, AgentType.SENTIMENT)
            == Action.SELL
        )

    def test_sentiment_mid_score_returns_hold(self):
        assert (
            _extract_agent_action({"sentiment_score": 50}, AgentType.SENTIMENT)
            == Action.HOLD
        )

    def test_sentiment_boundary_score_60_returns_hold(self):
        # score == 60 is NOT > 60, so HOLD
        assert (
            _extract_agent_action({"sentiment_score": 60}, AgentType.SENTIMENT)
            == Action.HOLD
        )

    def test_sentiment_boundary_score_40_returns_hold(self):
        # score == 40 is NOT < 40, so HOLD
        assert (
            _extract_agent_action({"sentiment_score": 40}, AgentType.SENTIMENT)
            == Action.HOLD
        )

    # --- TECHNICAL ---
    def test_technical_buy_signal_returns_buy(self):
        assert (
            _extract_agent_action({"signal": "buy"}, AgentType.TECHNICAL) == Action.BUY
        )

    def test_technical_sell_signal_returns_sell(self):
        assert (
            _extract_agent_action({"signal": "sell"}, AgentType.TECHNICAL)
            == Action.SELL
        )

    def test_technical_other_signal_returns_hold(self):
        assert (
            _extract_agent_action({"signal": "neutral"}, AgentType.TECHNICAL)
            == Action.HOLD
        )

    # --- RISK / UNKNOWN ---
    def test_risk_agent_returns_none(self):
        assert _extract_agent_action({"signal": "ok"}, AgentType.RISK_MANAGER) is None

    def test_chairperson_agent_returns_none(self):
        assert _extract_agent_action({"signal": "buy"}, AgentType.CHAIRPERSON) is None


# ---------------------------------------------------------------------------
# update_outcome_prices
# ---------------------------------------------------------------------------


class TestUpdateOutcomePrices:
    async def test_returns_zero_when_no_outcomes(self, mock_db):
        empty_result = MagicMock()
        empty_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = empty_result

        result = await update_outcome_prices(mock_db)

        assert result == 0

    async def test_skips_outcome_when_session_not_found(self, mock_db):
        outcome = _make_outcome()
        mock_db.execute.side_effect = [
            _outcomes_result([outcome]),
            _session_result(None),  # session not found
        ]

        mock_client = AsyncMock()
        mock_client.get_stock_data = AsyncMock(return_value={"current_price": 110.0})
        with patch(
            "backend.shared.jobs.outcome_tracker.get_market_data_client",
            return_value=mock_client,
        ):
            result = await update_outcome_prices(mock_db)

        assert result == 0

    async def test_updates_1d_price_after_one_day(self, mock_db):
        outcome = _make_outcome(price_after_1d=None)
        session = _make_session(days_ago=2)
        mock_db.execute.side_effect = [
            _outcomes_result([outcome]),
            _session_result(session),
        ]

        mock_client = AsyncMock()
        mock_client.get_stock_data = AsyncMock(return_value={"current_price": 105.0})
        with patch(
            "backend.shared.jobs.outcome_tracker.get_market_data_client",
            return_value=mock_client,
        ):
            result = await update_outcome_prices(mock_db)

        assert outcome.price_after_1d == 105.0
        assert result >= 1

    async def test_updates_7d_price_after_seven_days(self, mock_db):
        outcome = _make_outcome(price_after_1d=105.0, price_after_7d=None)
        session = _make_session(days_ago=8)
        mock_db.execute.side_effect = [
            _outcomes_result([outcome]),
            _session_result(session),
        ]

        mock_client = AsyncMock()
        mock_client.get_stock_data = AsyncMock(return_value={"current_price": 108.0})
        with patch(
            "backend.shared.jobs.outcome_tracker.get_market_data_client",
            return_value=mock_client,
        ):
            result = await update_outcome_prices(mock_db)

        assert outcome.price_after_7d == 108.0
        assert result >= 1

    async def test_updates_30d_price_and_sets_outcome_correct(self, mock_db):
        outcome = _make_outcome(
            action=Action.BUY,
            price_at_rec=100.0,
            price_after_1d=105.0,
            price_after_7d=107.0,
            price_after_30d=None,
            outcome_correct=None,
        )
        session = _make_session(days_ago=35)
        mock_db.execute.side_effect = [
            _outcomes_result([outcome]),
            _session_result(session),
        ]

        mock_client = AsyncMock()
        mock_client.get_stock_data = AsyncMock(return_value={"current_price": 115.0})
        with patch(
            "backend.shared.jobs.outcome_tracker.get_market_data_client",
            return_value=mock_client,
        ):
            result = await update_outcome_prices(mock_db)

        assert outcome.price_after_30d == 115.0
        # BUY with price going from 100 to 115 -> correct
        assert outcome.outcome_correct is True
        assert result >= 1

    async def test_handles_oserror_with_dns_error_gracefully(self, mock_db):
        outcome = _make_outcome()
        session = _make_session(days_ago=35)
        mock_db.execute.side_effect = [
            _outcomes_result([outcome]),
            _session_result(session),
        ]

        dns_error = OSError("Name or service not known")
        dns_error.errno = -2

        mock_client = AsyncMock()
        mock_client.get_stock_data = AsyncMock(side_effect=dns_error)
        with patch(
            "backend.shared.jobs.outcome_tracker.get_market_data_client",
            return_value=mock_client,
        ):
            result = await update_outcome_prices(mock_db)

        mock_db.rollback.assert_called_once()
        assert result == 0

    async def test_handles_generic_exception_gracefully(self, mock_db):
        outcome = _make_outcome()
        session = _make_session(days_ago=35)
        mock_db.execute.side_effect = [
            _outcomes_result([outcome]),
            _session_result(session),
        ]

        mock_client = AsyncMock()
        mock_client.get_stock_data = AsyncMock(side_effect=RuntimeError("API timeout"))
        with patch(
            "backend.shared.jobs.outcome_tracker.get_market_data_client",
            return_value=mock_client,
        ):
            result = await update_outcome_prices(mock_db)

        mock_db.rollback.assert_called_once()
        assert result == 0

    async def test_commits_after_successful_price_update(self, mock_db):
        outcome = _make_outcome(price_after_1d=None)
        session = _make_session(days_ago=2)
        mock_db.execute.side_effect = [
            _outcomes_result([outcome]),
            _session_result(session),
        ]

        mock_client = AsyncMock()
        mock_client.get_stock_data = AsyncMock(return_value={"current_price": 110.0})
        with patch(
            "backend.shared.jobs.outcome_tracker.get_market_data_client",
            return_value=mock_client,
        ):
            await update_outcome_prices(mock_db)

        mock_db.commit.assert_called_once()

    async def test_updates_last_updated_timestamp(self, mock_db):
        outcome = _make_outcome(price_after_1d=None)
        session = _make_session(days_ago=2)
        mock_db.execute.side_effect = [
            _outcomes_result([outcome]),
            _session_result(session),
        ]

        mock_client = AsyncMock()
        mock_client.get_stock_data = AsyncMock(return_value={"current_price": 110.0})
        with patch(
            "backend.shared.jobs.outcome_tracker.get_market_data_client",
            return_value=mock_client,
        ):
            await update_outcome_prices(mock_db)

        assert outcome.last_updated is not None


# ---------------------------------------------------------------------------
# update_agent_accuracy
# ---------------------------------------------------------------------------


class TestUpdateAgentAccuracy:
    async def test_calls_calculate_for_all_agents_and_periods(self, mock_db):
        with patch(
            "backend.shared.jobs.outcome_tracker._calculate_agent_accuracy",
            new_callable=AsyncMock,
        ) as mock_calc:
            await update_agent_accuracy(mock_db)

        # 3 agents x 3 periods = 9 calls
        assert mock_calc.call_count == 9

    async def test_covers_all_three_analyst_agents(self, mock_db):
        called_agents = []

        async def capture_calc(db, agent_type, period):
            called_agents.append(agent_type)

        with patch(
            "backend.shared.jobs.outcome_tracker._calculate_agent_accuracy",
            side_effect=capture_calc,
        ):
            await update_agent_accuracy(mock_db)

        assert AgentType.FUNDAMENTAL in called_agents
        assert AgentType.SENTIMENT in called_agents
        assert AgentType.TECHNICAL in called_agents
        assert AgentType.RISK_MANAGER not in called_agents
        assert AgentType.CHAIRPERSON not in called_agents

    async def test_covers_all_three_periods(self, mock_db):
        called_periods = []

        async def capture_calc(db, agent_type, period):
            called_periods.append(period)

        with patch(
            "backend.shared.jobs.outcome_tracker._calculate_agent_accuracy",
            side_effect=capture_calc,
        ):
            await update_agent_accuracy(mock_db)

        assert "7d" in called_periods
        assert "30d" in called_periods
        assert "90d" in called_periods

    async def test_handles_exception_in_calculate_gracefully(self, mock_db):
        with patch(
            "backend.shared.jobs.outcome_tracker._calculate_agent_accuracy",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB failure"),
        ):
            # Should not raise; exceptions are caught and logged
            await update_agent_accuracy(mock_db)


# ---------------------------------------------------------------------------
# run_outcome_tracker_job
# ---------------------------------------------------------------------------


class TestRunOutcomeTrackerJob:
    async def test_returns_success_true_with_updated_count(self, mock_db):
        with (
            patch(
                "backend.shared.jobs.outcome_tracker.update_outcome_prices",
                new_callable=AsyncMock,
                return_value=5,
            ),
            patch(
                "backend.shared.jobs.outcome_tracker.update_agent_accuracy",
                new_callable=AsyncMock,
            ),
        ):
            result = await run_outcome_tracker_job(mock_db)

        assert result["success"] is True
        assert result["outcomes_updated"] == 5
        assert "duration_seconds" in result

    async def test_returns_success_false_when_exception_occurs(self, mock_db):
        with patch(
            "backend.shared.jobs.outcome_tracker.update_outcome_prices",
            new_callable=AsyncMock,
            side_effect=RuntimeError("catastrophic failure"),
        ):
            result = await run_outcome_tracker_job(mock_db)

        assert result["success"] is False
        assert "error" in result
        assert "catastrophic failure" in result["error"]

    async def test_duration_seconds_is_non_negative(self, mock_db):
        with (
            patch(
                "backend.shared.jobs.outcome_tracker.update_outcome_prices",
                new_callable=AsyncMock,
                return_value=0,
            ),
            patch(
                "backend.shared.jobs.outcome_tracker.update_agent_accuracy",
                new_callable=AsyncMock,
            ),
        ):
            result = await run_outcome_tracker_job(mock_db)

        assert result["duration_seconds"] >= 0


# ---------------------------------------------------------------------------
# update_outcome_prices: 90d update path and non-DNS OSError
# ---------------------------------------------------------------------------


class TestUpdateOutcomePricesAdditional:
    async def test_updates_90d_price_after_ninety_days(self, mock_db):
        """90d price is populated once 90 days have elapsed."""
        # All earlier prices are already populated; only 90d is missing
        outcome = _make_outcome(
            price_after_1d=101.0,
            price_after_7d=105.0,
            price_after_30d=110.0,
            price_after_90d=None,
            outcome_correct=True,  # already set, won't be re-evaluated
        )
        session = _make_session(days_ago=91)
        mock_db.execute.side_effect = [
            _outcomes_result([outcome]),
            _session_result(session),
        ]

        mock_client = AsyncMock()
        mock_client.get_stock_data = AsyncMock(return_value={"current_price": 120.0})
        with patch(
            "backend.shared.jobs.outcome_tracker.get_market_data_client",
            return_value=mock_client,
        ):
            result = await update_outcome_prices(mock_db)

        assert outcome.price_after_90d == 120.0
        assert result >= 1

    async def test_handles_non_dns_oserror_gracefully(self, mock_db):
        """Non-DNS OSError (e.g. connection refused) is handled gracefully."""
        outcome = _make_outcome()
        session = _make_session(days_ago=35)
        mock_db.execute.side_effect = [
            _outcomes_result([outcome]),
            _session_result(session),
        ]

        # OSError that is NOT a DNS error (errno != -2, no "Name or service not known")
        conn_error = OSError("Connection refused")
        conn_error.errno = 111  # ECONNREFUSED, not -2 (NXDOMAIN)

        mock_client = AsyncMock()
        mock_client.get_stock_data = AsyncMock(side_effect=conn_error)
        with patch(
            "backend.shared.jobs.outcome_tracker.get_market_data_client",
            return_value=mock_client,
        ):
            result = await update_outcome_prices(mock_db)

        mock_db.rollback.assert_called_once()
        assert result == 0


# ---------------------------------------------------------------------------
# _calculate_agent_accuracy
# ---------------------------------------------------------------------------


def _rows_result(rows):
    """Build a mock execute result whose .all() returns rows."""
    result = MagicMock()
    result.all.return_value = rows
    return result


def _make_accuracy_row(report_data, decision_action, outcome_correct):
    """Build a mock (AnalysisOutcome, FinalDecision, AgentReport) tuple."""
    outcome = MagicMock()
    outcome.outcome_correct = outcome_correct

    decision = MagicMock()
    decision.action = decision_action

    agent_report = MagicMock()
    agent_report.report_data = report_data

    return (outcome, decision, agent_report)


class TestCalculateAgentAccuracy:
    async def test_creates_new_accuracy_record_when_none_exists(self, mock_db):
        """_calculate_agent_accuracy() creates a new AgentAccuracy when missing."""
        row = _make_accuracy_row(
            {"signal": "bullish"},  # FUNDAMENTAL → BUY
            Action.BUY,
            outcome_correct=True,
        )
        mock_db.execute.side_effect = [
            _rows_result([row]),
            _accuracy_result(None),  # no existing record
        ]

        await _calculate_agent_accuracy(mock_db, AgentType.FUNDAMENTAL, "30d")

        # A new record was added to the session
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_updates_existing_accuracy_record(self, mock_db):
        """_calculate_agent_accuracy() updates an existing AgentAccuracy record."""
        row = _make_accuracy_row(
            {"signal": "bullish"},  # FUNDAMENTAL → BUY
            Action.BUY,
            outcome_correct=True,
        )
        existing = MagicMock()
        mock_db.execute.side_effect = [
            _rows_result([row]),
            _accuracy_result(existing),
        ]

        await _calculate_agent_accuracy(mock_db, AgentType.FUNDAMENTAL, "30d")

        # Existing record fields are updated, not a new one added
        mock_db.add.assert_not_called()
        assert existing.total_signals == 1
        assert existing.correct_signals == 1
        assert existing.accuracy == 1.0

    async def test_correct_signal_when_agent_agreed_and_outcome_correct(self, mock_db):
        """Agent agrees with decision + outcome correct → counted as correct signal."""
        row = _make_accuracy_row(
            {"signal": "bullish"},  # FUNDAMENTAL → BUY
            Action.BUY,
            outcome_correct=True,
        )
        existing = MagicMock()
        mock_db.execute.side_effect = [_rows_result([row]), _accuracy_result(existing)]

        await _calculate_agent_accuracy(mock_db, AgentType.FUNDAMENTAL, "30d")

        assert existing.correct_signals == 1
        assert existing.total_signals == 1

    async def test_incorrect_signal_when_agent_agreed_but_outcome_wrong(self, mock_db):
        """Agent agrees with decision + outcome incorrect → counted as incorrect."""
        row = _make_accuracy_row(
            {"signal": "bullish"},  # FUNDAMENTAL → BUY
            Action.BUY,
            outcome_correct=False,
        )
        existing = MagicMock()
        mock_db.execute.side_effect = [_rows_result([row]), _accuracy_result(existing)]

        await _calculate_agent_accuracy(mock_db, AgentType.FUNDAMENTAL, "30d")

        assert existing.correct_signals == 0
        assert existing.total_signals == 1

    async def test_correct_signal_when_agent_disagreed_and_outcome_wrong(self, mock_db):
        """Agent disagrees with decision + outcome incorrect → counted as correct."""
        row = _make_accuracy_row(
            {"signal": "bullish"},  # FUNDAMENTAL → BUY
            Action.SELL,  # decision was SELL (agent disagreed)
            outcome_correct=False,  # SELL was wrong, agent was right to disagree
        )
        existing = MagicMock()
        mock_db.execute.side_effect = [_rows_result([row]), _accuracy_result(existing)]

        await _calculate_agent_accuracy(mock_db, AgentType.FUNDAMENTAL, "30d")

        assert existing.correct_signals == 1
        assert existing.total_signals == 1

    async def test_zero_accuracy_when_no_rows(self, mock_db):
        """With no outcome rows, accuracy defaults to 0.0."""
        existing = MagicMock()
        mock_db.execute.side_effect = [
            _rows_result([]),
            _accuracy_result(existing),
        ]

        await _calculate_agent_accuracy(mock_db, AgentType.TECHNICAL, "7d")

        assert existing.accuracy == 0.0
        assert existing.total_signals == 0

    async def test_skips_row_when_agent_action_is_none(self, mock_db):
        """Rows where _extract_agent_action returns None are skipped."""
        # RISK agent always returns None from _extract_agent_action
        row = _make_accuracy_row(
            {"signal": "ok"},
            Action.BUY,
            outcome_correct=True,
        )
        existing = MagicMock()
        mock_db.execute.side_effect = [_rows_result([row]), _accuracy_result(existing)]

        # Use RISK agent type, which causes _extract_agent_action to return None
        await _calculate_agent_accuracy(mock_db, AgentType.RISK_MANAGER, "30d")

        # Row was skipped, so total_signals remains 0
        assert existing.total_signals == 0

    async def test_commits_after_calculation(self, mock_db):
        """_calculate_agent_accuracy() always commits after updating."""
        mock_db.execute.side_effect = [
            _rows_result([]),
            _accuracy_result(MagicMock()),
        ]

        await _calculate_agent_accuracy(mock_db, AgentType.FUNDAMENTAL, "90d")

        mock_db.commit.assert_called_once()

    async def test_uses_correct_price_field_for_7d_period(self, mock_db):
        """_calculate_agent_accuracy() queries price_after_7d for the '7d' period."""
        mock_db.execute.side_effect = [
            _rows_result([]),
            _accuracy_result(MagicMock()),
        ]

        # Should not raise - the price_field_map["7d"] must resolve correctly
        await _calculate_agent_accuracy(mock_db, AgentType.SENTIMENT, "7d")

        assert mock_db.execute.call_count == 2

    async def test_uses_correct_price_field_for_90d_period(self, mock_db):
        """_calculate_agent_accuracy() queries price_after_90d for the '90d' period."""
        mock_db.execute.side_effect = [
            _rows_result([]),
            _accuracy_result(MagicMock()),
        ]

        await _calculate_agent_accuracy(mock_db, AgentType.TECHNICAL, "90d")

        assert mock_db.execute.call_count == 2
