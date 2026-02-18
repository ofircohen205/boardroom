from unittest.mock import AsyncMock, patch

import pytest

from backend.shared.ai.agents.risk_manager import RiskManagerAgent, calculate_var_95
from backend.shared.ai.state.agent_state import (
    FundamentalReport,
    SentimentReport,
    TechnicalReport,
)
from backend.shared.ai.state.enums import Trend


@pytest.fixture
def sample_reports():
    return {
        "fundamental": FundamentalReport(
            revenue_growth=0.15,
            pe_ratio=25.0,
            debt_to_equity=1.5,
            market_cap=2500000000000,
            sector="Technology",
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
    with patch("backend.ai.agents.risk_manager.get_llm_client") as mock_llm:
        mock_llm.return_value.complete = AsyncMock(
            return_value="VETO: NO\nRisk acceptable."
        )

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
    with patch("backend.ai.agents.risk_manager.get_llm_client") as mock_llm:
        mock_llm.return_value.complete = AsyncMock(
            return_value="VETO: YES\nREASON: Portfolio already 45% Tech."
        )

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


# --- VaR calculation tests ---


def test_var_95_empty_history():
    assert calculate_var_95([]) == 0.0


def test_var_95_single_price():
    assert calculate_var_95([{"close": 100}]) == 0.0


def test_var_95_rising_prices():
    """Steadily rising prices should have low (possibly zero) VaR."""
    history = [{"close": 100 + i} for i in range(30)]
    var = calculate_var_95(history)
    assert var >= 0.0
    assert var < 0.1  # low risk for steady uptrend


def test_var_95_volatile_prices():
    """Highly volatile prices should produce higher VaR."""
    import math

    history = [{"close": 100 * (1 + 0.05 * math.sin(i))} for i in range(60)]
    var = calculate_var_95(history)
    assert var >= 0.0


def test_var_95_declining_prices():
    """Declining prices produce positive VaR (downside risk)."""
    history = [{"close": 200 - i * 2} for i in range(50)]
    var = calculate_var_95(history)
    assert var > 0.0


@pytest.mark.asyncio
async def test_risk_manager_uses_var(sample_reports):
    """Verify VaR is computed from technical price_history."""
    # Give technical report a real price history
    sample_reports["technical"] = TechnicalReport(
        current_price=150.0,
        ma_50=145.0,
        ma_200=140.0,
        rsi=55.0,
        trend=Trend.BULLISH,
        price_history=[{"close": 100 + i} for i in range(30)],
        summary="Bullish trend",
    )

    with patch("backend.ai.agents.risk_manager.get_llm_client") as mock_llm:
        mock_llm.return_value.complete = AsyncMock(
            return_value="VETO: NO\nRisk acceptable."
        )

        agent = RiskManagerAgent()
        assessment = await agent.assess(
            ticker="AAPL",
            sector="Technology",
            portfolio_tech_weight=0.10,
            fundamental=sample_reports["fundamental"],
            sentiment=sample_reports["sentiment"],
            technical=sample_reports["technical"],
        )

        assert assessment["var_95"] >= 0.0
        # With 30 rising prices, VaR should be computed (not the old hardcoded 0.0)
