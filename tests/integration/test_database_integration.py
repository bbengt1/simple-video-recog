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
        cursor = db._get_connection().cursor()
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
        cursor = db._get_connection().cursor()
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

    def test_bulk_event_insertion_1000(self, initialized_db):
        """Test inserting 1000 events for performance and scale."""
        db = initialized_db

        base_time = datetime(2025, 11, 9, 12, 0, 0)
        events_inserted = 0

        # Insert 1000 events
        for i in range(1000):
            event = create_sample_event(
                f"evt_bulk_{i:04d}",
                base_time.replace(second=i % 60, microsecond=i*1000)
            )
            success = db.insert_event(event)
            assert success
            events_inserted += 1

        assert events_inserted == 1000

        # Verify all events persisted
        cursor = db._get_connection().cursor()
        cursor.execute("SELECT COUNT(*) FROM events WHERE event_id LIKE 'evt_bulk_%'")
        count = cursor.fetchone()[0]
        assert count == 1000

        # Verify JSON serialization/deserialization round-trip
        cursor.execute("SELECT detected_objects FROM events WHERE event_id = 'evt_bulk_0500' LIMIT 1")
        detected_json = cursor.fetchone()[0]

        import json
        detected_objects = json.loads(detected_json)
        assert len(detected_objects) == 1
        assert detected_objects[0]["label"] == "person"
        assert detected_objects[0]["confidence"] == 0.85

        # Verify data integrity by querying various events
        cursor.execute("""
            SELECT event_id, camera_id, motion_confidence, detected_objects
            FROM events
            WHERE event_id LIKE 'evt_bulk_%'
            ORDER BY timestamp
            LIMIT 5
        """)
        sample_rows = cursor.fetchall()
        assert len(sample_rows) == 5

        for event_id, camera_id, motion_confidence, detected_json in sample_rows:
            assert event_id.startswith("evt_bulk_")
            assert camera_id == "test_camera"
            assert motion_confidence == 0.75
            detected_objects = json.loads(detected_json)
            assert len(detected_objects) == 1

    def test_batch_insert_functionality(self, initialized_db):
        """Test batch insert method with 100 events."""
        db = initialized_db

        base_time = datetime(2025, 11, 9, 12, 0, 0)
        events = []

        # Create 100 events
        for i in range(100):
            event = create_sample_event(
                f"evt_batch_{i:03d}",
                base_time.replace(second=i % 60, microsecond=i*1000)
            )
            events.append(event)

        # Batch insert
        successful, failed = db.insert_events(events)

        assert successful == 100
        assert failed == 0

        # Verify all events persisted
        cursor = db._get_connection().cursor()
        cursor.execute("SELECT COUNT(*) FROM events WHERE event_id LIKE 'evt_batch_%'")
        count = cursor.fetchone()[0]
        assert count == 100

    def test_batch_insert_with_duplicates(self, initialized_db):
        """Test batch insert handling duplicates correctly."""
        db = initialized_db

        base_time = datetime(2025, 11, 9, 12, 0, 0)

        # Create events, including duplicates
        events = []
        for i in range(10):
            event = create_sample_event(
                f"evt_dup_{i % 5:03d}",  # Only 5 unique IDs, repeated
                base_time.replace(second=i)
            )
            events.append(event)

        # Batch insert
        successful, failed = db.insert_events(events)

        assert successful == 5  # Only first 5 unique events
        assert failed == 5     # 5 duplicates

        # Verify only unique events persisted
        cursor = db._get_connection().cursor()
        cursor.execute("SELECT COUNT(*) FROM events WHERE event_id LIKE 'evt_dup_%'")
        count = cursor.fetchone()[0]
        assert count == 5

    def test_query_operations_with_1000_events(self, initialized_db):
        """Test query operations with 1000 events inserted."""
        db = initialized_db

        base_time = datetime(2025, 11, 9, 12, 0, 0)
        events_created = []

        # Insert 1000 events with varied timestamps and cameras
        for i in range(1000):
            camera_id = f"camera_{(i % 3) + 1}"  # 3 different cameras
            event_time = base_time.replace(second=i % 60, microsecond=i*1000)
            event = create_sample_event(
                f"evt_query_{i:04d}",
                event_time,
                camera_id
            )
            success = db.insert_event(event)
            assert success
            events_created.append(event)

        # Test count_events
        total_count = db.count_events()
        assert total_count >= 1000  # May have more from other tests

        # Test get_event_by_id
        specific_event = events_created[500]
        retrieved = db.get_event_by_id(specific_event.event_id)
        assert retrieved is not None
        assert retrieved.event_id == specific_event.event_id
        assert retrieved.camera_id == specific_event.camera_id
        assert len(retrieved.detected_objects) == 1

        # Test get_events_by_timerange
        start_range = base_time.replace(second=30)
        end_range = base_time.replace(second=45)
        timerange_events = db.get_events_by_timerange(start_range, end_range)
        assert len(timerange_events) > 0
        # Verify all returned events are within range
        for event in timerange_events:
            assert start_range <= event.timestamp < end_range

        # Test get_recent_events
        recent_events = db.get_recent_events(limit=50)
        assert len(recent_events) <= 50
        # Verify ordering (most recent first)
        for i in range(len(recent_events) - 1):
            assert recent_events[i].timestamp >= recent_events[i + 1].timestamp

        # Test get_events_by_camera
        camera_events = db.get_events_by_camera("camera_1", limit=100)
        assert len(camera_events) > 0
        # Verify all events are from the correct camera
        for event in camera_events:
            assert event.camera_id == "camera_1"

        # Test pagination
        paginated_events = db.get_events_by_timerange(
            datetime.min, datetime.max, offset=100, limit=50
        )
        assert len(paginated_events) <= 50

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
        cursor = db._get_connection().cursor()
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
        assert db._get_connection() is not None

        # Should be able to query
        cursor = db._get_connection().cursor()
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