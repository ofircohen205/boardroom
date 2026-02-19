from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app


@pytest.mark.asyncio
async def test_db_health_check_success(test_db_session):
    """Test /health/db returns 200 and healthy status."""
    from backend.shared.db import get_db

    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "postgres"

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_cache_health_check_success():
    """Test /health/cache returns 200 and healthy/degraded status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/cache")
        assert response.status_code == 200
        data = response.json()
        # It might be healthy or degraded depending on if redis is actually running in the test env
        assert data["status"] in ["healthy", "degraded"]
        assert data["service"] == "redis"
        assert "stats" in data


@pytest.mark.asyncio
async def test_db_health_check_failure():
    """Test /health/db returns unhealthy when DB is down."""
    from backend.shared.db import get_db

    async def override_get_db_failure():
        mock_session = MagicMock()
        # Mock execute to be an async function that raises exception
        mock_session.execute = MagicMock(side_effect=Exception("DB Connection Failed"))

        # Make the mock awaitable (since session.execute is awaited)
        async def async_execute(*args, **kwargs):
            raise Exception("DB Connection Failed")

        mock_session.execute = async_execute
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db_failure

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/db")
        # The endpoint catches exception and returns 200 with unhealthy status
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["service"] == "postgres"
        assert "DB Connection Failed" in data["error"]

    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_cache_health_check_failure():
    """Test /health/cache returns unhealthy when Cache check raises exception."""
    with patch("backend.main.get_cache") as mock_get_cache:
        mock_cache_instance = MagicMock()
        mock_cache_instance.stats.side_effect = Exception("Redis Connection Failed")
        mock_get_cache.return_value = mock_cache_instance

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health/cache")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["service"] == "redis"
            assert "Redis Connection Failed" in data["error"]
