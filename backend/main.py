from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.api.websocket import websocket_endpoint

app = FastAPI(title="Boardroom", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.websocket("/ws/analyze")(websocket_endpoint)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
