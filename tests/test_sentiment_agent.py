import pytest
from unittest.mock import AsyncMock, patch
from backend.agents.sentiment import SentimentAgent
from backend.state.enums import Market


@pytest.fixture
def mock_search_results():
    return [
        {
            "title": "Stock rises on good news",
            "url": "https://example.com/1",
            "snippet": "The company reported strong earnings...",
            "published_at": "2026-02-01T10:00:00Z",
            "source": "news",
        }
    ]


@pytest.mark.asyncio
async def test_sentiment_agent_analyze(mock_search_results):
    with patch("backend.agents.sentiment.get_search_client") as mock_search:
        with patch("backend.agents.sentiment.get_llm_client") as mock_llm:
            mock_search.return_value.search_news = AsyncMock(return_value=mock_search_results)
            mock_search.return_value.search_social = AsyncMock(return_value=[])
            mock_llm.return_value.complete = AsyncMock(return_value="SENTIMENT: 0.7\nSUMMARY: Positive news coverage.")

            agent = SentimentAgent()
            report = await agent.analyze("AAPL", Market.US)

            assert "overall_sentiment" in report
            assert "news_items" in report
            assert len(report["news_items"]) > 0
