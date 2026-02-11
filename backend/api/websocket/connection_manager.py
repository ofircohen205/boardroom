# backend/api/websocket/connection_manager.py
"""WebSocket connection manager for real-time notifications."""

from typing import Dict, Set
from uuid import UUID

from fastapi import WebSocket

from backend.core.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time notifications.

    Keeps track of active connections per user and provides methods to:
    - Register/unregister connections
    - Send notifications to all user's connections (multi-device support)
    """

    def __init__(self):
        # Maps user_id -> set of WebSocket connections
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}

    async def connect(self, user_id: UUID, websocket: WebSocket):
        """
        Register a new WebSocket connection for a user.

        Args:
            user_id: User ID
            websocket: WebSocket connection to register
        """
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        logger.info(
            f"WebSocket connected for user {user_id}. Total connections: {len(self.active_connections[user_id])}"
        )

    def disconnect(self, user_id: UUID, websocket: WebSocket):
        """
        Unregister a WebSocket connection for a user.

        Args:
            user_id: User ID
            websocket: WebSocket connection to unregister
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

            # Clean up empty sets
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                logger.info(f"All WebSocket connections closed for user {user_id}")
            else:
                logger.info(
                    f"WebSocket disconnected for user {user_id}. Remaining connections: {len(self.active_connections[user_id])}"
                )

    async def send_notification(self, user_id: UUID, notification: dict):
        """
        Send a notification to all active connections for a user.

        Args:
            user_id: User ID
            notification: Notification data to send (dict with id, type, title, body, data, created_at)
        """
        if user_id not in self.active_connections:
            logger.debug(
                f"No active connections for user {user_id}, skipping notification"
            )
            return

        connections = self.active_connections[
            user_id
        ].copy()  # Copy to avoid modification during iteration
        disconnected = []

        for websocket in connections:
            try:
                await websocket.send_json(
                    {"type": "notification", "data": notification}
                )
                logger.debug(f"Notification sent to user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to send notification to user {user_id}: {e}")
                disconnected.append(websocket)

        # Clean up disconnected sockets
        for websocket in disconnected:
            self.disconnect(user_id, websocket)


# Global singleton instance
connection_manager = ConnectionManager()
