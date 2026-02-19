# tests/unit/test_api_performance.py
"""Unit tests for performance API endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from backend.dependencies import get_performance_service
from backend.main import app
from backend.shared.auth.dependencies import get_current_user
from backend.shared.db.database import get_db


@pytest.fixture
def mock_user():
    """A mock User that does not require a real database session."""
    user = MagicMock()
    user.id = uuid4()
    user.email = "perf-test@example.com"
    user.is_active = True
    return user


def _make_mock_db():
    """Create a mock async DB session that satisfies SQLAlchemy execute calls."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []

    mock_db = MagicMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.close = AsyncMock()
    return mock_db


@pytest.fixture
def mock_perf_svc():
    """Create a mock PerformanceService."""
    svc = MagicMock()
    svc.get_performance_summary = AsyncMock(
        return_value={
            "total_recommendations": 5,
            "correct_count": 3,
            "accuracy": 0.6,
            "by_action": {"BUY": {"total": 3, "correct": 2, "accuracy": 0.67}},
        }
    )
    svc.get_recent_outcomes = AsyncMock(
        return_value=[
            {
                "ticker": "AAPL",
                "action": "BUY",
                "price_at_recommendation": 150.0,
                "confidence": 0.85,
                "outcome_correct": True,
                "returns": {"1d": 0.03},
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ]
    )
    svc.performance_dao = MagicMock()
    svc.performance_dao.session = MagicMock()
    return svc


@pytest.fixture
async def perf_client(mock_user, mock_perf_svc):
    """AsyncClient with performance service and auth overridden."""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_performance_service] = lambda: mock_perf_svc
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def db_client(mock_user):
    """AsyncClient with auth and a mock DB session (no real DB needed)."""
    mock_db = _make_mock_db()
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


async def test_get_summary_returns_200(perf_client):
    """GET /api/performance/summary returns 200 with summary data."""
    response = await perf_client.get("/api/performance/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_recommendations"] == 5
    assert data["accuracy"] == pytest.approx(0.6)
    assert "by_action" in data


async def test_get_summary_calls_service(perf_client, mock_perf_svc):
    """GET /api/performance/summary calls service.get_performance_summary."""
    await perf_client.get("/api/performance/summary")
    mock_perf_svc.get_performance_summary.assert_called_once()


async def test_get_summary_service_error_returns_500(mock_user):
    """GET /api/performance/summary returns 500 when service raises exception."""
    mock_svc = MagicMock()
    mock_svc.get_performance_summary = AsyncMock(side_effect=RuntimeError("DB error"))
    mock_svc.performance_dao = MagicMock()
    mock_svc.performance_dao.session = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_performance_service] = lambda: mock_svc
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/performance/summary")
    app.dependency_overrides.clear()

    assert response.status_code == 500
    assert "DB error" in response.json()["detail"]


async def test_get_recent_returns_200(perf_client):
    """GET /api/performance/recent returns 200 with outcomes wrapped in dict."""
    response = await perf_client.get("/api/performance/recent")
    assert response.status_code == 200
    data = response.json()
    assert "outcomes" in data
    assert len(data["outcomes"]) == 1
    assert data["outcomes"][0]["ticker"] == "AAPL"


async def test_get_recent_with_ticker_filter(perf_client, mock_perf_svc):
    """GET /api/performance/recent?ticker=AAPL passes ticker to service."""
    response = await perf_client.get("/api/performance/recent?ticker=AAPL&limit=5")
    assert response.status_code == 200
    mock_perf_svc.get_recent_outcomes.assert_called_once()
    call_kwargs = mock_perf_svc.get_recent_outcomes.call_args
    assert call_kwargs.kwargs.get("ticker") == "AAPL"
    assert call_kwargs.kwargs.get("limit") == 5


async def test_get_recent_default_limit(perf_client, mock_perf_svc):
    """GET /api/performance/recent uses default limit of 20."""
    await perf_client.get("/api/performance/recent")
    call_kwargs = mock_perf_svc.get_recent_outcomes.call_args
    assert call_kwargs.kwargs.get("limit") == 20


async def test_get_recent_empty_results(mock_user):
    """GET /api/performance/recent returns empty outcomes when no data."""
    mock_svc = MagicMock()
    mock_svc.get_recent_outcomes = AsyncMock(return_value=[])
    mock_svc.performance_dao = MagicMock()
    mock_svc.performance_dao.session = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_performance_service] = lambda: mock_svc
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/performance/recent")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"outcomes": []}


async def test_get_recent_service_error_returns_500(mock_user):
    """GET /api/performance/recent returns 500 when service raises exception."""
    mock_svc = MagicMock()
    mock_svc.get_recent_outcomes = AsyncMock(side_effect=RuntimeError("Service fail"))
    mock_svc.performance_dao = MagicMock()
    mock_svc.performance_dao.session = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_performance_service] = lambda: mock_svc
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/performance/recent")
    app.dependency_overrides.clear()

    assert response.status_code == 500


async def test_get_agent_accuracy_returns_200(db_client):
    """GET /api/performance/agents returns 200 with agents structure."""
    response = await db_client.get("/api/performance/agents")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert data["agents"] == {}


async def test_get_agent_details_valid_agent(db_client):
    """GET /api/performance/agent/{agent_type} returns 200 for valid agent type."""
    response = await db_client.get("/api/performance/agent/fundamental")
    assert response.status_code == 200
    data = response.json()
    assert data["agent_type"] == "fundamental"
    assert "metrics" in data
    assert data["metrics"] == {}
    assert "message" in data


async def test_get_agent_details_invalid_agent_returns_400(db_client):
    """GET /api/performance/agent/{agent_type} returns 400 for unknown agent type."""
    response = await db_client.get("/api/performance/agent/invalid_agent_xyz")
    assert response.status_code == 400
    assert "Invalid agent type" in response.json()["detail"]


async def test_get_ticker_performance_no_data(db_client):
    """GET /api/performance/ticker/{ticker} returns empty history when no data."""
    response = await db_client.get("/api/performance/ticker/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"
    assert data["total_recommendations"] == 0
    assert data["history"] == []


async def test_get_ticker_performance_uppercases_ticker(db_client):
    """GET /api/performance/ticker/{ticker} uppercases the ticker symbol."""
    response = await db_client.get("/api/performance/ticker/aapl")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"


async def test_trigger_update_calls_scheduler(mock_user):
    """POST /api/performance/trigger-update calls scheduler.run_now()."""
    mock_scheduler = MagicMock()
    mock_scheduler.run_now = AsyncMock(return_value={"status": "completed"})

    app.dependency_overrides[get_current_user] = lambda: mock_user
    with patch(
        "backend.domains.performance.api.endpoints.get_scheduler",
        return_value=mock_scheduler,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/performance/trigger-update")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    mock_scheduler.run_now.assert_called_once()


async def test_trigger_update_scheduler_error_returns_500(mock_user):
    """POST /api/performance/trigger-update returns 500 when scheduler fails."""
    mock_scheduler = MagicMock()
    mock_scheduler.run_now = AsyncMock(side_effect=RuntimeError("Scheduler error"))

    app.dependency_overrides[get_current_user] = lambda: mock_user
    with patch(
        "backend.domains.performance.api.endpoints.get_scheduler",
        return_value=mock_scheduler,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/performance/trigger-update")
    app.dependency_overrides.clear()

    assert response.status_code == 500
    assert "Scheduler error" in response.json()["detail"]
