from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.api.websocket import websocket_endpoint
from backend.api.comparison import router as comparison_router
from backend.api.performance import router as performance_router

from backend.jobs.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: start/stop background jobs."""
    # Startup
    await start_scheduler()
    yield
    # Shutdown
    await stop_scheduler()


app = FastAPI(title="Boardroom", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(comparison_router)
app.include_router(performance_router)
app.websocket("/ws/analyze")(websocket_endpoint)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
