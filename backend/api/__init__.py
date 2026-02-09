# backend/api/__init__.py
"""API routers organized by domain."""
from fastapi import APIRouter

# Import domain routers
from .auth.endpoints import router as auth_router
from .watchlists.endpoints import router as watchlists_router
from .portfolios.endpoints import router as portfolios_router
from .analysis.endpoints import router as analysis_router
from .sectors.endpoints import router as sectors_router
from .websocket.endpoints import router as websocket_router

# Utility routes (markets, cache, stock search)
from .routes import router as utils_router

# Create main API router
api_router = APIRouter(prefix="/api")

# Include all domain routers
api_router.include_router(analysis_router)
api_router.include_router(auth_router)
api_router.include_router(portfolios_router)
api_router.include_router(sectors_router)
api_router.include_router(utils_router)
api_router.include_router(watchlists_router)
api_router.include_router(websocket_router)

__all__ = ["api_router"]
