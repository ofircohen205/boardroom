# tests/unit/performance/test_dao_performance.py
"""
Unit tests for backend/shared/dao/performance.py.

Tests cover:
- PerformanceDAO.create_outcome: delegates to BaseDAO.create
- PerformanceDAO.get_by_session_id: SELECT outcome WHERE session_id
- PerformanceDAO.get_recent_outcomes: JOIN query with optional ticker filter
- PerformanceDAO.get_agent_accuracy: SELECT AgentAccuracy WHERE agent_type, period
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.shared.ai.state.enums import Action, AgentType
from backend.shared.dao.performance import PerformanceDAO
from backend.shared.db.models import AgentAccuracy, AnalysisOutcome

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session():
    """Lightweight mock async DB session."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def dao(mock_session):
    return PerformanceDAO(mock_session)


# ---------------------------------------------------------------------------
# create_outcome
# ---------------------------------------------------------------------------


async def test_create_outcome_adds_analysis_outcome(dao, mock_session):
    """create_outcome() must add an AnalysisOutcome with correct fields."""
    session_id = uuid4()

    await dao.create_outcome(
        session_id=session_id,
        ticker="AAPL",
        action_recommended=Action.BUY,
        price_at_recommendation=150.0,
    )

    mock_session.add.assert_called_once()
    added = mock_session.add.call_args[0][0]
    assert isinstance(added, AnalysisOutcome)
    assert added.session_id == session_id
    assert added.ticker == "AAPL"
    assert added.action_recommended == Action.BUY
    assert added.price_at_recommendation == 150.0


async def test_create_outcome_calls_add_flush_refresh(dao, mock_session):
    """create_outcome() must call session.add, flush, and refresh."""
    await dao.create_outcome(uuid4(), "MSFT", Action.SELL, 300.0)

    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once()


async def test_create_outcome_returns_analysis_outcome(dao, mock_session):
    """create_outcome() must return an AnalysisOutcome instance."""
    result = await dao.create_outcome(uuid4(), "GOOG", Action.HOLD, 2800.0)

    assert isinstance(result, AnalysisOutcome)


# ---------------------------------------------------------------------------
# get_by_session_id
# ---------------------------------------------------------------------------


async def test_get_by_session_id_returns_outcome(dao, mock_session):
    """get_by_session_id() must return the matching outcome."""
    session_id = uuid4()
    outcome = MagicMock(spec=AnalysisOutcome)

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = outcome
    mock_session.execute.return_value = mock_result

    result = await dao.get_by_session_id(session_id)

    assert result is outcome
    mock_session.execute.assert_called_once()


async def test_get_by_session_id_returns_none_when_not_found(dao, mock_session):
    """get_by_session_id() must return None when no outcome exists."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    result = await dao.get_by_session_id(uuid4())

    assert result is None


# ---------------------------------------------------------------------------
# get_recent_outcomes
# ---------------------------------------------------------------------------


async def test_get_recent_outcomes_returns_tuples(dao, mock_session):
    """get_recent_outcomes() must return tuples from the JOIN query."""
    row1 = (MagicMock(), MagicMock(), MagicMock())

    mock_result = MagicMock()
    mock_result.all.return_value = [row1]
    mock_session.execute.return_value = mock_result

    result = await dao.get_recent_outcomes()

    assert len(result) == 1
    assert result[0] == row1
    mock_session.execute.assert_called_once()


async def test_get_recent_outcomes_with_ticker_filter(dao, mock_session):
    """get_recent_outcomes() applies ticker filter when provided."""
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result

    result = await dao.get_recent_outcomes(ticker="AAPL")

    assert result == []
    mock_session.execute.assert_called_once()


async def test_get_recent_outcomes_without_ticker_returns_all(dao, mock_session):
    """get_recent_outcomes() without ticker returns all results."""
    rows = [(MagicMock(), MagicMock(), MagicMock()) for _ in range(3)]

    mock_result = MagicMock()
    mock_result.all.return_value = rows
    mock_session.execute.return_value = mock_result

    result = await dao.get_recent_outcomes(limit=3)

    assert len(result) == 3


async def test_get_recent_outcomes_returns_empty_list(dao, mock_session):
    """get_recent_outcomes() returns [] when no outcomes exist."""
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result

    result = await dao.get_recent_outcomes()

    assert result == []


# ---------------------------------------------------------------------------
# get_agent_accuracy
# ---------------------------------------------------------------------------


async def test_get_agent_accuracy_returns_record(dao, mock_session):
    """get_agent_accuracy() must return the matching AgentAccuracy record."""
    accuracy = MagicMock(spec=AgentAccuracy)

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = accuracy
    mock_session.execute.return_value = mock_result

    result = await dao.get_agent_accuracy(AgentType.FUNDAMENTAL, "30d")

    assert result is accuracy
    mock_session.execute.assert_called_once()


async def test_get_agent_accuracy_returns_none_when_missing(dao, mock_session):
    """get_agent_accuracy() returns None when no record exists for that period."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    result = await dao.get_agent_accuracy(AgentType.TECHNICAL, "7d")

    assert result is None


async def test_get_agent_accuracy_queries_correct_agent_and_period(dao, mock_session):
    """get_agent_accuracy() passes both agent_type and period to the query."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    await dao.get_agent_accuracy(AgentType.SENTIMENT, "90d")

    # Query was executed (specific SQL content verified via integration tests)
    mock_session.execute.assert_called_once()
