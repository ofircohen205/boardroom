"""Unit tests for backend.shared.ai.tools.search (OpenAISearchClient)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.shared.ai.tools.search import OpenAISearchClient, get_search_client


def _make_annotation(url: str, title: str, start_index: int = 10):
    ann = MagicMock()
    ann.url = url
    ann.title = title
    ann.start_index = start_index
    return ann


def _make_response_output(
    annotations: list, text: str = "sample text for context " * 20
):
    block = MagicMock()
    block.text = text
    block.annotations = annotations

    msg = MagicMock()
    msg.type = "message"
    msg.content = [block]

    response = MagicMock()
    response.output = [msg]
    return response


class TestOpenAISearchClientInit:
    def test_uses_provided_api_key(self):
        client = OpenAISearchClient(api_key="my-key")  # pragma: allowlist secret
        assert client.api_key == "my-key"  # pragma: allowlist secret
        assert client._client is None

    def test_reads_settings_when_key_is_none(self):
        with patch("backend.shared.ai.tools.search.settings") as mock_settings:
            mock_settings.openai_api_key.get_secret_value.return_value = "settings-key"
            client = OpenAISearchClient()
        assert client.api_key == "settings-key"  # pragma: allowlist secret


class TestOpenAISearchClientProperty:
    def test_client_property_creates_client_lazily(self):
        client = OpenAISearchClient(api_key="key")  # pragma: allowlist secret
        assert client._client is None
        with patch("backend.shared.ai.tools.search.AsyncOpenAI") as mock_cls:
            mock_cls.return_value = MagicMock()
            c = client.client
            assert c is client._client
            mock_cls.assert_called_once_with(api_key="key")  # pragma: allowlist secret

    def test_client_property_returns_same_instance_on_second_call(self):
        client = OpenAISearchClient(api_key="key")  # pragma: allowlist secret
        with patch("backend.shared.ai.tools.search.AsyncOpenAI") as mock_cls:
            mock_cls.return_value = MagicMock()
            c1 = client.client
            c2 = client.client
            assert c1 is c2
            mock_cls.assert_called_once()


class TestOpenAISearchClientSearch:
    @pytest.mark.asyncio
    async def test_search_extracts_results_from_annotations(self):
        client = OpenAISearchClient(api_key="key")  # pragma: allowlist secret

        anns = [
            _make_annotation("https://example.com/1", "Article One"),
            _make_annotation("https://example.com/2", "Article Two"),
        ]
        response = _make_response_output(anns)

        mock_openai = MagicMock()
        mock_openai.responses.create = AsyncMock(return_value=response)
        client._client = mock_openai

        results = await client._search("AAPL news", num_results=10)
        assert len(results) == 2
        urls = [r["url"] for r in results]
        assert "https://example.com/1" in urls
        assert "https://example.com/2" in urls

    @pytest.mark.asyncio
    async def test_search_deduplicates_urls(self):
        client = OpenAISearchClient(api_key="key")  # pragma: allowlist secret

        anns = [
            _make_annotation("https://example.com/same", "First"),
            _make_annotation("https://example.com/same", "Duplicate"),
        ]
        response = _make_response_output(anns)

        mock_openai = MagicMock()
        mock_openai.responses.create = AsyncMock(return_value=response)
        client._client = mock_openai

        results = await client._search("query")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_respects_num_results_limit(self):
        client = OpenAISearchClient(api_key="key")  # pragma: allowlist secret

        anns = [
            _make_annotation(f"https://example.com/{i}", f"Article {i}")
            for i in range(10)
        ]
        response = _make_response_output(anns)

        mock_openai = MagicMock()
        mock_openai.responses.create = AsyncMock(return_value=response)
        client._client = mock_openai

        results = await client._search("query", num_results=3)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_returns_empty_on_no_message_output(self):
        client = OpenAISearchClient(api_key="key")  # pragma: allowlist secret

        non_msg = MagicMock()
        non_msg.type = "tool_call"

        response = MagicMock()
        response.output = [non_msg]

        mock_openai = MagicMock()
        mock_openai.responses.create = AsyncMock(return_value=response)
        client._client = mock_openai

        results = await client._search("query")
        assert results == []


class TestOpenAISearchClientSearchNews:
    @pytest.mark.asyncio
    async def test_search_news_us_market(self):
        client = OpenAISearchClient(api_key="key")  # pragma: allowlist secret

        with patch.object(client, "_search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                {
                    "title": "AAPL up",
                    "url": "https://x.com",
                    "snippet": "...",
                    "published_at": "",
                    "source": "news",
                }
            ]
            results = await client.search_news("AAPL", market="US")

        call_query = mock_search.call_args[0][0]
        assert "TASE" not in call_query
        assert "AAPL" in call_query
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_news_tase_market_adds_context(self):
        client = OpenAISearchClient(api_key="key")  # pragma: allowlist secret

        with patch.object(client, "_search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            await client.search_news("TEVA", market="TASE")

        call_query = mock_search.call_args[0][0]
        assert "Israeli" in call_query or "Globes" in call_query


class TestOpenAISearchClientSearchSocial:
    @pytest.mark.asyncio
    async def test_search_social_tags_reddit_source(self):
        client = OpenAISearchClient(api_key="key")  # pragma: allowlist secret

        with patch.object(client, "_search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                {
                    "title": "Reddit post",
                    "url": "https://reddit.com/r/stocks",
                    "snippet": "...",
                    "published_at": "",
                    "source": "news",
                }
            ]
            results = await client.search_social("AAPL")

        assert results[0]["source"] == "reddit"

    @pytest.mark.asyncio
    async def test_search_social_tags_twitter_source(self):
        client = OpenAISearchClient(api_key="key")  # pragma: allowlist secret

        with patch.object(client, "_search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [
                {
                    "title": "Tweet",
                    "url": "https://twitter.com/user",
                    "snippet": "...",
                    "published_at": "",
                    "source": "news",
                }
            ]
            results = await client.search_social("AAPL")

        assert results[0]["source"] == "twitter"

    @pytest.mark.asyncio
    async def test_search_social_tase_context(self):
        client = OpenAISearchClient(api_key="key")  # pragma: allowlist secret

        with patch.object(client, "_search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            await client.search_social("TEVA", market="TASE")

        call_query = mock_search.call_args[0][0]
        assert "Israel" in call_query


class TestGetSearchClientFactory:
    def test_returns_openai_search_client_instance(self):
        client = get_search_client()
        assert isinstance(client, OpenAISearchClient)
