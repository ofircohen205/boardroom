# tests/unit/test_services_analysis.py
"""Unit tests for AnalysisService."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.domains.analysis.services.exceptions import (
    AnalysisError,
    AnalysisSessionNotFoundError,
)
from backend.domains.analysis.services.service import AnalysisService
from backend.shared.ai.state.enums import Action, AgentType, Market
from backend.shared.db.models import AgentReport, AnalysisSession, FinalDecision
from backend.shared.services.base import BaseService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
def mock_db():
    db = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def analysis_service(mock_analysis_dao):
    return AnalysisService(mock_analysis_dao)


@pytest.fixture
def sample_session():
    return AnalysisSession(
        id=uuid4(),
        ticker="AAPL",
        market=Market.US,
        created_at=datetime.now(),
    )


@pytest.fixture
def sample_report():
    return AgentReport(
        id=uuid4(),
        session_id=uuid4(),
        agent_type=AgentType.FUNDAMENTAL,
        report_data={"pe_ratio": 22.5},
        created_at=datetime.now(),
    )


@pytest.fixture
def sample_decision():
    return FinalDecision(
        id=uuid4(),
        session_id=uuid4(),
        action=Action.BUY,
        confidence=0.82,
        rationale="Strong fundamentals and positive sentiment.",
        vetoed=False,
        created_at=datetime.now(),
    )


# ---------------------------------------------------------------------------
# Service initialisation
# ---------------------------------------------------------------------------


def test_dao_stored_on_service(mock_analysis_dao):
    """Constructor stores the DAO on the service instance."""
    service = AnalysisService(mock_analysis_dao)
    assert service.analysis_dao is mock_analysis_dao


def test_inherits_from_base_service(mock_analysis_dao):
    """AnalysisService inherits from BaseService."""
    service = AnalysisService(mock_analysis_dao)
    assert isinstance(service, BaseService)


# ---------------------------------------------------------------------------
# create_analysis_session
# ---------------------------------------------------------------------------


async def test_create_session_success(
    analysis_service, mock_analysis_dao, mock_db, sample_session
):
    """Happy path: DAO creates session, db is committed and refreshed."""
    mock_analysis_dao.create_session.return_value = sample_session

    result = await analysis_service.create_analysis_session(
        ticker="AAPL",
        market=Market.US,
        user_id=None,
        db=mock_db,
    )

    assert result is sample_session
    mock_analysis_dao.create_session.assert_awaited_once_with("AAPL", Market.US, None)
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once_with(sample_session)


async def test_create_session_with_user_id(
    analysis_service, mock_analysis_dao, mock_db, sample_session
):
    """create_session is called with the user_id when supplied."""
    user_id = uuid4()
    mock_analysis_dao.create_session.return_value = sample_session

    await analysis_service.create_analysis_session(
        ticker="TSLA",
        market=Market.US,
        user_id=user_id,
        db=mock_db,
    )

    mock_analysis_dao.create_session.assert_awaited_once_with(
        "TSLA", Market.US, user_id
    )


async def test_create_session_tase_market(
    analysis_service, mock_analysis_dao, mock_db, sample_session
):
    """Accepts TASE market enum value without error."""
    mock_analysis_dao.create_session.return_value = sample_session

    result = await analysis_service.create_analysis_session(
        ticker="TEVA",
        market=Market.TASE,
        user_id=None,
        db=mock_db,
    )

    assert result is sample_session
    mock_analysis_dao.create_session.assert_awaited_once_with("TEVA", Market.TASE, None)


async def test_create_session_dao_failure_raises_analysis_error(
    analysis_service, mock_analysis_dao, mock_db
):
    """DAO exception triggers rollback and re-raises as AnalysisError."""
    mock_analysis_dao.create_session.side_effect = RuntimeError("DB unavailable")

    with pytest.raises(
        AnalysisError, match="Failed to create analysis session for AAPL"
    ):
        await analysis_service.create_analysis_session(
            ticker="AAPL",
            market=Market.US,
            user_id=None,
            db=mock_db,
        )

    mock_db.rollback.assert_awaited_once()
    mock_db.commit.assert_not_awaited()


async def test_create_session_failure_includes_ticker(
    analysis_service, mock_analysis_dao, mock_db
):
    """Error message includes the ticker symbol."""
    mock_analysis_dao.create_session.side_effect = Exception("timeout")

    with pytest.raises(AnalysisError, match="MSFT"):
        await analysis_service.create_analysis_session(
            ticker="MSFT",
            market=Market.US,
            user_id=None,
            db=mock_db,
        )


# ---------------------------------------------------------------------------
# save_agent_report
# ---------------------------------------------------------------------------


async def test_save_agent_report_success(
    analysis_service, mock_analysis_dao, mock_db, sample_session, sample_report
):
    """Happy path: session found, report saved, db committed and refreshed."""
    session_id = sample_session.id
    mock_analysis_dao.get_by_id.return_value = sample_session
    mock_analysis_dao.add_report.return_value = sample_report
    report_data = {"pe_ratio": 22.5}

    result = await analysis_service.save_agent_report(
        session_id=session_id,
        agent_type=AgentType.FUNDAMENTAL,
        report_data=report_data,
        db=mock_db,
    )

    assert result is sample_report
    mock_analysis_dao.get_by_id.assert_awaited_once_with(session_id)
    mock_analysis_dao.add_report.assert_awaited_once_with(
        session_id, AgentType.FUNDAMENTAL, report_data
    )
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once_with(sample_report)


async def test_save_agent_report_session_not_found(
    analysis_service, mock_analysis_dao, mock_db
):
    """Returns None from get_by_id → AnalysisSessionNotFoundError."""
    session_id = uuid4()
    mock_analysis_dao.get_by_id.return_value = None

    with pytest.raises(AnalysisSessionNotFoundError):
        await analysis_service.save_agent_report(
            session_id=session_id,
            agent_type=AgentType.SENTIMENT,
            report_data={},
            db=mock_db,
        )

    mock_db.commit.assert_not_awaited()
    mock_db.rollback.assert_not_awaited()


async def test_save_agent_report_not_found_is_not_wrapped(
    analysis_service, mock_analysis_dao, mock_db
):
    """AnalysisSessionNotFoundError propagates as-is, not wrapped in AnalysisError."""
    mock_analysis_dao.get_by_id.return_value = None

    caught = None
    try:
        await analysis_service.save_agent_report(
            session_id=uuid4(),
            agent_type=AgentType.RISK_MANAGER,
            report_data={},
            db=mock_db,
        )
    except AnalysisSessionNotFoundError as e:
        caught = e

    assert caught is not None
    assert type(caught) is AnalysisSessionNotFoundError


async def test_save_agent_report_dao_failure_rolls_back(
    analysis_service, mock_analysis_dao, mock_db, sample_session
):
    """Exception from add_report triggers rollback and wraps as AnalysisError."""
    session_id = sample_session.id
    mock_analysis_dao.get_by_id.return_value = sample_session
    mock_analysis_dao.add_report.side_effect = Exception("flush failed")

    with pytest.raises(AnalysisError, match="Failed to save"):
        await analysis_service.save_agent_report(
            session_id=session_id,
            agent_type=AgentType.TECHNICAL,
            report_data={"rsi": 45},
            db=mock_db,
        )

    mock_db.rollback.assert_awaited_once()
    mock_db.commit.assert_not_awaited()


async def test_save_agent_report_all_agent_types(
    analysis_service, mock_analysis_dao, mock_db, sample_session, sample_report
):
    """Each AgentType can be passed without raising."""
    mock_analysis_dao.get_by_id.return_value = sample_session
    mock_analysis_dao.add_report.return_value = sample_report

    for agent_type in AgentType:
        mock_analysis_dao.add_report.reset_mock()
        await analysis_service.save_agent_report(
            session_id=sample_session.id,
            agent_type=agent_type,
            report_data={"key": "value"},
            db=mock_db,
        )
        mock_analysis_dao.add_report.assert_awaited_once()


# ---------------------------------------------------------------------------
# save_final_decision
# ---------------------------------------------------------------------------


async def test_save_final_decision_success_with_db(
    analysis_service, mock_analysis_dao, mock_db, sample_session, sample_decision
):
    """Happy path with db: session found, decision saved, db committed and refreshed."""
    session_id = sample_session.id
    mock_analysis_dao.get_by_id.return_value = sample_session
    mock_analysis_dao.add_decision.return_value = sample_decision

    result = await analysis_service.save_final_decision(
        session_id=session_id,
        action=Action.BUY,
        confidence=0.82,
        rationale="Strong fundamentals.",
        db=mock_db,
    )

    assert result is sample_decision
    mock_analysis_dao.add_decision.assert_awaited_once_with(
        session_id=session_id,
        action=Action.BUY,
        confidence=0.82,
        rationale="Strong fundamentals.",
        vetoed=False,
        veto_reason=None,
    )
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once_with(sample_decision)


async def test_save_final_decision_success_without_db(
    analysis_service, mock_analysis_dao, sample_session, sample_decision
):
    """Happy path without db: no commit or refresh called."""
    session_id = sample_session.id
    mock_analysis_dao.get_by_id.return_value = sample_session
    mock_analysis_dao.add_decision.return_value = sample_decision

    result = await analysis_service.save_final_decision(
        session_id=session_id,
        action=Action.HOLD,
        confidence=0.55,
        rationale="Neutral signals.",
        db=None,
    )

    assert result is sample_decision
    mock_analysis_dao.add_decision.assert_awaited_once()


async def test_save_final_decision_session_not_found(
    analysis_service, mock_analysis_dao, mock_db
):
    """Returns None from get_by_id → AnalysisSessionNotFoundError."""
    mock_analysis_dao.get_by_id.return_value = None

    with pytest.raises(AnalysisSessionNotFoundError):
        await analysis_service.save_final_decision(
            session_id=uuid4(),
            action=Action.SELL,
            confidence=0.7,
            rationale="Bearish signals.",
            db=mock_db,
        )

    mock_db.commit.assert_not_awaited()
    mock_db.rollback.assert_not_awaited()


async def test_save_final_decision_not_found_without_db(
    analysis_service, mock_analysis_dao
):
    """Returns None from get_by_id without db → AnalysisSessionNotFoundError."""
    mock_analysis_dao.get_by_id.return_value = None

    with pytest.raises(AnalysisSessionNotFoundError):
        await analysis_service.save_final_decision(
            session_id=uuid4(),
            action=Action.BUY,
            confidence=0.8,
            rationale="Test.",
            db=None,
        )


async def test_save_final_decision_dao_failure_with_db_rolls_back(
    analysis_service, mock_analysis_dao, mock_db, sample_session
):
    """Exception from add_decision with db provided triggers rollback."""
    mock_analysis_dao.get_by_id.return_value = sample_session
    mock_analysis_dao.add_decision.side_effect = Exception("insert failed")

    with pytest.raises(AnalysisError, match="Failed to save final decision"):
        await analysis_service.save_final_decision(
            session_id=sample_session.id,
            action=Action.BUY,
            confidence=0.8,
            rationale="Test.",
            db=mock_db,
        )

    mock_db.rollback.assert_awaited_once()
    mock_db.commit.assert_not_awaited()


async def test_save_final_decision_dao_failure_without_db_no_rollback(
    analysis_service, mock_analysis_dao, sample_session
):
    """Exception from add_decision without db: no rollback, still raises AnalysisError."""
    mock_analysis_dao.get_by_id.return_value = sample_session
    mock_analysis_dao.add_decision.side_effect = Exception("insert failed")

    with pytest.raises(AnalysisError):
        await analysis_service.save_final_decision(
            session_id=sample_session.id,
            action=Action.BUY,
            confidence=0.8,
            rationale="Test.",
            db=None,
        )


async def test_save_final_decision_vetoed_forwarded(
    analysis_service, mock_analysis_dao, mock_db, sample_session, sample_decision
):
    """vetoed=True and veto_reason are forwarded to the DAO."""
    mock_analysis_dao.get_by_id.return_value = sample_session
    mock_analysis_dao.add_decision.return_value = sample_decision

    await analysis_service.save_final_decision(
        session_id=sample_session.id,
        action=Action.HOLD,
        confidence=0.6,
        rationale="Risk veto applied.",
        vetoed=True,
        veto_reason="Sector concentration too high.",
        db=mock_db,
    )

    mock_analysis_dao.add_decision.assert_awaited_once_with(
        session_id=sample_session.id,
        action=Action.HOLD,
        confidence=0.6,
        rationale="Risk veto applied.",
        vetoed=True,
        veto_reason="Sector concentration too high.",
    )


async def test_save_final_decision_default_vetoed_is_false(
    analysis_service, mock_analysis_dao, mock_db, sample_session, sample_decision
):
    """vetoed defaults to False when not provided."""
    mock_analysis_dao.get_by_id.return_value = sample_session
    mock_analysis_dao.add_decision.return_value = sample_decision

    await analysis_service.save_final_decision(
        session_id=sample_session.id,
        action=Action.BUY,
        confidence=0.9,
        rationale="Unanimous buy.",
        db=mock_db,
    )

    call_kwargs = mock_analysis_dao.add_decision.call_args.kwargs
    assert call_kwargs["vetoed"] is False
    assert call_kwargs["veto_reason"] is None


# ---------------------------------------------------------------------------
# get_analysis_session
# ---------------------------------------------------------------------------


async def test_get_analysis_session_success(
    analysis_service, mock_analysis_dao, sample_session
):
    """Happy path: session found and returned."""
    session_id = sample_session.id
    mock_analysis_dao.get_by_id.return_value = sample_session

    result = await analysis_service.get_analysis_session(session_id)

    assert result is sample_session
    mock_analysis_dao.get_by_id.assert_awaited_once_with(session_id)


async def test_get_analysis_session_not_found(analysis_service, mock_analysis_dao):
    """Returns None from DAO → AnalysisSessionNotFoundError."""
    session_id = uuid4()
    mock_analysis_dao.get_by_id.return_value = None

    with pytest.raises(AnalysisSessionNotFoundError, match=str(session_id)):
        await analysis_service.get_analysis_session(session_id)


async def test_get_analysis_session_not_found_exact_type(
    analysis_service, mock_analysis_dao
):
    """AnalysisSessionNotFoundError propagates as-is, not wrapped."""
    mock_analysis_dao.get_by_id.return_value = None

    caught = None
    try:
        await analysis_service.get_analysis_session(uuid4())
    except AnalysisSessionNotFoundError as e:
        caught = e

    assert caught is not None
    assert type(caught) is AnalysisSessionNotFoundError


async def test_get_analysis_session_dao_error_raises_analysis_error(
    analysis_service, mock_analysis_dao
):
    """Exception from DAO is wrapped as AnalysisError."""
    session_id = uuid4()
    mock_analysis_dao.get_by_id.side_effect = RuntimeError("connection lost")

    with pytest.raises(AnalysisError, match="Failed to fetch analysis session"):
        await analysis_service.get_analysis_session(session_id)


# ---------------------------------------------------------------------------
# get_user_analysis_history
# ---------------------------------------------------------------------------


async def test_get_user_analysis_history_success(
    analysis_service, mock_analysis_dao, sample_session
):
    """Happy path: sessions returned from DAO."""
    user_id = uuid4()
    mock_analysis_dao.get_user_sessions.return_value = [sample_session]

    result = await analysis_service.get_user_analysis_history(user_id)

    assert result == [sample_session]
    mock_analysis_dao.get_user_sessions.assert_awaited_once_with(user_id, 50)


async def test_get_user_analysis_history_default_limit(
    analysis_service, mock_analysis_dao
):
    """Default limit parameter is 50."""
    user_id = uuid4()
    mock_analysis_dao.get_user_sessions.return_value = []

    await analysis_service.get_user_analysis_history(user_id)

    args = mock_analysis_dao.get_user_sessions.call_args.args
    assert args[1] == 50


async def test_get_user_analysis_history_custom_limit(
    analysis_service, mock_analysis_dao
):
    """Custom limit is forwarded to the DAO."""
    user_id = uuid4()
    mock_analysis_dao.get_user_sessions.return_value = []

    await analysis_service.get_user_analysis_history(user_id, limit=10)

    mock_analysis_dao.get_user_sessions.assert_awaited_once_with(user_id, 10)


async def test_get_user_analysis_history_empty(analysis_service, mock_analysis_dao):
    """Empty list is returned when no sessions exist."""
    user_id = uuid4()
    mock_analysis_dao.get_user_sessions.return_value = []

    result = await analysis_service.get_user_analysis_history(user_id)

    assert result == []


async def test_get_user_analysis_history_multiple(analysis_service, mock_analysis_dao):
    """Multiple sessions are returned correctly."""
    user_id = uuid4()
    sessions = [
        AnalysisSession(
            id=uuid4(), ticker="AAPL", market=Market.US, created_at=datetime.now()
        ),
        AnalysisSession(
            id=uuid4(), ticker="TSLA", market=Market.US, created_at=datetime.now()
        ),
    ]
    mock_analysis_dao.get_user_sessions.return_value = sessions

    result = await analysis_service.get_user_analysis_history(user_id)

    assert len(result) == 2


async def test_get_user_analysis_history_dao_error(analysis_service, mock_analysis_dao):
    """Exception from DAO is wrapped as AnalysisError."""
    user_id = uuid4()
    mock_analysis_dao.get_user_sessions.side_effect = RuntimeError("query failed")

    with pytest.raises(AnalysisError, match="Failed to fetch analysis history"):
        await analysis_service.get_user_analysis_history(user_id)


async def test_get_user_analysis_history_error_includes_user_id(
    analysis_service, mock_analysis_dao
):
    """Error message includes the user_id."""
    user_id = uuid4()
    mock_analysis_dao.get_user_sessions.side_effect = RuntimeError("timeout")

    with pytest.raises(AnalysisError, match=str(user_id)):
        await analysis_service.get_user_analysis_history(user_id)


# ---------------------------------------------------------------------------
# get_recent_outcomes
# ---------------------------------------------------------------------------


async def test_get_recent_outcomes_success(
    analysis_service, mock_analysis_dao, sample_session
):
    """Happy path: recent sessions returned from DAO."""
    mock_analysis_dao.get_recent_sessions.return_value = [sample_session]

    result = await analysis_service.get_recent_outcomes()

    assert result == [sample_session]
    mock_analysis_dao.get_recent_sessions.assert_awaited_once_with(50)


async def test_get_recent_outcomes_default_limit(analysis_service, mock_analysis_dao):
    """Default limit parameter is 50."""
    mock_analysis_dao.get_recent_sessions.return_value = []

    await analysis_service.get_recent_outcomes()

    args = mock_analysis_dao.get_recent_sessions.call_args.args
    assert args[0] == 50


async def test_get_recent_outcomes_custom_limit(analysis_service, mock_analysis_dao):
    """Custom limit is forwarded to the DAO."""
    mock_analysis_dao.get_recent_sessions.return_value = []

    await analysis_service.get_recent_outcomes(limit=20)

    mock_analysis_dao.get_recent_sessions.assert_awaited_once_with(20)


async def test_get_recent_outcomes_empty(analysis_service, mock_analysis_dao):
    """Empty list is returned when no recent sessions exist."""
    mock_analysis_dao.get_recent_sessions.return_value = []

    result = await analysis_service.get_recent_outcomes()

    assert result == []


async def test_get_recent_outcomes_dao_error(analysis_service, mock_analysis_dao):
    """Exception from DAO is wrapped as AnalysisError."""
    mock_analysis_dao.get_recent_sessions.side_effect = Exception("network error")

    with pytest.raises(AnalysisError, match="Failed to fetch recent outcomes"):
        await analysis_service.get_recent_outcomes()


async def test_get_recent_outcomes_error_wraps_original(
    analysis_service, mock_analysis_dao
):
    """The AnalysisError wraps the original exception message."""
    mock_analysis_dao.get_recent_sessions.side_effect = Exception("specific db error")

    with pytest.raises(AnalysisError, match="specific db error"):
        await analysis_service.get_recent_outcomes()
