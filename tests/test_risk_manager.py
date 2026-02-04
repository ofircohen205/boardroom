import pytest
from unittest.mock import AsyncMock, patch
from backend.agents.risk_manager import RiskManagerAgent
from backend.state.agent_state import FundamentalReport, SentimentReport, TechnicalReport
from backend.state.enums import Trend


@pytest.fixture
def sample_reports():
    return {
        "fundamental": FundamentalReport(
            revenue_growth=0.15,
            pe_ratio=25.0,
            debt_to_equity=1.5,
            market_cap=2500000000000,
            summary="Strong fundamentals",
        ),
        "sentiment": SentimentReport(
            overall_sentiment=0.6,
            news_items=[],
            social_mentions=[],
            summary="Positive sentiment",
        ),
        "technical": TechnicalReport(
            current_price=150.0,
            ma_50=145.0,
            ma_200=140.0,
            rsi=55.0,
            trend=Trend.BULLISH,
            price_history=[],
            summary="Bullish trend",
        ),
    }


@pytest.mark.asyncio
async def test_risk_manager_no_veto(sample_reports):
    with patch("backend.agents.risk_manager.get_llm_client") as mock_llm:
        mock_llm.return_value.complete = AsyncMock(return_value="VETO: NO\nRisk acceptable.")

        agent = RiskManagerAgent()
        assessment = await agent.assess(
            ticker="AAPL",
            sector="Technology",
            portfolio_tech_weight=0.20,
            fundamental=sample_reports["fundamental"],
            sentiment=sample_reports["sentiment"],
            technical=sample_reports["technical"],
        )

        assert assessment["veto"] is False


@pytest.mark.asyncio
async def test_risk_manager_veto_overweight():
    with patch("backend.agents.risk_manager.get_llm_client") as mock_llm:
        mock_llm.return_value.complete = AsyncMock(return_value="VETO: YES\nREASON: Portfolio already 45% Tech.")

        agent = RiskManagerAgent()
        assessment = await agent.assess(
            ticker="AAPL",
            sector="Technology",
            portfolio_tech_weight=0.45,
            fundamental=None,
            sentiment=None,
            technical=None,
        )

        assert assessment["veto"] is True
        assert "veto_reason" in assessment
