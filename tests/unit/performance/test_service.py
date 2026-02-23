# tests/unit/test_services_performance.py
"""Unit tests for PerformanceService."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from backend.domains.performance.services.service import PerformanceService
from backend.shared.ai.state.enums import Action, Market
from backend.shared.db.models import AnalysisOutcome, AnalysisSession, FinalDecision
from backend.shared.services.base import BaseService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_db_result(value):
    """Return a mock db.execute result whose scalar_one_or_none() returns value."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def make_outcome(
    ticker="AAPL",
    action=Action.BUY,
    price_at_recommendation=150.0,
    price_after_1d=None,
    price_after_7d=None,
    price_after_30d=None,
    price_after_90d=None,
    outcome_correct=None,
):
    """Build a minimal AnalysisOutcome-like MagicMock."""
    outcome = MagicMock(spec=AnalysisOutcome)
    outcome.ticker = ticker
    outcome.action_recommended = action
    outcome.price_at_recommendation = price_at_recommendation
    outcome.price_after_1d = price_after_1d
    outcome.price_after_7d = price_after_7d
    outcome.price_after_30d = price_after_30d
    outcome.price_after_90d = price_after_90d
    outcome.outcome_correct = outcome_correct
    outcome.created_at = datetime.now()
    return outcome


def make_decision(action=Action.BUY, confidence=0.82):
    """Build a minimal FinalDecision-like MagicMock."""
    decision = MagicMock(spec=FinalDecision)
    decision.action = action
    decision.confidence = confidence
    return decision


def make_session(ticker="AAPL", market=Market.US):
    """Build a minimal AnalysisSession-like MagicMock."""
    session = MagicMock(spec=AnalysisSession)
    session.ticker = ticker
    session.market = market
    return session


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_performance_dao():
    dao = MagicMock()
    dao.session = MagicMock()
    dao.create = AsyncMock()
    dao.get_all = AsyncMock()
    dao.get_recent_outcomes = AsyncMock()
    dao.get_analysis_session = AsyncMock()
    dao.get_final_decision = AsyncMock()
    dao.get_by_session_id = AsyncMock()
    dao.create_outcome = AsyncMock()
    return dao


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def performance_service(mock_performance_dao):
    return PerformanceService(mock_performance_dao)


# ---------------------------------------------------------------------------
# Service initialisation
# ---------------------------------------------------------------------------


def test_dao_stored_on_service(mock_performance_dao):
    """Constructor stores the DAO on the service instance."""
    service = PerformanceService(mock_performance_dao)
    assert service.performance_dao is mock_performance_dao


def test_inherits_from_base_service(mock_performance_dao):
    """PerformanceService inherits from BaseService."""
    service = PerformanceService(mock_performance_dao)
    assert isinstance(service, BaseService)


# ---------------------------------------------------------------------------
# create_analysis_outcome
# ---------------------------------------------------------------------------


async def test_create_outcome_session_not_found(performance_service, mock_db):
    """When the session query returns None the method returns None."""
    session_id = uuid4()
    mock_db.execute.return_value = make_db_result(None)

    result = await performance_service.create_analysis_outcome(mock_db, session_id)

    assert result is None
    mock_db.commit.assert_not_awaited()
    mock_db.rollback.assert_not_awaited()


async def test_create_outcome_decision_not_found(performance_service, mock_db):
    """When the decision query returns None the method returns None."""
    session_id = uuid4()
    session = make_session()

    # Query 1 (session) → found; Query 2 (decision) → None
    mock_db.execute.side_effect = [
        make_db_result(session),
        make_db_result(None),
    ]

    result = await performance_service.create_analysis_outcome(mock_db, session_id)

    assert result is None
    mock_db.commit.assert_not_awaited()


async def test_create_outcome_already_exists(performance_service, mock_db):
    """When an existing outcome record is found the method returns None."""
    session_id = uuid4()
    session = make_session()
    decision = make_decision()
    existing_outcome = MagicMock(spec=AnalysisOutcome)

    # Query 1 → session; Query 2 → decision; Query 3 → existing outcome
    mock_db.execute.side_effect = [
        make_db_result(session),
        make_db_result(decision),
        make_db_result(existing_outcome),
    ]

    result = await performance_service.create_analysis_outcome(mock_db, session_id)

    assert result is None
    mock_db.commit.assert_not_awaited()


async def test_create_outcome_price_fetch_error(performance_service, mock_db):
    """When get_market_data_client raises an exception the method returns None."""
    session_id = uuid4()
    session = make_session()
    decision = make_decision()

    # Query 1 → session; Query 2 → decision; Query 3 → no existing outcome
    mock_db.execute.side_effect = [
        make_db_result(session),
        make_db_result(decision),
        make_db_result(None),
    ]

    with patch(
        "backend.domains.performance.services.service.get_market_data_client"
    ) as mock_client_factory:
        mock_client_factory.side_effect = RuntimeError("market data unavailable")

        result = await performance_service.create_analysis_outcome(mock_db, session_id)

    assert result is None
    # Price fetch error is caught and returns None gracefully (no rollback needed)
    mock_db.rollback.assert_not_awaited()
    mock_db.commit.assert_not_awaited()


