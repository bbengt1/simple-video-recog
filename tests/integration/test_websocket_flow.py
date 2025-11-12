# Integration tests for WebSocket event streaming

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import WebSocketDisconnect

from api.app import create_app
from api.websocket import WebSocketManager
from core.event_manager import EventManager
from core.database import DatabaseManager
from core.events import Event
from core.models import DetectedObject, BoundingBox
from datetime import datetime


class TestWebSocketIntegration:
    """Integration tests for WebSocket event streaming."""

    @pytest.fixture
    def app(self):
        """Create FastAPI app for testing."""
        return create_app()

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def ws_manager(self):
        """Get fresh WebSocket manager for each test."""
        # Create a fresh manager for each test to avoid singleton interference
        return WebSocketManager()

    @pytest.fixture
    def event_manager(self, ws_manager):
        """Create EventManager with WebSocket support."""
        db_manager = MagicMock(spec=DatabaseManager)
        db_manager.insert_event.return_value = None  # Mock successful insertion
        return EventManager(
            database_manager=db_manager,
            websocket_manager=ws_manager
        )

    def test_websocket_endpoint_exists(self, client):
        """Test WebSocket endpoint is registered."""
        # WebSocket endpoints don't appear in OpenAPI, but route should exist
        routes = [route for route in client.app.routes if hasattr(route, 'path') and route.path == "/ws/events"]
        assert len(routes) == 1

    @pytest.mark.asyncio
    async def test_websocket_connection_lifecycle(self, ws_manager):
        """Test full WebSocket connection lifecycle."""
        # Create mock WebSocket
        mock_ws = AsyncMock()
        received_messages = []

        async def mock_receive_text():
            # Simulate client sending pong
            return json.dumps({"type": "pong"})

        async def mock_send_json(message):
            received_messages.append(message)

        mock_ws.receive_text = mock_receive_text
        mock_ws.send_json = mock_send_json

        # Simulate connection
        connection_id = ws_manager.connect(mock_ws)
        assert connection_id is not None
        assert ws_manager.get_connection_count() == 1

        # Simulate initial ping
        await ws_manager.send_ping_to_all()
        assert len(received_messages) >= 1
        assert received_messages[0]["type"] == "ping"

        # Simulate disconnection
        ws_manager.disconnect(connection_id)
        assert ws_manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_event_broadcasting_integration(self, event_manager, ws_manager):
        """Test event creation broadcasts to WebSocket clients."""
        # Create mock WebSocket client
        mock_ws = AsyncMock()
        received_messages = []

        async def mock_send_json(message):
            received_messages.append(message)

        mock_ws.send_json = mock_send_json

        # Connect client
        ws_manager.connect(mock_ws)

        # Create test event
        detected_objects = [
            DetectedObject(
                label="person",
                confidence=0.9,
                bbox=BoundingBox(x=10, y=20, width=100, height=150)
            )
        ]
        event = event_manager.create_event(
            event_id="test_evt_123",
            timestamp=datetime.now(),
            camera_id="cam1",
            motion_confidence=0.8,
            detected_objects=detected_objects,
            llm_description="A person detected",
            image_path="/path/to/image.jpg",
            json_log_path="/path/to/log.json",
            metadata={"test": True}
        )

        # Give async task time to complete
        await asyncio.sleep(0.1)

        # Verify event was broadcast
        assert len(received_messages) == 1
        message = received_messages[0]
        assert message["type"] == "event"
        assert message["data"]["event_id"] == "test_evt_123"
        assert message["data"]["camera_id"] == "cam1"
        assert message["data"]["llm_description"] == "A person detected"

    @pytest.mark.asyncio
    async def test_multiple_clients_receive_events(self, event_manager, ws_manager):
        """Test multiple WebSocket clients receive the same event."""
        # Create multiple mock clients
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws3 = AsyncMock()

        received_messages = [[], [], []]

        async def mock_send_json1(msg):
            received_messages[0].append(msg)
        async def mock_send_json2(msg):
            received_messages[1].append(msg)
        async def mock_send_json3(msg):
            received_messages[2].append(msg)

        mock_ws1.send_json = mock_send_json1
        mock_ws2.send_json = mock_send_json2
        mock_ws3.send_json = mock_send_json3

        # Connect all clients
        ws_manager.connect(mock_ws1)
        ws_manager.connect(mock_ws2)
        ws_manager.connect(mock_ws3)

        # Create event
        detected_objects = [
            DetectedObject(
                label="car",
                confidence=0.85,
                bbox=BoundingBox(x=50, y=60, width=200, height=100)
            )
        ]
        event_manager.create_event(
            event_id="multi_test_456",
            timestamp=datetime.now(),
            camera_id="cam1",
            motion_confidence=0.7,
            detected_objects=detected_objects,
            llm_description="A car detected",
            image_path="/path/to/car.jpg",
            json_log_path="/path/to/car.json"
        )

        # Give async tasks time to complete
        await asyncio.sleep(0.1)

        # All clients should have received the event
        for i, messages in enumerate(received_messages):
            assert len(messages) == 1, f"Client {i+1} should have received 1 message"
            assert messages[0]["type"] == "event"
            assert messages[0]["data"]["event_id"] == "multi_test_456"

    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, ws_manager):
        """Test WebSocket error handling and dead connection cleanup."""
        # Create clients - some will fail
        mock_ws_good = AsyncMock()
        mock_ws_bad1 = AsyncMock()
        mock_ws_bad2 = AsyncMock()

        received_messages = []

        async def mock_send_json_good(msg):
            received_messages.append(msg)

        mock_ws_good.send_json = mock_send_json_good
        mock_ws_bad1.send_json.side_effect = Exception("Connection failed")
        mock_ws_bad2.send_json.side_effect = Exception("Network error")

        # Connect clients
        ws_manager.connect(mock_ws_good)
        ws_manager.connect(mock_ws_bad1)
        ws_manager.connect(mock_ws_bad2)

        assert ws_manager.get_connection_count() == 3

        # Broadcast event - should handle failures gracefully
        await ws_manager.broadcast_event({"event_id": "error_test"})

        # Good client should have received the message
        assert len(received_messages) == 1
        assert received_messages[0]["type"] == "event"

        # Bad connections should have been cleaned up
        assert ws_manager.get_connection_count() == 1

    @pytest.mark.asyncio
    async def test_ping_pong_heartbeat(self, ws_manager):
        """Test ping/pong heartbeat mechanism."""
        # Create mock client
        mock_ws = AsyncMock()
        received_messages = []

        async def mock_send_json(msg):
            received_messages.append(msg)

        mock_ws.send_json = mock_send_json

        # Connect client
        ws_manager.connect(mock_ws)

        # Send ping
        await ws_manager.send_ping_to_all()

        # Verify ping was sent
        assert len(received_messages) == 1
        ping_msg = received_messages[0]
        assert ping_msg["type"] == "ping"
        assert "timestamp" in ping_msg
        assert isinstance(ping_msg["timestamp"], str)

    def test_event_manager_without_websocket(self):
        """Test EventManager works without WebSocket manager."""
        db_manager = MagicMock(spec=DatabaseManager)
        event_manager = EventManager(database_manager=db_manager, websocket_manager=None)

        # Should not raise error
        event = event_manager.create_event(
            event_id="no_ws_test",
            timestamp=datetime.now(),
            camera_id="cam1",
            motion_confidence=0.5,
            detected_objects=[],
            llm_description="Test without WebSocket",
            image_path="/test.jpg",
            json_log_path="/test.json"
        )

        assert event is not None
        assert event.event_id == "no_ws_test"