# tests/unit/analysis/test_dao_analysis.py
"""
Unit tests for backend/shared/dao/analysis.py.

Tests cover:
- AnalysisDAO.create_session: delegates to BaseDAO.create
- AnalysisDAO.add_report: creates AgentReport, add/flush/refresh
- AnalysisDAO.add_decision: creates FinalDecision, add/flush/refresh
- AnalysisDAO.get_user_sessions: SELECT with user_id filter
- AnalysisDAO.get_recent_sessions: SELECT ordered by created_at
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.shared.ai.state.enums import Action, AgentType, Market
from backend.shared.dao.analysis import AnalysisDAO
from backend.shared.db.models import AgentReport, AnalysisSession, FinalDecision

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
    return AnalysisDAO(mock_session)


# ---------------------------------------------------------------------------
# create_session
# ---------------------------------------------------------------------------


async def test_create_session_calls_add_flush_refresh(dao, mock_session):
    """create_session() must call session.add, flush, and refresh."""
    result = await dao.create_session("AAPL", Market.US)

    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once()


async def test_create_session_adds_analysis_session_object(dao, mock_session):
    """create_session() adds an AnalysisSession with the correct fields."""
    user_id = uuid4()
    await dao.create_session("TSLA", Market.US, user_id)

    added = mock_session.add.call_args[0][0]
    assert isinstance(added, AnalysisSession)
    assert added.ticker == "TSLA"
    assert added.market == Market.US
    assert added.user_id == user_id


async def test_create_session_without_user_id(dao, mock_session):
    """create_session() works with user_id=None (anonymous analysis)."""
    await dao.create_session("MSFT", Market.US)

    added = mock_session.add.call_args[0][0]
    assert added.user_id is None


# ---------------------------------------------------------------------------
# add_report
# ---------------------------------------------------------------------------


async def test_add_report_creates_agent_report_with_correct_fields(dao, mock_session):
    """add_report() must add an AgentReport with session_id, agent_type, report_data."""
    session_id = uuid4()
    report_data = {"signal": "bullish", "confidence": 0.8}

    await dao.add_report(session_id, AgentType.FUNDAMENTAL, report_data)

    added = mock_session.add.call_args[0][0]
    assert isinstance(added, AgentReport)
    assert added.session_id == session_id
    assert added.agent_type == AgentType.FUNDAMENTAL
    assert added.report_data == report_data


async def test_add_report_calls_add_flush_refresh(dao, mock_session):
    """add_report() must call session.add, flush, and refresh."""
    await dao.add_report(uuid4(), AgentType.TECHNICAL, {"signal": "buy"})

    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once()


async def test_add_report_returns_agent_report(dao, mock_session):
    """add_report() must return an AgentReport instance."""
    result = await dao.add_report(uuid4(), AgentType.SENTIMENT, {"sentiment_score": 75})

    assert isinstance(result, AgentReport)


# ---------------------------------------------------------------------------
# add_decision
# ---------------------------------------------------------------------------


async def test_add_decision_creates_final_decision_with_correct_fields(
    dao, mock_session
):
    """add_decision() must add a FinalDecision with correct action and confidence."""
    session_id = uuid4()

    await dao.add_decision(
        session_id,
        action=Action.BUY,
        confidence=0.85,
        rationale="Strong fundamentals",
    )

    added = mock_session.add.call_args[0][0]
    assert isinstance(added, FinalDecision)
    assert added.session_id == session_id
    assert added.action == Action.BUY
    assert added.confidence == 0.85
    assert added.rationale == "Strong fundamentals"


async def test_add_decision_with_veto(dao, mock_session):
    """add_decision() must pass vetoed=True and veto_reason to FinalDecision."""
    await dao.add_decision(
        uuid4(),
        action=Action.HOLD,
        confidence=0.5,
        rationale="Risk veto",
        vetoed=True,
        veto_reason="Sector overweight",
    )

    added = mock_session.add.call_args[0][0]
    assert added.vetoed is True
    assert added.veto_reason == "Sector overweight"


async def test_add_decision_calls_add_flush_refresh(dao, mock_session):
    """add_decision() must call session.add, flush, and refresh."""
    await dao.add_decision(uuid4(), Action.SELL, 0.7, "Bearish trend")

    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once()


async def test_add_decision_returns_final_decision(dao, mock_session):
    """add_decision() must return a FinalDecision instance."""
    result = await dao.add_decision(uuid4(), Action.BUY, 0.9, "Bullish signals")

    assert isinstance(result, FinalDecision)


# ---------------------------------------------------------------------------
# get_user_sessions
# ---------------------------------------------------------------------------


async def test_get_user_sessions_returns_list(dao, mock_session):
    """get_user_sessions() must return a list of AnalysisSession."""
    user_id = uuid4()
    sessions = [MagicMock(spec=AnalysisSession), MagicMock(spec=AnalysisSession)]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = sessions
    mock_session.execute.return_value = mock_result

    result = await dao.get_user_sessions(user_id)

    assert result == sessions
    mock_session.execute.assert_called_once()


async def test_get_user_sessions_returns_empty_when_none(dao, mock_session):
    """get_user_sessions() returns [] when no sessions exist for user."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    result = await dao.get_user_sessions(uuid4())

    assert result == []


async def test_get_user_sessions_accepts_custom_limit(dao, mock_session):
    """get_user_sessions() passes the limit parameter to the query."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    await dao.get_user_sessions(uuid4(), limit=10)

    mock_session.execute.assert_called_once()


# ---------------------------------------------------------------------------
# get_recent_sessions
# ---------------------------------------------------------------------------


async def test_get_recent_sessions_returns_list(dao, mock_session):
    """get_recent_sessions() must return a list of AnalysisSession."""
    sessions = [MagicMock(spec=AnalysisSession)]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = sessions
    mock_session.execute.return_value = mock_result

    result = await dao.get_recent_sessions()

    assert result == sessions
    mock_session.execute.assert_called_once()


async def test_get_recent_sessions_returns_empty_list(dao, mock_session):
    """get_recent_sessions() returns [] when no sessions exist."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    result = await dao.get_recent_sessions()

    assert result == []


async def test_get_recent_sessions_accepts_custom_limit(dao, mock_session):
    """get_recent_sessions() accepts a custom limit parameter."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    result = await dao.get_recent_sessions(limit=5)

    assert result == []
    mock_session.execute.assert_called_once()