async def test_create_outcome_success(
    performance_service, mock_performance_dao, mock_db
):
    """Happy path: all queries pass, price is fetched, outcome is created and returned."""
    session_id = uuid4()
    session = make_session(ticker="AAPL", market=Market.US)
    decision = make_decision(action=Action.BUY)
    created_outcome = make_outcome(
        ticker="AAPL", action=Action.BUY, price_at_recommendation=155.0
    )

    mock_performance_dao.get_analysis_session.return_value = session
    mock_performance_dao.get_final_decision.return_value = decision
    mock_performance_dao.get_by_session_id.return_value = None  # No existing outcome
    mock_performance_dao.create_outcome.return_value = created_outcome

    mock_market_client = MagicMock()
    mock_market_client.get_stock_data = AsyncMock(return_value={"current_price": 155.0})

    with patch(
        "backend.domains.performance.services.service.get_market_data_client",
        return_value=mock_market_client,
    ):
        result = await performance_service.create_analysis_outcome(mock_db, session_id)

    assert result is created_outcome
    mock_performance_dao.create_outcome.assert_awaited_once()
    call_kwargs = mock_performance_dao.create_outcome.call_args.kwargs
    assert call_kwargs["ticker"] == "AAPL"
    assert call_kwargs["action_recommended"] == Action.BUY
    assert call_kwargs["price_at_recommendation"] == 155.0


async def test_create_outcome_success_passes_session_market_to_client(
    performance_service, mock_performance_dao, mock_db
):
    """The market data client is called with the session's ticker and market."""
    session_id = uuid4()
    session = make_session(ticker="TEVA", market=Market.TASE)
    decision = make_decision(action=Action.SELL)
    created_outcome = make_outcome(ticker="TEVA", action=Action.SELL)

    mock_performance_dao.get_analysis_session.return_value = session
    mock_performance_dao.get_final_decision.return_value = decision
    mock_performance_dao.get_by_session_id.return_value = None
    mock_performance_dao.create_outcome.return_value = created_outcome

    mock_market_client = MagicMock()
    mock_market_client.get_stock_data = AsyncMock(return_value={"current_price": 10.0})

    with patch(
        "backend.domains.performance.services.service.get_market_data_client",
        return_value=mock_market_client,
    ):
        await performance_service.create_analysis_outcome(mock_db, session_id)

    mock_market_client.get_stock_data.assert_awaited_once_with("TEVA", Market.TASE)


# ---------------------------------------------------------------------------
# get_performance_summary
# ---------------------------------------------------------------------------


async def test_get_performance_summary_empty(
    performance_service, mock_performance_dao, mock_db
):
    """When there are no outcomes the summary contains zeros."""
    mock_performance_dao.get_all.return_value = []

    result = await performance_service.get_performance_summary(mock_db)

    assert result["total_recommendations"] == 0
    assert result["correct_count"] == 0
    assert result["accuracy"] == 0.0
    assert result["by_action"] == {}


async def test_get_performance_summary_with_outcomes(
    performance_service, mock_performance_dao, mock_db
):
    """Summary counts and accuracy are calculated correctly across action types."""
    outcomes = [
        # BUY correct
        make_outcome(action=Action.BUY, outcome_correct=True),
        # BUY incorrect
        make_outcome(action=Action.BUY, outcome_correct=False),
        # SELL correct
        make_outcome(action=Action.SELL, outcome_correct=True),
    ]
    mock_performance_dao.get_all.return_value = outcomes

    result = await performance_service.get_performance_summary(mock_db)

    assert result["total_recommendations"] == 3
    assert result["correct_count"] == 2
    assert pytest.approx(result["accuracy"]) == 2 / 3

    buy_stats = result["by_action"][Action.BUY.value]
    assert buy_stats["total"] == 2
    assert buy_stats["correct"] == 1
    assert pytest.approx(buy_stats["accuracy"]) == 0.5

    sell_stats = result["by_action"][Action.SELL.value]
    assert sell_stats["total"] == 1
    assert sell_stats["correct"] == 1
    assert pytest.approx(sell_stats["accuracy"]) == 1.0

    # HOLD not in outcomes so must not appear in by_action
    assert Action.HOLD.value not in result["by_action"]


async def test_get_performance_summary_all_correct(
    performance_service, mock_performance_dao, mock_db
):
    """100% accuracy when every outcome is correct."""
    outcomes = [
        make_outcome(action=Action.BUY, outcome_correct=True),
        make_outcome(action=Action.SELL, outcome_correct=True),
    ]
    mock_performance_dao.get_all.return_value = outcomes

    result = await performance_service.get_performance_summary(mock_db)

    assert result["accuracy"] == 1.0
    assert result["correct_count"] == 2


async def test_get_performance_summary_none_correct(
    performance_service, mock_performance_dao, mock_db
):
    """0% accuracy when no outcome is correct."""
    outcomes = [
        make_outcome(action=Action.HOLD, outcome_correct=False),
    ]
    mock_performance_dao.get_all.return_value = outcomes

    result = await performance_service.get_performance_summary(mock_db)

    assert result["accuracy"] == 0.0
    assert result["correct_count"] == 0


