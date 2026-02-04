import pytest
from unittest.mock import AsyncMock, patch
from backend.tools.search import ExaSearchClient, SearchResult


@pytest.fixture
def mock_exa_response():
    return {
        "results": [
            {
                "title": "TEVA stock rises on news",
                "url": "https://example.com/news/1",
                "text": "Teva Pharmaceutical announced...",
                "published_date": "2026-02-01T10:00:00Z",
            }
        ]
    }


def test_search_result_structure():
    result = SearchResult(
        title="Test",
        url="https://example.com",
        snippet="Test snippet",
        published_at="2026-02-01T10:00:00Z",
        source="news",
    )
    assert result["title"] == "Test"
    assert result["source"] == "news"


@pytest.mark.asyncio
async def test_exa_search_formats_query():
    client = ExaSearchClient(api_key="test")
    with patch.object(client, "_search", new_callable=AsyncMock) as mock:
        mock.return_value = []
        await client.search_news("TEVA", hours=48)
        mock.assert_called_once()
        call_args = mock.call_args[0][0]
        assert "TEVA" in call_args
