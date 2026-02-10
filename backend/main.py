from backend.db import get_db
from contextlib import asynccontextmanager

from sqlalchemy import text

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import api_router, websocket_router_root
from backend.jobs.scheduler import start_scheduler, stop_scheduler
from backend.core.cache import get_cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: start/stop background jobs and connections."""
    # Startup
    cache = get_cache()
    await cache._ensure_connection()  # Initialize Redis connection
    await start_scheduler()
    yield
    # Shutdown
    await stop_scheduler()
    await cache.close()  # Close Redis connection


app = FastAPI(title="Boardroom", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include modular API router
app.include_router(api_router)

# Include WebSocket router (no /api prefix)
app.include_router(websocket_router_root)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/health/db")
async def postgres_health():
    """Check PostgreSQL connection health."""
    try:
        # Get a session and execute a simple query
        async for session in get_db():
            await session.execute(text("SELECT 1"))
            return {"status": "healthy", "service": "postgres"}
    except Exception as e:
        return {"status": "unhealthy", "service": "postgres", "error": str(e)}


@app.get("/health/cache")
async def redis_health():
    """Check Redis connection health."""
    try:
        cache = get_cache()
        stats = await cache.stats()
        if stats.get("connected"):
            return {"status": "healthy", "service": "redis", "stats": stats}
        else:
            return {
                "status": "degraded",
                "service": "redis",
                "message": "Redis not connected, using in-memory fallback",
                "stats": stats,
            }
    except Exception as e:
        return {"status": "unhealthy", "service": "redis", "error": str(e)}
