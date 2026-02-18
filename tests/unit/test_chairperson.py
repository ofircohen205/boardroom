from unittest.mock import AsyncMock, patch

import pytest

from backend.shared.ai.agents.chairperson import ChairpersonAgent
from backend.shared.ai.state.agent_state import (
    FundamentalReport,
    SentimentReport,
    TechnicalReport,
)
from backend.shared.ai.state.enums import Action, Trend


@pytest.fixture
def bullish_reports():
    return {
        "fundamental": FundamentalReport(
            revenue_growth=0.20,
            pe_ratio=20.0,
            debt_to_equity=0.5,
            market_cap=2500000000000,
            summary="Excellent fundamentals",
        ),
        "sentiment": SentimentReport(
            overall_sentiment=0.8,
            news_items=[],
            social_mentions=[],
            summary="Very positive sentiment",
        ),
        "technical": TechnicalReport(
            current_price=150.0,
            ma_50=145.0,
            ma_200=140.0,
            rsi=55.0,
            trend=Trend.BULLISH,
            price_history=[],
            summary="Strong uptrend",
        ),
    }


@pytest.mark.asyncio
async def test_chairperson_buy_decision(bullish_reports):
    with patch("backend.ai.agents.chairperson.get_llm_client") as mock_llm:
        mock_llm.return_value.complete = AsyncMock(
            return_value="ACTION: BUY\nCONFIDENCE: 0.85\nRATIONALE: Strong fundamentals and positive sentiment."
        )

        agent = ChairpersonAgent()
        decision = await agent.decide(
            ticker="AAPL",
            fundamental=bullish_reports["fundamental"],
            sentiment=bullish_reports["sentiment"],
            technical=bullish_reports["technical"],
        )

        assert decision["action"] == Action.BUY
        assert decision["confidence"] > 0.5
