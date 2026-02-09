import pytest
from unittest.mock import AsyncMock, patch
from backend.ai.agents.technical import TechnicalAgent
from backend.ai.state.enums import Market, Trend


@pytest.fixture
def mock_stock_data():
    prices = [100 + i * 0.5 for i in range(100)]
    return {
        "ticker": "AAPL",
        "market": Market.US,
        "current_price": 150.0,
        "price_history": [{"close": p} for p in prices],
    }


@pytest.mark.asyncio
async def test_technical_agent_analyze(mock_stock_data):
    with patch("backend.ai.agents.technical.get_market_data_client") as mock_market:
        with patch("backend.ai.agents.technical.get_llm_client") as mock_llm:
            mock_market.return_value.get_stock_data = AsyncMock(return_value=mock_stock_data)
            mock_llm.return_value.complete = AsyncMock(return_value="Bullish trend with strong momentum.")

            agent = TechnicalAgent()
            report = await agent.analyze("AAPL", Market.US)

            assert "current_price" in report
            assert "ma_50" in report
            assert "ma_200" in report
            assert "rsi" in report
            assert "trend" in report
