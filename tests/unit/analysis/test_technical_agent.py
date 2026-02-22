from unittest.mock import AsyncMock, patch

import pytest

from backend.shared.ai.agents.technical import TechnicalAgent
from backend.shared.ai.state.enums import Market


@pytest.fixture
def mock_stock_data():
    prices = [100 + i * 0.5 for i in range(100)]
    return {
        "ticker": "AAPL",
        "market": Market.US,
        "current_price": 150.0,
        "price_history": [
            {"close": p, "high": p + 1.0, "low": p - 1.0} for p in prices
        ],
    }


@pytest.mark.asyncio
async def test_technical_agent_analyze(mock_stock_data):
    with patch(
        "backend.shared.ai.agents.technical.get_market_data_client"
    ) as mock_market:
        with patch("backend.shared.ai.agents.technical.get_llm_client") as mock_llm:
            mock_market.return_value.get_stock_data = AsyncMock(
                return_value=mock_stock_data
            )

            # Mock the LiteLLMClient instance and its complete method
            mock_client_instance = AsyncMock()
            mock_client_instance.complete = AsyncMock(
                return_value="Bullish trend with strong momentum."
            )
            mock_llm.return_value = mock_client_instance

            agent = TechnicalAgent()
            report = await agent.analyze("AAPL", Market.US)

            assert "current_price" in report
            assert "ma_50" in report
            assert "ma_200" in report
            assert "rsi" in report
            assert "trend" in report
            assert "macd" in report
            assert "macd_signal" in report
            assert "macd_histogram" in report
            assert "bollinger_upper" in report
            assert "bollinger_lower" in report
            assert "bollinger_width_pct" in report
            assert "atr" in report
