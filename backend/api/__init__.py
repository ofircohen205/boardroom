# backend/api/__init__.py
"""API routers organized by domain."""
from fastapi import APIRouter

# Import domain routers
from .auth.endpoints import router as auth_router
from .watchlists.endpoints import router as watchlists_router
from .portfolios.endpoints import router as portfolios_router
from .analysis.endpoints import router as analysis_router
from .comparison import router as comparison_router
from .performance import router as performance_router

# Utility routes (markets, cache, stock search)
from .routes import router as utils_router

# Create main API router
api_router = APIRouter(prefix="/api")

# Include all domain routers
api_router.include_router(utils_router, tags=["utils"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(watchlists_router, prefix="/watchlists", tags=["watchlists"])
api_router.include_router(portfolios_router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
api_router.include_router(comparison_router, tags=["comparison"])
api_router.include_router(performance_router, tags=["performance"])

__all__ = ["api_router"]