# ---------------------------------------------------------------------------
# get_recent_outcomes
# ---------------------------------------------------------------------------


async def test_get_recent_outcomes_empty(
    performance_service, mock_performance_dao, mock_db
):
    """When the DAO returns an empty list the method returns an empty list."""
    mock_performance_dao.get_recent_outcomes.return_value = []

    result = await performance_service.get_recent_outcomes(mock_db)

    assert result == []


async def test_get_recent_outcomes_1d_and_30d_only(
    performance_service, mock_performance_dao, mock_db
):
    """Only 1d and 30d prices present → returns dict with '1d' and '30d' but not '7d' or '90d'."""
    outcome = make_outcome(
        ticker="MSFT",
        action=Action.BUY,
        price_at_recommendation=300.0,
        price_after_1d=310.0,
        price_after_7d=None,
        price_after_30d=330.0,
        price_after_90d=None,
        outcome_correct=True,
    )
    decision = make_decision(action=Action.BUY, confidence=0.75)
    session = make_session(ticker="MSFT")

    mock_performance_dao.get_recent_outcomes.return_value = [
        (outcome, decision, session)
    ]

    result = await performance_service.get_recent_outcomes(mock_db)

    assert len(result) == 1
    row = result[0]
    assert "1d" in row["returns"]
    assert "30d" in row["returns"]
    assert "7d" not in row["returns"]
    assert "90d" not in row["returns"]
    assert pytest.approx(row["returns"]["1d"]) == (310.0 - 300.0) / 300.0
    assert pytest.approx(row["returns"]["30d"]) == (330.0 - 300.0) / 300.0


async def test_get_recent_outcomes_no_follow_up_prices(
    performance_service, mock_performance_dao, mock_db
):
    """When all follow-up prices are None the returns dict is empty."""
    outcome = make_outcome(
        ticker="GOOG",
        action=Action.HOLD,
        price_at_recommendation=100.0,
        price_after_1d=None,
        price_after_7d=None,
        price_after_30d=None,
        price_after_90d=None,
    )
    decision = make_decision(action=Action.HOLD, confidence=0.5)
    session = make_session(ticker="GOOG")

    mock_performance_dao.get_recent_outcomes.return_value = [
        (outcome, decision, session)
    ]

    result = await performance_service.get_recent_outcomes(mock_db)

    assert result[0]["returns"] == {}


async def test_get_recent_outcomes_all_follow_up_prices(
    performance_service, mock_performance_dao, mock_db
):
    """All four price windows populate the returns dict."""
    outcome = make_outcome(
        ticker="AAPL",
        action=Action.BUY,
        price_at_recommendation=100.0,
        price_after_1d=101.0,
        price_after_7d=107.0,
        price_after_30d=130.0,
        price_after_90d=190.0,
    )
    decision = make_decision(action=Action.BUY, confidence=0.9)
    session = make_session()

    mock_performance_dao.get_recent_outcomes.return_value = [
        (outcome, decision, session)
    ]

    result = await performance_service.get_recent_outcomes(mock_db)

    returns = result[0]["returns"]
    assert set(returns.keys()) == {"1d", "7d", "30d", "90d"}


async def test_get_recent_outcomes_row_fields(
    performance_service, mock_performance_dao, mock_db
):
    """Each row contains the expected top-level keys."""
    outcome = make_outcome(
        ticker="TSLA",
        action=Action.SELL,
        price_at_recommendation=200.0,
        outcome_correct=False,
    )
    decision = make_decision(action=Action.SELL, confidence=0.6)
    session = make_session(ticker="TSLA")

    mock_performance_dao.get_recent_outcomes.return_value = [
        (outcome, decision, session)
    ]

    result = await performance_service.get_recent_outcomes(mock_db)

    row = result[0]
    assert row["ticker"] == "TSLA"
    assert row["action"] == Action.SELL.value
    assert row["price_at_recommendation"] == 200.0
    assert row["confidence"] == 0.6
    assert row["outcome_correct"] is False
    assert "returns" in row
    assert "created_at" in row


async def test_get_recent_outcomes_passes_limit_and_ticker(
    performance_service, mock_performance_dao, mock_db
):
    """The limit and ticker parameters are forwarded to the DAO."""
    mock_performance_dao.get_recent_outcomes.return_value = []

    await performance_service.get_recent_outcomes(mock_db, limit=5, ticker="NVDA")

    mock_performance_dao.get_recent_outcomes.assert_awaited_once_with(
        limit=5, ticker="NVDA"
    )


async def test_get_recent_outcomes_default_limit_and_no_ticker(
    performance_service, mock_performance_dao, mock_db
):
    """Default limit is 20 and ticker defaults to None."""
    mock_performance_dao.get_recent_outcomes.return_value = []

    await performance_service.get_recent_outcomes(mock_db)

    mock_performance_dao.get_recent_outcomes.assert_awaited_once_with(
        limit=20, ticker=None
    )
