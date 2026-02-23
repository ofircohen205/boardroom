# backend/api.py
"""API router aggregation from all domains."""

from fastapi import APIRouter

from backend.domains.analysis.api.backtest.router import router as backtest_router
from backend.domains.analysis.api.endpoints import router as analysis_router
from backend.domains.analysis.api.paper.router import router as paper_router
from backend.domains.analysis.api.strategies.router import router as strategies_router
from backend.domains.analysis.api.websocket import router as websocket_router
from backend.domains.auth.api.endpoints import router as auth_router
from backend.domains.notifications.api.alerts import router as alerts_router
from backend.domains.notifications.api.endpoints import (
    router as notifications_router,
)
from backend.domains.notifications.api.notifications import (
    router as new_notifications_router,
)
from backend.domains.notifications.api.schedules import router as schedules_router
from backend.domains.performance.api.endpoints import router as performance_router
from backend.domains.portfolio.api.portfolios import router as portfolios_router
from backend.domains.portfolio.api.watchlists import router as watchlists_router
from backend.domains.sectors.api.endpoints import router as sectors_router
from backend.domains.settings.api.endpoints import router as settings_router
from backend.shared.utils.routes import router as utils_router

# Create main API router with /api prefix
api_router = APIRouter(prefix="/api")

# Include all domain routers
api_router.include_router(auth_router)
api_router.include_router(portfolios_router)
api_router.include_router(watchlists_router)
api_router.include_router(analysis_router)
api_router.include_router(alerts_router)
api_router.include_router(schedules_router)
api_router.include_router(notifications_router)
api_router.include_router(new_notifications_router)
api_router.include_router(performance_router)
api_router.include_router(settings_router)
api_router.include_router(sectors_router)
api_router.include_router(backtest_router)
api_router.include_router(paper_router)
api_router.include_router(strategies_router)
api_router.include_router(utils_router)

# WebSocket router (separate from /api prefix)
websocket_router_root = APIRouter(prefix="/ws")
websocket_router_root.include_router(websocket_router)

__all__ = ["api_router", "websocket_router_root"]
