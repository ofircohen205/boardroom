"""Unit tests for backend.main (FastAPI health endpoints)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health check endpoints using a real TestClient with mocked deps."""

    @pytest.fixture(autouse=True)
    def mock_startup(self):
        """Prevent real startup side-effects (scheduler, Redis) during tests."""
        with (
            patch("backend.main.start_scheduler", new_callable=AsyncMock),
            patch("backend.main.stop_scheduler", new_callable=AsyncMock),
            patch("backend.main.get_cache") as mock_cache_factory,
        ):
            mock_cache = MagicMock()
            mock_cache._ensure_connection = AsyncMock()
            mock_cache.close = AsyncMock()
            mock_cache.stats = AsyncMock(
                return_value={"connected": True, "backend": "redis"}
            )
            mock_cache_factory.return_value = mock_cache
            self.mock_cache = mock_cache
            yield

    @pytest.fixture
    def client(self):
        from backend.main import app

        with TestClient(app, raise_server_exceptions=False) as c:
            yield c

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_db_health_healthy(self, client):
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()

        async def override_get_db():
            yield mock_session

        from backend.main import app
        from backend.shared.db import get_db

        app.dependency_overrides[get_db] = override_get_db

        response = client.get("/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "postgres"

        app.dependency_overrides.clear()

    def test_db_health_unhealthy(self, client):
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("connection refused"))

        async def override_get_db():
            yield mock_session

        from backend.main import app
        from backend.shared.db import get_db

        app.dependency_overrides[get_db] = override_get_db

        response = client.get("/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "connection refused" in data["error"]

        app.dependency_overrides.clear()

    def test_cache_health_connected(self, client):
        self.mock_cache.stats = AsyncMock(
            return_value={"connected": True, "backend": "redis"}
        )

        response = client.get("/health/cache")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "redis"

    def test_cache_health_degraded_when_not_connected(self, client):
        self.mock_cache.stats = AsyncMock(
            return_value={"connected": False, "backend": "memory"}
        )

        response = client.get("/health/cache")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"

    def test_cache_health_unhealthy_on_exception(self, client):
        self.mock_cache.stats = AsyncMock(side_effect=Exception("redis down"))

        response = client.get("/health/cache")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "redis down" in data["error"]
