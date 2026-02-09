from contextlib import asynccontextmanager

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
