# Unit tests for WebSocket functionality

import pytest
from unittest.mock import AsyncMock, MagicMock
import asyncio

from api.websocket import WebSocketManager


class TestWebSocketManager:
    """Test WebSocket connection management and broadcasting."""

    @pytest.fixture
    def ws_manager(self):
        """Create a fresh WebSocketManager for each test."""
        return WebSocketManager()

    def test_connect_creates_connection_id(self, ws_manager):
        """Test that connect() returns a unique connection ID."""
        mock_ws = MagicMock()
        connection_id = ws_manager.connect(mock_ws)

        assert connection_id is not None
        assert isinstance(connection_id, str)
        assert len(connection_id) > 0
        assert ws_manager.get_connection_count() == 1

    def test_disconnect_removes_connection(self, ws_manager):
        """Test that disconnect() removes the connection."""
        mock_ws = MagicMock()
        connection_id = ws_manager.connect(mock_ws)

        assert ws_manager.get_connection_count() == 1

        ws_manager.disconnect(connection_id)

        assert ws_manager.get_connection_count() == 0

    def test_disconnect_unknown_connection_no_error(self, ws_manager):
        """Test that disconnecting unknown connection doesn't raise error."""
        ws_manager.disconnect("unknown_id")  # Should not raise

    @pytest.mark.asyncio
    async def test_broadcast_event_no_connections(self, ws_manager):
        """Test broadcasting when no connections exist."""
        # Should not raise any errors
        await ws_manager.broadcast_event({"test": "data"})

    @pytest.mark.asyncio
    async def test_broadcast_event_to_multiple_clients(self, ws_manager):
        """Test broadcasting event to multiple connected clients."""
        # Create mock WebSocket clients
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws3 = AsyncMock()

        # Connect clients
        ws_manager.connect(mock_ws1)
        ws_manager.connect(mock_ws2)
        ws_manager.connect(mock_ws3)

        # Broadcast event
        event_data = {"event_id": "test_123", "description": "Test event"}
        await ws_manager.broadcast_event(event_data)

        # Verify all clients received the message
        expected_message = {
            "type": "event",
            "data": event_data
        }

        mock_ws1.send_json.assert_called_once_with(expected_message)
        mock_ws2.send_json.assert_called_once_with(expected_message)
        mock_ws3.send_json.assert_called_once_with(expected_message)

    @pytest.mark.asyncio
    async def test_broadcast_handles_failed_connections(self, ws_manager):
        """Test that broadcast handles clients that fail to receive."""
        # Create mock clients - one will fail
        mock_ws_good = AsyncMock()
        mock_ws_bad = AsyncMock()
        mock_ws_bad.send_json.side_effect = Exception("Connection failed")

        # Connect clients
        ws_manager.connect(mock_ws_good)
        ws_manager.connect(mock_ws_bad)

        # Broadcast event
        event_data = {"event_id": "test_123"}
        await ws_manager.broadcast_event(event_data)

        # Good client should have received the message
        mock_ws_good.send_json.assert_called_once()

        # Bad client should have been removed
        assert ws_manager.get_connection_count() == 1

    @pytest.mark.asyncio
    async def test_send_ping_to_all(self, ws_manager):
        """Test sending ping to all connected clients."""
        # Create mock clients
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        # Connect clients
        ws_manager.connect(mock_ws1)
        ws_manager.connect(mock_ws2)

        # Send ping
        await ws_manager.send_ping_to_all()

        # Verify ping messages sent
        mock_ws1.send_json.assert_called_once()
        mock_ws2.send_json.assert_called_once()

        # Check that ping messages contain correct type and timestamp
        call_args1 = mock_ws1.send_json.call_args[0][0]
        call_args2 = mock_ws2.send_json.call_args[0][0]

        assert call_args1["type"] == "ping"
        assert call_args2["type"] == "ping"
        assert "timestamp" in call_args1
        assert "timestamp" in call_args2
        assert isinstance(call_args1["timestamp"], str)
        assert isinstance(call_args2["timestamp"], str)

    @pytest.mark.asyncio
    async def test_close_all_connections(self, ws_manager):
        """Test closing all WebSocket connections gracefully."""
        # Create mock clients
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()

        # Connect clients
        ws_manager.connect(mock_ws1)
        ws_manager.connect(mock_ws2)

        assert ws_manager.get_connection_count() == 2

        # Close all connections
        await ws_manager.close_all()

        # Verify close() was called on all clients
        mock_ws1.close.assert_called_once()
        mock_ws2.close.assert_called_once()

        # Verify connections were cleared
        assert ws_manager.get_connection_count() == 0

    def test_get_connection_count(self, ws_manager):
        """Test getting connection count."""
        assert ws_manager.get_connection_count() == 0

        mock_ws = MagicMock()
        ws_manager.connect(mock_ws)

        assert ws_manager.get_connection_count() == 1

        ws_manager.disconnect(ws_manager.connect(mock_ws))

        assert ws_manager.get_connection_count() == 1  # Still 1 after second connect

    @pytest.mark.asyncio
    async def test_heartbeat_task_basic(self, ws_manager):
        """Test basic heartbeat functionality."""
        # This is a basic test - full heartbeat testing would require
        # running the task and stopping it, which is complex in unit tests

        # Just verify the method exists and can be called
        await ws_manager.send_ping_to_all()  # Should not raise

        # Verify heartbeat method exists
        assert hasattr(ws_manager, 'start_heartbeat')
        assert callable(ws_manager.start_heartbeat)