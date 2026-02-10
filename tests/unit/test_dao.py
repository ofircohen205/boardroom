from datetime import datetime
from uuid import uuid4

from backend.ai.state.enums import Action, AgentType, Market
from backend.db.models import AgentReport, AnalysisSession, FinalDecision


def test_analysis_session_creation():
    session = AnalysisSession(
        id=uuid4(),
        ticker="AAPL",
        market=Market.US,
        created_at=datetime.now(),
    )
    assert session.ticker == "AAPL"
    assert session.market == Market.US


def test_agent_report_creation():
    report = AgentReport(
        id=uuid4(),
        session_id=uuid4(),
        agent_type=AgentType.FUNDAMENTAL,
        report_data={"pe_ratio": 15.5},
        created_at=datetime.now(),
    )
    assert report.agent_type == AgentType.FUNDAMENTAL
    assert report.report_data["pe_ratio"] == 15.5


def test_final_decision_creation():
    decision = FinalDecision(
        id=uuid4(),
        session_id=uuid4(),
        action=Action.BUY,
        confidence=0.85,
        rationale="Strong fundamentals",
        vetoed=False,
        created_at=datetime.now(),
    )
    assert decision.action == Action.BUY
    assert decision.confidence == 0.85


# ============================================================================
# DAO Tests (Unit tests with mocks - no database required)
# ============================================================================

from unittest.mock import MagicMock


def test_user_dao_initialization():
    """Test UserDAO can be initialized."""
    from backend.dao.user import UserDAO
    from backend.db.models import User

    mock_session = MagicMock()
    dao = UserDAO.get_instance(mock_session)

    assert dao.session == mock_session
    assert dao.model == User


def test_watchlist_dao_initialization():
    """Test WatchlistDAO can be initialized."""
    from backend.dao.portfolio import WatchlistDAO
    from backend.db.models import Watchlist

    mock_session = MagicMock()
    dao = WatchlistDAO.get_instance(mock_session)

    assert dao.session == mock_session
    assert dao.model == Watchlist


def test_analysis_dao_initialization():
    """Test AnalysisDAO can be initialized."""
    from backend.dao.analysis import AnalysisDAO
    from backend.db.models import AnalysisSession

    mock_session = MagicMock()
    dao = AnalysisDAO(mock_session)

    assert dao.session == mock_session
    assert dao.model == AnalysisSession


def test_performance_dao_initialization():
    """Test PerformanceDAO can be initialized."""
    from backend.dao.performance import PerformanceDAO
    from backend.db.models import AnalysisOutcome

    mock_session = MagicMock()
    dao = PerformanceDAO.get_instance(mock_session)

    assert dao.session == mock_session
    assert dao.model == AnalysisOutcome


def test_dao_imports():
    """Test all DAOs can be imported from backend.dao."""
    from backend.dao import (
        AnalysisDAO,
        BaseDAO,
        PerformanceDAO,
        PortfolioDAO,
        UserDAO,
        WatchlistDAO,
    )

    # All imports should succeed
    assert BaseDAO is not None
    assert UserDAO is not None
    assert WatchlistDAO is not None
    assert PortfolioDAO is not None
    assert AnalysisDAO is not None
    assert PerformanceDAO is not None
