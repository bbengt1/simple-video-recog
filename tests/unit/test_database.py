"""Unit tests for database module."""

import json
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from core.database import DatabaseManager
from core.events import Event
from core.exceptions import DatabaseError
from core.models import DetectedObject, BoundingBox


@pytest.fixture
def temp_db_path():
    """Create a temporary database path for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def sample_event():
    """Create a sample Event for testing."""
    bbox = BoundingBox(x=100, y=150, width=200, height=300)
    detected_obj = DetectedObject(label="person", confidence=0.92, bbox=bbox)

    return Event(
        event_id="evt_1234567890_abc123",
        timestamp=datetime.fromisoformat("2025-11-09T12:00:00"),
        camera_id="camera_1",
        motion_confidence=0.87,
        detected_objects=[detected_obj],
        llm_description="Person detected",
        image_path="data/events/2025-11-09/evt_1234567890_abc123.jpg",
        json_log_path="data/events/2025-11-09/events.json",
        metadata={"test": True}
    )


class TestDatabaseManager:
    """Test DatabaseManager class."""

    def test_init(self, temp_db_path):
        """Test DatabaseManager initialization."""
        db = DatabaseManager(temp_db_path)
        assert db.db_path == temp_db_path
        assert db.conn is None

    @patch('core.database.sqlite3.connect')
    @patch('core.database.Path')
    def test_init_database_success(self, mock_path, mock_connect, temp_db_path):
        """Test successful database initialization."""
        # Mock the connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (0,)  # No schema version yet
        mock_connect.return_value = mock_conn

        # Mock migration file reading
        migration_sql = "CREATE TABLE test (id INTEGER);"
        with patch('builtins.open', mock_open(read_data=migration_sql)):
            db = DatabaseManager(temp_db_path)
            db.init_database()

        # Verify connection was made
        mock_connect.assert_called_once_with(temp_db_path)
        mock_conn.execute.assert_called_with("PRAGMA foreign_keys = ON")
        mock_conn.executescript.assert_called_once_with(migration_sql)
        mock_conn.commit.assert_called_once()

    @patch('core.database.sqlite3.connect')
    def test_init_database_sqlite_error(self, mock_connect, temp_db_path):
        """Test database initialization with SQLite error."""
        mock_connect.side_effect = sqlite3.Error("Connection failed")

        db = DatabaseManager(temp_db_path)

        with pytest.raises(DatabaseError, match="Failed to initialize database"):
            db.init_database()

    @patch('core.database.sqlite3.connect')
    def test_get_schema_version_no_table(self, mock_connect, temp_db_path):
        """Test getting schema version when table doesn't exist."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.side_effect = sqlite3.Error("no such table")
        mock_connect.return_value = mock_conn

        db = DatabaseManager(temp_db_path)
        db.conn = mock_conn

        version = db._get_schema_version()
        assert version == 0

    @patch('core.database.sqlite3.connect')
    def test_get_schema_version_existing(self, mock_connect, temp_db_path):
        """Test getting schema version when table exists."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)
        mock_connect.return_value = mock_conn

        db = DatabaseManager(temp_db_path)
        db.conn = mock_conn

        version = db._get_schema_version()
        assert version == 1

    @patch('core.database.sqlite3.connect')
    def test_insert_event_success(self, mock_connect, temp_db_path, sample_event):
        """Test successful event insertion."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        db = DatabaseManager(temp_db_path)
        db.conn = mock_conn

        result = db.insert_event(sample_event)

        assert result is True
        mock_cursor.execute.assert_called_once()
        args, kwargs = mock_cursor.execute.call_args
        sql = args[0]
        data = args[1]

        # Verify SQL structure
        assert "INSERT INTO events" in sql
        assert len(data) == 8  # 8 fields
        assert data[0] == sample_event.event_id
        assert data[1] == sample_event.timestamp.isoformat()

        # Verify detected_objects JSON serialization
        detected_json = json.loads(data[4])
        assert len(detected_json) == 1
        assert detected_json[0]["label"] == "person"

        mock_conn.commit.assert_called_once()

    @patch('core.database.sqlite3.connect')
    def test_insert_event_duplicate(self, mock_connect, temp_db_path, sample_event):
        """Test event insertion with duplicate event_id."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed")
        mock_connect.return_value = mock_conn

        db = DatabaseManager(temp_db_path)
        db.conn = mock_conn

        result = db.insert_event(sample_event)

        assert result is False
        mock_conn.rollback.assert_called_once()

    @patch('core.database.sqlite3.connect')
    def test_insert_event_database_error(self, mock_connect, temp_db_path, sample_event):
        """Test event insertion with database error."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = sqlite3.Error("Disk full")
        mock_connect.return_value = mock_conn

        db = DatabaseManager(temp_db_path)
        db.conn = mock_conn

        with pytest.raises(DatabaseError, match="Failed to insert event"):
            db.insert_event(sample_event)

        mock_conn.rollback.assert_called_once()

    @patch('core.database.sqlite3.connect')
    def test_insert_event_not_initialized(self, mock_connect, temp_db_path, sample_event):
        """Test event insertion when database not initialized."""
        db = DatabaseManager(temp_db_path)
        # conn is None

        with pytest.raises(DatabaseError, match="Database not initialized"):
            db.insert_event(sample_event)

    def test_close(self, temp_db_path):
        """Test database connection closing."""
        mock_conn = MagicMock()
        db = DatabaseManager(temp_db_path)
        db.conn = mock_conn

        db.close()

        mock_conn.close.assert_called_once()
        assert db.conn is None