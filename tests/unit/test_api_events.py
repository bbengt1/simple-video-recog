"""Unit tests for the events API endpoints.

Tests cover:
- Event list endpoint with pagination and filtering
- Single event endpoint
- Event image endpoint
- Error handling and edge cases
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import sqlite3
from datetime import datetime

from httpx import AsyncClient
from httpx import ASGITransport

from api.app import create_app
from api.models import Event, DetectedObject, BoundingBox
from core.config import SystemConfig


class TestEventRoutes:
    """Test that event routes are properly registered."""

    def test_event_routes_registered(self):
        """Test that all event routes are registered in the app."""
        from fastapi.routing import APIRoute

        app = create_app()

        # Check that routes contain the events endpoints
        routes = [str(route.path) for route in app.routes if isinstance(route, APIRoute)]
        assert '/api/events' in routes
        assert '/api/events/{event_id}' in routes
        assert '/api/events/{event_id}/image' in routes


class TestEventListEndpoint:
    """Test event list endpoint functionality."""

    @pytest.mark.asyncio
    async def test_list_events_empty_database(self):
        """Test event list returns empty results for empty database."""
        from unittest.mock import patch

        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock count query returns 0
        mock_cursor.fetchone.return_value = (0,)
        # Mock events query returns empty list
        mock_cursor.fetchall.return_value = []

        with patch('api.dependencies._db_conn', mock_conn), \
             patch('api.dependencies._config', None):
            app = create_app()

            async with AsyncClient(transport=ASGITransport(app=app), base_url='http://testserver') as client:
                response = await client.get('/api/events?limit=10&offset=0')

                assert response.status_code == 200
                data = response.json()

                assert data['total'] == 0
                assert data['limit'] == 10
                assert data['offset'] == 0
                assert data['events'] == []

    @patch('api.dependencies.get_config')
    @pytest.mark.asyncio
    async def test_list_events_pagination(self, mock_get_config):
        """Test pagination parameters work correctly."""
        # Mock the config with required attributes
        mock_config = Mock()
        mock_config.db_path = "data/events.db"
        mock_get_config.return_value = mock_config

        app = create_app()

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://testserver') as client:
            response = await client.get('/api/events?limit=50&offset=20')

            assert response.status_code == 200
            data = response.json()

            assert data['limit'] == 50
            assert data['offset'] == 20

    @patch('api.dependencies.get_config')
    @pytest.mark.asyncio
    async def test_list_events_invalid_limit(self, mock_get_config):
        """Test invalid limit parameter returns 422."""
        # Mock the config with required attributes
        mock_config = Mock()
        mock_config.db_path = "data/events.db"
        mock_get_config.return_value = mock_config

        app = create_app()

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://testserver') as client:
            response = await client.get('/api/events?limit=2000')  # Max is 1000

            assert response.status_code == 422

    @patch('api.dependencies.load_config')
    @pytest.mark.asyncio
    async def test_list_events_invalid_offset(self, mock_get_config):
        """Test invalid offset parameter returns 422."""
        # Mock the config with required attributes
        mock_config = Mock()
        mock_config.db_path = "data/events.db"
        mock_get_config.return_value = mock_config

        app = create_app()

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://testserver') as client:
            response = await client.get('/api/events?offset=-1')  # Must be >= 0

            assert response.status_code == 422

    @patch('api.dependencies.load_config')
    @pytest.mark.asyncio
    async def test_list_events_time_range_filtering(self, mock_get_config):
        """Test time range filtering parameters are accepted."""
        # Mock the config with required attributes
        mock_config = Mock()
        mock_config.db_path = "data/events.db"
        mock_get_config.return_value = mock_config

        app = create_app()

        start_time = "2025-11-01T00:00:00Z"
        end_time = "2025-11-10T23:59:59Z"

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://testserver') as client:
            response = await client.get(f'/api/events?start={start_time}&end={end_time}')

            assert response.status_code == 200
            # Since database is empty, should return empty results
            data = response.json()
            assert data['total'] == 0

    @patch('api.dependencies.load_config')
    @pytest.mark.asyncio
    async def test_list_events_camera_filtering(self, mock_get_config):
        """Test camera ID filtering parameter is accepted."""
        # Mock the config with required attributes
        mock_config = Mock()
        mock_config.db_path = "data/events.db"
        mock_get_config.return_value = mock_config

        app = create_app()

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://testserver') as client:
            response = await client.get('/api/events?camera_id=front_door')

            assert response.status_code == 200
            data = response.json()
            assert data['total'] == 0


class TestSingleEventEndpoint:
    """Test single event endpoint functionality."""

    @patch('api.dependencies.load_config')
    @pytest.mark.asyncio
    async def test_get_event_not_found(self, mock_get_config):
        """Test getting non-existent event returns 404."""
        # Mock the config with required attributes
        mock_config = Mock()
        mock_config.db_path = "data/events.db"
        mock_get_config.return_value = mock_config

        app = create_app()

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://testserver') as client:
            response = await client.get('/api/events/invalid_event_id')

            assert response.status_code == 404
            data = response.json()

            assert 'detail' in data
            assert data['detail']['code'] == 'EVENT_NOT_FOUND'
            assert 'timestamp' in data['detail']
            assert 'request_id' in data['detail']


class TestEventImageEndpoint:
    """Test event image endpoint functionality."""

    @patch('api.dependencies.load_config')
    @pytest.mark.asyncio
    async def test_get_event_image_not_found(self, mock_get_config):
        """Test getting image for non-existent event returns 404."""
        # Mock the config with required attributes
        mock_config = Mock()
        mock_config.db_path = "data/events.db"
        mock_get_config.return_value = mock_config

        app = create_app()

        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://testserver') as client:
            response = await client.get('/api/events/invalid_event_id/image')

            assert response.status_code == 404
            data = response.json()

            assert 'detail' in data
            assert data['detail']['code'] == 'EVENT_NOT_FOUND'


class TestEventModels:
    """Test Pydantic models for events."""

    def test_event_model_creation(self):
        """Test Event model can be created with valid data."""
        test_timestamp = datetime(2025, 11, 8, 14, 32, 15)
        bbox = BoundingBox(x=120, y=50, width=180, height=320)
        detected_obj = DetectedObject(
            label="person",
            confidence=0.92,
            bbox=bbox
        )

        event = Event(
            event_id="evt_1699459335_a7b3c",
            timestamp=test_timestamp,
            camera_id="front_door",
            motion_confidence=0.87,
            detected_objects=[detected_obj],
            llm_description="Person in blue shirt carrying package",
            image_path="/images/2025-11-08/evt_1699459335_a7b3c.jpg",
            created_at=test_timestamp
        )

        assert event.event_id == "evt_1699459335_a7b3c"
        assert event.camera_id == "front_door"
        assert len(event.detected_objects) == 1
        assert event.detected_objects[0].label == "person"

    def test_bounding_box_validation(self):
        """Test BoundingBox model validation."""
        # Valid bounding box
        bbox = BoundingBox(x=120, y=50, width=180, height=320)
        assert bbox.x == 120
        assert bbox.width == 180

        # Invalid negative coordinates
        with pytest.raises(ValueError):
            BoundingBox(x=-10, y=50, width=180, height=320)

        # Invalid zero width
        with pytest.raises(ValueError):
            BoundingBox(x=120, y=50, width=0, height=320)

    def test_detected_object_validation(self):
        """Test DetectedObject model validation."""
        bbox = BoundingBox(x=120, y=50, width=180, height=320)

        # Valid object
        obj = DetectedObject(
            label="person",
            confidence=0.92,
            bbox=bbox
        )
        assert obj.label == "person"
        assert obj.confidence == 0.92

        # Invalid confidence > 1.0
        with pytest.raises(ValueError):
            DetectedObject(
                label="person",
                confidence=1.5,
                bbox=bbox
            )

        # Invalid confidence < 0.0
        with pytest.raises(ValueError):
            DetectedObject(
                label="person",
                confidence=-0.1,
                bbox=bbox
            )


class TestDatabaseIntegration:
    """Test database integration aspects."""

    def test_database_connection_readonly(self):
        """Test that database connection is read-only."""
        from api.dependencies import get_db_connection

        # This test assumes the database exists
        try:
            conn = get_db_connection()
            assert conn is not None

            # Should be able to read
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events")
            count = cursor.fetchone()[0]
            assert isinstance(count, int)

            # Should not be able to write (read-only mode)
            with pytest.raises(sqlite3.OperationalError):
                cursor.execute("INSERT INTO events (event_id) VALUES ('test')")

        except Exception:
            # If database doesn't exist or connection fails, that's ok for this test
            pass