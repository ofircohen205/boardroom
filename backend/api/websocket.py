from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

from backend.graph.workflow import BoardroomGraph
from backend.state.enums import Market


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            ticker = data.get("ticker")
            market = Market(data.get("market", "US"))
            portfolio_weight = data.get("portfolio_weight", 0.0)

            graph = BoardroomGraph()
            async for event in graph.run_streaming(ticker, market, portfolio_weight):
                await websocket.send_json({
                    "type": event["type"].value,
                    "agent": event["agent"].value if event["agent"] else None,
                    "data": _serialize(event["data"]),
                    "timestamp": datetime.now().isoformat(),
                })

    except WebSocketDisconnect:
        pass


def _serialize(data):
    """Convert data to JSON-serializable format"""
    if isinstance(data, dict):
        return {k: _serialize(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_serialize(v) for v in data]
    if hasattr(data, "value"):  # Enum
        return data.value
    if hasattr(data, "isoformat"):  # datetime
        return data.isoformat()
    return data
