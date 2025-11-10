# WebSocket endpoint for real-time event streaming

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime
import logging
import json

from api.websocket import WebSocketManager

router = APIRouter()
logger = logging.getLogger(__name__)

# Module-level WebSocket manager singleton
ws_manager = WebSocketManager()


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """
    WebSocket endpoint for real-time event streaming.

    Clients connect to receive live event updates as they occur.
    Connection remains open until client disconnects or server shuts down.
    """
    connection_id = None

    try:
        # Accept connection
        await websocket.accept()
        connection_id = ws_manager.connect(websocket)

        logger.info(f"[{connection_id}] WebSocket connected")

        # Send initial ping
        await websocket.send_json({
            "type": "ping",
            "timestamp": datetime.now().isoformat()
        })

        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client messages (pong responses, etc.)
                data = await websocket.receive_text()
                message = json.loads(data)

                if message.get("type") == "pong":
                    logger.debug(f"[{connection_id}] Received pong")
                else:
                    logger.warning(f"[{connection_id}] Unknown message type: {message.get('type')}")

            except json.JSONDecodeError:
                logger.warning(f"[{connection_id}] Received invalid JSON")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })

    except WebSocketDisconnect:
        logger.info(f"[{connection_id}] WebSocket disconnected")

    except Exception as e:
        logger.error(f"[{connection_id}] WebSocket error: {e}", exc_info=True)

    finally:
        if connection_id:
            ws_manager.disconnect(connection_id)
            logger.info(f"[{connection_id}] Connection closed")


def get_websocket_manager() -> WebSocketManager:
    """Get WebSocket manager singleton."""
    return ws_manager