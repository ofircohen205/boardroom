"""Unit tests for sectors API endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app


@pytest.fixture
async def sectors_client():
    """Client for sectors endpoints (no auth required)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


async def test_list_sectors(sectors_client):
    """GET /api/sectors/ returns list of available sectors."""
    response = await sectors_client.get("/api/sectors/")
    assert response.status_code == 200
    data = response.json()
    assert "sectors" in data
    assert len(data["sectors"]) > 0


async def test_list_sectors_contains_known_sector(sectors_client):
    """GET /api/sectors/ includes at least the technology sector."""
    response = await sectors_client.get("/api/sectors/")
    assert response.status_code == 200
    sectors = response.json()["sectors"]
    assert any("technology" in str(s).lower() for s in sectors)


async def test_compare_stocks_too_few_tickers(sectors_client):
    """POST /api/sectors/compare with only 1 ticker returns 422 (Pydantic min_length)."""
    with patch("backend.domains.sectors.api.endpoints.create_boardroom_graph"):
        response = await sectors_client.post(
            "/api/sectors/compare",
            json={"tickers": ["AAPL"], "market": "US"},
        )
    assert response.status_code == 422


async def test_compare_stocks_too_many_tickers(sectors_client):
    """POST /api/sectors/compare with 5 tickers returns 422 (Pydantic max_length)."""
    with patch("backend.domains.sectors.api.endpoints.create_boardroom_graph"):
        response = await sectors_client.post(
            "/api/sectors/compare",
            json={"tickers": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"], "market": "US"},
        )
    assert response.status_code == 422


async def test_compare_stocks_valid_returns_result(sectors_client):
    """POST /api/sectors/compare with 2 valid tickers returns comparison data."""
    mock_event = {
        "type": MagicMock(**{"value": "comparison_result"}),
        "data": {"rankings": ["AAPL", "MSFT"], "best_pick": "AAPL"},
    }

    async def fake_streaming(*args, **kwargs):
        yield mock_event

    mock_graph = MagicMock()
    mock_graph.run_comparison_streaming = fake_streaming

    with patch(
        "backend.domains.sectors.api.endpoints.create_boardroom_graph",
        return_value=mock_graph,
    ):
        response = await sectors_client.post(
            "/api/sectors/compare",
            json={"tickers": ["AAPL", "MSFT"], "market": "US"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "rankings" in data
    assert "best_pick" in data


async def test_compare_stocks_no_comparison_result_returns_500(sectors_client):
    """POST /api/sectors/compare with no comparison_result event returns 500."""

    async def fake_streaming_other_event(*args, **kwargs):
        yield {
            "type": MagicMock(**{"value": "other_event"}),
            "data": {},
        }

    mock_graph = MagicMock()
    mock_graph.run_comparison_streaming = fake_streaming_other_event

    with patch(
        "backend.domains.sectors.api.endpoints.create_boardroom_graph",
        return_value=mock_graph,
    ):
        response = await sectors_client.post(
            "/api/sectors/compare",
            json={"tickers": ["AAPL", "MSFT"], "market": "US"},
        )
    assert response.status_code == 500


async def test_analyze_sector_not_found(sectors_client):
    """POST /api/sectors/analyze with unknown sector returns 404."""
    with patch(
        "backend.domains.sectors.api.endpoints.get_sector_tickers",
        return_value=[],
    ):
        response = await sectors_client.post(
            "/api/sectors/analyze",
            json={"sector": "NonExistentSector99999", "market": "US", "limit": 5},
        )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


async def test_analyze_sector_valid_returns_result(sectors_client):
    """POST /api/sectors/analyze with valid sector returns comparison data with sector key."""
    mock_event = {
        "type": MagicMock(**{"value": "comparison_result"}),
        "data": {"rankings": ["AAPL", "MSFT"], "best_pick": "AAPL"},
    }

    async def fake_streaming(*args, **kwargs):
        yield mock_event

    mock_graph = MagicMock()
    mock_graph.run_comparison_streaming = fake_streaming

    with (
        patch(
            "backend.domains.sectors.api.endpoints.get_sector_tickers",
            return_value=["AAPL", "MSFT", "GOOGL"],
        ),
        patch(
            "backend.domains.sectors.api.endpoints.create_boardroom_graph",
            return_value=mock_graph,
        ),
    ):
        response = await sectors_client.post(
            "/api/sectors/analyze",
            json={"sector": "technology", "market": "US", "limit": 3},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["sector"] == "technology"
    assert "rankings" in data


async def test_analyze_sector_no_comparison_result_returns_500(sectors_client):
    """POST /api/sectors/analyze with no comparison_result event returns 500."""

    async def fake_streaming_empty(*args, **kwargs):
        return
        yield  # make it an async generator

    mock_graph = MagicMock()
    mock_graph.run_comparison_streaming = fake_streaming_empty

    with (
        patch(
            "backend.domains.sectors.api.endpoints.get_sector_tickers",
            return_value=["AAPL", "MSFT"],
        ),
        patch(
            "backend.domains.sectors.api.endpoints.create_boardroom_graph",
            return_value=mock_graph,
        ),
    ):
        response = await sectors_client.post(
            "/api/sectors/analyze",
            json={"sector": "technology", "market": "US", "limit": 2},
        )
    assert response.status_code == 500
