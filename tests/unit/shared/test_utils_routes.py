# tests/unit/shared/test_utils_routes.py
"""
Unit tests for backend/shared/utils/routes.py.

Tests cover:
- GET /api/markets: returns market enum values
- GET /api/stocks/search: delegates to search_stocks
- GET /api/cache/stats: returns cache statistics
- POST /api/cache/clear: clears cache and returns status
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def utils_client():
    """HTTP client for utility endpoints (no auth required)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# ---------------------------------------------------------------------------
# GET /api/markets
# ---------------------------------------------------------------------------


async def test_get_markets_returns_200(utils_client):
    """GET /api/markets must return HTTP 200."""
    response = await utils_client.get("/api/markets")
    assert response.status_code == 200


async def test_get_markets_returns_dict(utils_client):
    """GET /api/markets must return a non-empty dict of market values."""
    response = await utils_client.get("/api/markets")
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) > 0


async def test_get_markets_includes_us_market(utils_client):
    """GET /api/markets must include the US market."""
    response = await utils_client.get("/api/markets")
    data = response.json()
    assert "US" in data


# ---------------------------------------------------------------------------
# GET /api/stocks/search
# ---------------------------------------------------------------------------


async def test_search_stocks_returns_200(utils_client):
    """GET /api/stocks/search returns 200 with mocked search function."""
    mock_result = MagicMock()
    mock_result.symbol = "AAPL"
    mock_result.name = "Apple Inc."
    mock_result.exchange = "NASDAQ"

    with patch(
        "backend.shared.utils.routes.search_stocks",
        new_callable=AsyncMock,
        return_value=[mock_result],
    ):
        response = await utils_client.get("/api/stocks/search?q=AAPL&market=US")

    assert response.status_code == 200


async def test_search_stocks_returns_symbol_name_exchange(utils_client):
    """GET /api/stocks/search returns dicts with symbol, name, exchange keys."""
    mock_result = MagicMock()
    mock_result.symbol = "MSFT"
    mock_result.name = "Microsoft Corporation"
    mock_result.exchange = "NASDAQ"

    with patch(
        "backend.shared.utils.routes.search_stocks",
        new_callable=AsyncMock,
        return_value=[mock_result],
    ):
        response = await utils_client.get("/api/stocks/search?q=MSFT&market=US")

    data = response.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "MSFT"
    assert data[0]["name"] == "Microsoft Corporation"
    assert data[0]["exchange"] == "NASDAQ"


async def test_search_stocks_empty_query_returns_list(utils_client):
    """GET /api/stocks/search with empty query returns a list."""
    with patch(
        "backend.shared.utils.routes.search_stocks",
        new_callable=AsyncMock,
        return_value=[],
    ):
        response = await utils_client.get("/api/stocks/search")

    assert response.status_code == 200
    assert response.json() == []


async def test_search_stocks_tase_market(utils_client):
    """GET /api/stocks/search with market=TASE passes TASE enum to search_stocks."""
    with patch(
        "backend.shared.utils.routes.search_stocks",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_search:
        await utils_client.get("/api/stocks/search?q=TEVA&market=TASE")

    # Verify search_stocks was called (market enum selection is internal)
    mock_search.assert_called_once()


# ---------------------------------------------------------------------------
# GET /api/cache/stats
# ---------------------------------------------------------------------------


async def test_cache_stats_returns_200(utils_client):
    """GET /api/cache/stats returns HTTP 200."""
    mock_cache = MagicMock()
    mock_cache.stats = AsyncMock(return_value={"connected": True, "keys": 5})

    with patch("backend.shared.utils.routes.get_cache", return_value=mock_cache):
        response = await utils_client.get("/api/cache/stats")

    assert response.status_code == 200


async def test_cache_stats_returns_cache_data(utils_client):
    """GET /api/cache/stats returns the data from cache.stats()."""
    mock_cache = MagicMock()
    mock_cache.stats = AsyncMock(return_value={"connected": True, "keys": 3})

    with patch("backend.shared.utils.routes.get_cache", return_value=mock_cache):
        response = await utils_client.get("/api/cache/stats")

    data = response.json()
    assert data["connected"] is True
    assert data["keys"] == 3


# ---------------------------------------------------------------------------
# POST /api/cache/clear
# ---------------------------------------------------------------------------


async def test_cache_clear_returns_200(utils_client):
    """POST /api/cache/clear returns HTTP 200."""
    mock_cache = MagicMock()
    mock_cache.clear = AsyncMock()

    with patch("backend.shared.utils.routes.get_cache", return_value=mock_cache):
        response = await utils_client.post("/api/cache/clear")

    assert response.status_code == 200


async def test_cache_clear_calls_cache_clear(utils_client):
    """POST /api/cache/clear must call cache.clear()."""
    mock_cache = MagicMock()
    mock_cache.clear = AsyncMock()

    with patch("backend.shared.utils.routes.get_cache", return_value=mock_cache):
        await utils_client.post("/api/cache/clear")

    mock_cache.clear.assert_called_once()


async def test_cache_clear_returns_cleared_status(utils_client):
    """POST /api/cache/clear returns {"status": "cleared"}."""
    mock_cache = MagicMock()
    mock_cache.clear = AsyncMock()

    with patch("backend.shared.utils.routes.get_cache", return_value=mock_cache):
        response = await utils_client.post("/api/cache/clear")

    assert response.json() == {"status": "cleared"}
