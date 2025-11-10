"""Integration tests for database operations with real SQLite."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from core.database import DatabaseManager
from core.events import Event
from core.models import DetectedObject, BoundingBox


@pytest.fixture
def real_db_path():
    """Create a real database path for integration testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def initialized_db(real_db_path):
    """Initialize a real database for testing."""
    db = DatabaseManager(real_db_path)
    db.init_database()
    yield db
    db.close()


def create_sample_event(event_id: str, timestamp: datetime, camera_id: str = "test_camera") -> Event:
    """Create a sample event for testing."""
    bbox = BoundingBox(x=100, y=150, width=200, height=300)
    detected_obj = DetectedObject(label="person", confidence=0.85, bbox=bbox)

    return Event(
        event_id=event_id,
        timestamp=timestamp,
        camera_id=camera_id,
        motion_confidence=0.75,
        detected_objects=[detected_obj],
        llm_description=f"Test event {event_id}",
        image_path=f"data/events/{timestamp.date()}/{event_id}.jpg",
        json_log_path=f"data/events/{timestamp.date()}/events.json",
        metadata={"integration_test": True}
    )


class TestDatabaseIntegration:
    """Integration tests with real SQLite database."""

    def test_database_initialization(self, initialized_db):
        """Test that database initializes correctly with schema."""
        db = initialized_db

        # Check that tables exist
        cursor = db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        assert "events" in tables
        assert "schema_version" in tables

        # Check schema version
        cursor.execute("SELECT version FROM schema_version")
        version = cursor.fetchone()[0]
        assert version == 1

        # Check indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}

        expected_indexes = {
            "idx_events_timestamp",
            "idx_events_camera",
            "idx_events_event_id"
        }
        assert expected_indexes.issubset(indexes)

    def test_insert_and_retrieve_events(self, initialized_db):
        """Test inserting events and basic retrieval."""
        db = initialized_db

        # Create and insert test events
        base_time = datetime(2025, 11, 9, 12, 0, 0)
        events = []

        for i in range(5):
            event = create_sample_event(
                f"evt_test_{i:03d}",
                base_time.replace(second=i*10)
            )
            success = db.insert_event(event)
            assert success
            events.append(event)

        # Verify events were inserted
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        count = cursor.fetchone()[0]
        assert count == 5

        # Verify data integrity
        cursor.execute("SELECT event_id, camera_id, motion_confidence FROM events ORDER BY timestamp")
        rows = cursor.fetchall()

        for i, (event_id, camera_id, motion_confidence) in enumerate(rows):
            assert event_id == f"evt_test_{i:03d}"
            assert camera_id == "test_camera"
            assert motion_confidence == 0.75

    def test_bulk_event_insertion(self, initialized_db):
        """Test inserting 100 events for performance and scale."""
        db = initialized_db

        base_time = datetime(2025, 11, 9, 12, 0, 0)
        events_inserted = 0

        # Insert 100 events
        for i in range(100):
            event = create_sample_event(
                f"evt_bulk_{i:03d}",
                base_time.replace(second=i % 60, microsecond=i*1000)
            )
            success = db.insert_event(event)
            assert success
            events_inserted += 1

        assert events_inserted == 100

        # Verify all events persisted
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events WHERE event_id LIKE 'evt_bulk_%'")
        count = cursor.fetchone()[0]
        assert count == 100

        # Verify JSON serialization of detected_objects
        cursor.execute("SELECT detected_objects FROM events WHERE event_id = 'evt_bulk_050' LIMIT 1")
        detected_json = cursor.fetchone()[0]

        import json
        detected_objects = json.loads(detected_json)
        assert len(detected_objects) == 1
        assert detected_objects[0]["label"] == "person"
        assert detected_objects[0]["confidence"] == 0.85

    def test_duplicate_event_handling(self, initialized_db):
        """Test that duplicate event_ids are rejected."""
        db = initialized_db

        event = create_sample_event("evt_duplicate_test", datetime(2025, 11, 9, 12, 0, 0))

        # First insert should succeed
        success1 = db.insert_event(event)
        assert success1

        # Second insert should fail (duplicate)
        success2 = db.insert_event(event)
        assert not success2

        # Verify only one event exists
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events WHERE event_id = 'evt_duplicate_test'")
        count = cursor.fetchone()[0]
        assert count == 1

    def test_database_connection_persistence(self, initialized_db):
        """Test that database connection persists across operations."""
        db = initialized_db

        # Insert event
        event = create_sample_event("evt_persistence_test", datetime(2025, 11, 9, 12, 0, 0))
        db.insert_event(event)

        # Connection should still be open
        assert db.conn is not None

        # Should be able to query
        cursor = db.conn.cursor()
        cursor.execute("SELECT event_id FROM events WHERE event_id = 'evt_persistence_test'")
        result = cursor.fetchone()
        assert result[0] == "evt_persistence_test"

    def test_database_close(self, initialized_db):
        """Test proper database connection closing."""
        db = initialized_db

        # Insert something first
        event = create_sample_event("evt_close_test", datetime(2025, 11, 9, 12, 0, 0))
        db.insert_event(event)

        # Close connection
        db.close()

        # Connection should be None
        assert db.conn is None