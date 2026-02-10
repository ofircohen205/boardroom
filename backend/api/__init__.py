# backend/api/__init__.py
"""API routers organized by domain."""
from fastapi import APIRouter

from .alerts.endpoints import router as alerts_router
from .analysis.endpoints import router as analysis_router

# Import domain routers
from .auth.endpoints import router as auth_router
from .notifications.endpoints import router as notifications_router
from .portfolios.endpoints import router as portfolios_router

# Utility routes (markets, cache, stock search)
from .routes import router as utils_router
from .schedules.endpoints import router as schedules_router
from .sectors.endpoints import router as sectors_router
from .settings.endpoints import router as settings_router
from .watchlists.endpoints import router as watchlists_router
from .websocket.endpoints import router as websocket_router

# Create main API router
api_router = APIRouter(prefix="/api")

# Include all domain routers
api_router.include_router(alerts_router)
api_router.include_router(analysis_router)
api_router.include_router(auth_router)
api_router.include_router(notifications_router)
api_router.include_router(portfolios_router)
api_router.include_router(schedules_router)
api_router.include_router(sectors_router)
api_router.include_router(settings_router)
api_router.include_router(utils_router)
api_router.include_router(watchlists_router)

# WebSocket router (separate from /api prefix)
websocket_router_root = APIRouter(prefix="/ws")
websocket_router_root.include_router(websocket_router)

__all__ = ["api_router", "websocket_router_root"]
