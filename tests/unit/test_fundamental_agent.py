from unittest.mock import AsyncMock, patch

import pytest

from backend.shared.ai.agents.fundamental import FundamentalAgent
from backend.shared.ai.state.enums import Market


@pytest.fixture
def mock_stock_data():
    return {
        "ticker": "AAPL",
        "market": Market.US,
        "current_price": 150.0,
        "pe_ratio": 25.0,
        "revenue_growth": 0.15,
        "debt_to_equity": 1.5,
        "market_cap": 2500000000000,
        "sector": "Technology",
        "price_history": [],
    }


@pytest.fixture
def mock_llm_response():
    return "Apple shows strong fundamentals with healthy revenue growth of 15%."


@pytest.mark.asyncio
async def test_fundamental_agent_analyze(mock_stock_data, mock_llm_response):
    with patch("backend.ai.agents.fundamental.get_market_data_client") as mock_market:
        with patch("backend.ai.agents.fundamental.get_llm_client") as mock_llm:
            mock_market.return_value.get_stock_data = AsyncMock(
                return_value=mock_stock_data
            )

            # Mock the LiteLLMClient instance
            mock_client_instance = AsyncMock()

            # We can simply mock the complete method directly as before,
            # which isolates the agent test from the client implementation details.
            # This is the cleanest approach for unit testing the AGENT.
            # The previous change to mock _router was too coupled to implementation.
            # Reverting to simple interface mocking is better.
            mock_client_instance.complete = AsyncMock(return_value=mock_llm_response)
            mock_llm.return_value = mock_client_instance

            agent = FundamentalAgent()
            report = await agent.analyze("AAPL", Market.US)

            assert report["pe_ratio"] == 25.0
            assert report["revenue_growth"] == 0.15
            assert "summary" in report
