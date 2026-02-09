import pytest
from datetime import datetime
from uuid import uuid4
from backend.db.models import AnalysisSession, AgentReport, FinalDecision
from backend.state.enums import Market, AgentType, Action


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
