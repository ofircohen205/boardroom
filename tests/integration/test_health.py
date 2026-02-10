import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from unittest.mock import MagicMock, patch

@pytest.mark.asyncio
async def test_db_health_check_success():
    """Test /health/db returns 200 and healthy status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "postgres"

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
    with patch("backend.main.get_db") as mock_get_db:
        # Mock get_db to raise an exception
        mock_get_db.side_effect = Exception("DB Connection Failed")
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health/db")
            # The endpoint catches exception and returns 200 with unhealthy status
            assert response.status_code == 200 
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["service"] == "postgres"
            assert "DB Connection Failed" in data["error"]

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
