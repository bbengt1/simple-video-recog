# WebSocket connection manager for real-time event streaming

from fastapi import WebSocket
from typing import Dict
import asyncio
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts events to all connected clients.

    Thread-safe connection management with automatic cleanup of dead connections.
    """

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()
        self._heartbeat_task = None

    def connect(self, websocket: WebSocket) -> str:
        """
        Add a new WebSocket connection.

        Returns:
            connection_id: Unique identifier for this connection
        """
        connection_id = f"ws_{uuid.uuid4().hex[:8]}"
        self.active_connections[connection_id] = websocket
        logger.info(f"Connection added: {connection_id} (total: {len(self.active_connections)})")
        return connection_id

    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info(f"Connection removed: {connection_id} (total: {len(self.active_connections)})")

    async def broadcast_event(self, event_data: dict):
        """
        Broadcast event to all connected clients.

        Args:
            event_data: Event dictionary matching Event Pydantic model
        """
        if not self.active_connections:
            logger.debug("No active connections to broadcast to")
            return

        message = {
            "type": "event",
            "data": event_data
        }

        logger.debug(f"Broadcasting event to {len(self.active_connections)} clients")

        # Broadcast to all clients, handle individual failures
        dead_connections = []

        async with self._lock:
            for connection_id, websocket in self.active_connections.items():
                try:
                    await websocket.send_json(message)
                    logger.debug(f"[{connection_id}] Event sent successfully")

                except Exception as e:
                    logger.warning(f"[{connection_id}] Failed to send event: {e}")
                    dead_connections.append(connection_id)

        # Clean up dead connections
        for connection_id in dead_connections:
            self.disconnect(connection_id)

    async def send_ping_to_all(self):
        """Send ping to all connected clients to detect stale connections."""
        if not self.active_connections:
            return

        ping_message = {
            "type": "ping",
            "timestamp": datetime.now().isoformat()
        }

        logger.debug(f"Sending ping to {len(self.active_connections)} clients")

        dead_connections = []

        async with self._lock:
            for connection_id, websocket in self.active_connections.items():
                try:
                    await websocket.send_json(ping_message)
                except Exception as e:
                    logger.warning(f"[{connection_id}] Ping failed: {e}")
                    dead_connections.append(connection_id)

        for connection_id in dead_connections:
            self.disconnect(connection_id)

    async def start_heartbeat(self, interval: int = 30):
        """
        Start heartbeat task to ping clients periodically.

        Args:
            interval: Seconds between pings (default: 30)
        """
        while True:
            await asyncio.sleep(interval)
            await self.send_ping_to_all()

    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)

    async def close_all(self):
        """Close all WebSocket connections gracefully."""
        logger.info(f"Closing all connections ({len(self.active_connections)})")

        async with self._lock:
            for connection_id, websocket in self.active_connections.items():
                try:
                    await websocket.close()
                    logger.info(f"[{connection_id}] Connection closed")
                except Exception as e:
                    logger.warning(f"[{connection_id}] Error closing connection: {e}")

            self.active_connections.clear()