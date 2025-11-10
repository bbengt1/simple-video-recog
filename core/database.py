"""Database manager for event persistence.

This module provides SQLite database operations for storing and retrieving
video recognition events. Handles schema initialization, migrations, and
atomic event insertion with proper error handling.
"""

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from core.events import Event
from core.exceptions import DatabaseError, DatabaseWriteError
from core.logging_config import get_logger
from core.models import DetectedObject


class DatabaseManager:
    """Database manager for event persistence.

    Handles SQLite database operations for storing and retrieving
    video recognition events. Manages schema migrations and provides
    atomic operations for event insertion.
    """

    def __init__(self, db_path: str):
        """Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.logger = get_logger(__name__)

    def init_database(self) -> None:
        """Initialize database schema and apply migrations.

        Creates database file if it doesn't exist, sets up tables,
        indexes, and applies any pending schema migrations.

        Raises:
            DatabaseError: If database initialization fails
        """
        try:
            # Create database directory if needed
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)

            # Connect to database
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys

            # Check current schema version
            current_version = self._get_schema_version()

            if current_version < 1:
                self._apply_migration("001_initial.sql")
                self.logger.info("Database initialized with schema version 1")
            else:
                self.logger.info(f"Database schema version {current_version} is up to date")

        except sqlite3.Error as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise DatabaseError(f"Failed to initialize database: {e}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error during database initialization: {e}")
            raise DatabaseError(f"Database initialization failed: {e}") from e

    def _get_schema_version(self) -> int:
        """Get current schema version from database.

        Returns:
            Current schema version, or 0 if schema_version table doesn't exist
        """
        if self.conn is None:
            raise DatabaseError("Database not initialized. Call init_database() first.")

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT MAX(version) FROM schema_version")
            result = cursor.fetchone()
            return result[0] if result and result[0] is not None else 0
        except sqlite3.Error:
            # schema_version table doesn't exist yet
            return 0

    def _apply_migration(self, migration_file: str) -> None:
        """Apply a database migration.

        Args:
            migration_file: Name of migration file in migrations/ directory

        Raises:
            DatabaseError: If migration fails
        """
        if self.conn is None:
            raise DatabaseError("Database not initialized. Call init_database() first.")

        migration_path = Path(__file__).parent.parent / "migrations" / migration_file

        if not migration_path.exists():
            raise DatabaseError(f"Migration file not found: {migration_path}")

        try:
            with open(migration_path, "r") as f:
                sql = f.read()

            # Execute migration within transaction
            self.conn.executescript(sql)
            self.conn.commit()

            self.logger.info(f"Applied migration: {migration_file}")

        except sqlite3.Error as e:
            self.conn.rollback()
            self.logger.error(f"Migration {migration_file} failed: {e}")
            raise DatabaseError(f"Migration {migration_file} failed: {e}") from e

    def insert_event(self, event: Event) -> bool:
        """Insert event into database.

        Args:
            event: Event object to persist

        Returns:
            True if inserted successfully, False if duplicate

        Raises:
            DatabaseWriteError: If write operation fails
        """
        if self.conn is None:
            raise DatabaseError("Database not initialized. Call init_database() first.")

        start_time = time.time()

        try:
            # Serialize detected_objects to JSON
            detected_objects_json = json.dumps([obj.model_dump() for obj in event.detected_objects])

            # Prepare data for insertion
            data = (
                event.event_id,
                event.timestamp.isoformat(),
                event.camera_id,
                event.motion_confidence,
                detected_objects_json,
                event.llm_description,
                event.image_path,
                event.json_log_path,
            )

            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO events (
                    event_id, timestamp, camera_id, motion_confidence,
                    detected_objects, llm_description, image_path, json_log_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                data,
            )

            self.conn.commit()

            # Performance monitoring
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms > 10:
                self.logger.warning(
                    f"Event insertion exceeded 10ms threshold: {elapsed_ms:.2f}ms for event {event.event_id}"
                )
            else:
                self.logger.debug(f"Inserted event: {event.event_id} in {elapsed_ms:.2f}ms")

            return True

        except sqlite3.IntegrityError:
            # UNIQUE constraint violation (duplicate event_id)
            self.conn.rollback()
            self.logger.warning(f"Duplicate event not inserted: {event.event_id}")
            return False
        except sqlite3.Error as e:
            self.conn.rollback()
            self.logger.error(f"Database write failed: {e}")
            raise DatabaseWriteError(f"Failed to write event to database: {e}") from e

    def insert_events(self, events: list[Event]) -> tuple[int, int]:
        """Insert multiple events into database.

        Args:
            events: List of Event objects to persist

        Returns:
            Tuple of (successful_inserts, failed_inserts)

        Raises:
            DatabaseWriteError: If batch write operation fails
        """
        if not events:
            return 0, 0

        if self.conn is None:
            raise DatabaseError("Database not initialized. Call init_database() first.")

        successful = 0
        failed = 0

        start_time = time.time()

        try:
            cursor = self.conn.cursor()

            for event in events:
                try:
                    # Serialize detected_objects to JSON
                    detected_objects_json = json.dumps(
                        [obj.model_dump() for obj in event.detected_objects]
                    )

                    # Prepare data for insertion
                    data = (
                        event.event_id,
                        event.timestamp.isoformat(),
                        event.camera_id,
                        event.motion_confidence,
                        detected_objects_json,
                        event.llm_description,
                        event.image_path,
                        event.json_log_path,
                    )

                    cursor.execute(
                        """
                        INSERT INTO events (
                            event_id, timestamp, camera_id, motion_confidence,
                            detected_objects, llm_description, image_path, json_log_path
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        data,
                    )

                    successful += 1

                except sqlite3.IntegrityError:
                    # UNIQUE constraint violation (duplicate event_id)
                    self.logger.warning(f"Duplicate event not inserted: {event.event_id}")
                    failed += 1
                except sqlite3.Error as e:
                    self.logger.error(f"Failed to insert event {event.event_id}: {e}")
                    failed += 1

            self.conn.commit()

            # Performance monitoring
            elapsed_ms = (time.time() - start_time) * 1000
            total_events = len(events)
            self.logger.info(
                f"Batch inserted {successful}/{total_events} events in {elapsed_ms:.2f}ms ({failed} failed)"
            )

            return successful, failed

        except sqlite3.Error as e:
            self.conn.rollback()
            self.logger.error(f"Database batch write failed: {e}")
            raise DatabaseWriteError(f"Failed to write events batch to database: {e}") from e

    def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """Retrieve a single event by its event_id.

        Args:
            event_id: Unique event identifier to search for

        Returns:
            Event object if found, None if not found

        Raises:
            DatabaseError: If database query fails
        """
        if self.conn is None:
            raise DatabaseError("Database not initialized. Call init_database() first.")

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT event_id, timestamp, camera_id, motion_confidence,
                       detected_objects, llm_description, image_path, json_log_path
                FROM events
                WHERE event_id = ?
            """,
                (event_id,),
            )

            row = cursor.fetchone()
            if row is None:
                return None

            # Deserialize detected_objects from JSON
            detected_objects_json = row[4]
            detected_objects = [DetectedObject(**obj) for obj in json.loads(detected_objects_json)]

            # Parse timestamp
            timestamp = datetime.fromisoformat(row[1])

            # Create Event object
            event = Event(
                event_id=row[0],
                timestamp=timestamp,
                camera_id=row[2],
                motion_confidence=row[3],
                detected_objects=detected_objects,
                llm_description=row[5],
                image_path=row[6],
                json_log_path=row[7],
            )

            return event

        except sqlite3.Error as e:
            self.logger.error(f"Database query failed for event_id {event_id}: {e}")
            raise DatabaseError(f"Failed to query event by ID: {e}") from e

    def get_events_by_timerange(
        self, start: datetime, end: datetime, offset: int = 0, limit: Optional[int] = None
    ) -> list[Event]:
        """Retrieve events within a timestamp range.

        Args:
            start: Start timestamp (inclusive)
            end: End timestamp (exclusive)
            offset: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of Event objects ordered by timestamp DESC

        Raises:
            DatabaseError: If database query fails
        """
        if self.conn is None:
            raise DatabaseError("Database not initialized. Call init_database() first.")

        start_time = time.time()

        try:
            cursor = self.conn.cursor()

            # Build query with optional limit
            query = """
                SELECT event_id, timestamp, camera_id, motion_confidence,
                       detected_objects, llm_description, image_path, json_log_path
                FROM events
                WHERE timestamp >= ? AND timestamp < ?
                ORDER BY timestamp DESC
            """

            params: list[Any] = [start.isoformat(), end.isoformat()]

            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)

            if offset > 0:
                query += " OFFSET ?"
                params.append(offset)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            events = []
            for row in rows:
                # Deserialize detected_objects from JSON
                detected_objects_json = row[4]
                detected_objects = [
                    DetectedObject(**obj) for obj in json.loads(detected_objects_json)
                ]

                # Parse timestamp
                timestamp = datetime.fromisoformat(row[1])

                # Create Event object
                event = Event(
                    event_id=row[0],
                    timestamp=timestamp,
                    camera_id=row[2],
                    motion_confidence=row[3],
                    detected_objects=detected_objects,
                    llm_description=row[5],
                    image_path=row[6],
                    json_log_path=row[7],
                )
                events.append(event)

            # Performance monitoring
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms > 50:
                self.logger.warning(
                    f"Timerange query exceeded 50ms threshold: {elapsed_ms:.2f}ms for {len(events)} results"
                )
            else:
                self.logger.debug(
                    f"Timerange query returned {len(events)} events in {elapsed_ms:.2f}ms"
                )

            return events

        except sqlite3.Error as e:
            self.logger.error(f"Database timerange query failed: {e}")
            raise DatabaseError(f"Failed to query events by timerange: {e}") from e

    def get_recent_events(self, limit: int = 100) -> list[Event]:
        """Retrieve the most recent events.

        Args:
            limit: Maximum number of events to return (default 100)

        Returns:
            List of most recent Event objects ordered by timestamp DESC

        Raises:
            DatabaseError: If database query fails
        """
        if self.conn is None:
            raise DatabaseError("Database not initialized. Call init_database() first.")

        start_time = time.time()

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT event_id, timestamp, camera_id, motion_confidence,
                       detected_objects, llm_description, image_path, json_log_path
                FROM events
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (limit,),
            )

            rows = cursor.fetchall()

            events = []
            for row in rows:
                # Deserialize detected_objects from JSON
                detected_objects_json = row[4]
                detected_objects = [
                    DetectedObject(**obj) for obj in json.loads(detected_objects_json)
                ]

                # Parse timestamp
                timestamp = datetime.fromisoformat(row[1])

                # Create Event object
                event = Event(
                    event_id=row[0],
                    timestamp=timestamp,
                    camera_id=row[2],
                    motion_confidence=row[3],
                    detected_objects=detected_objects,
                    llm_description=row[5],
                    image_path=row[6],
                    json_log_path=row[7],
                )
                events.append(event)

            # Performance monitoring
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms > 50:
                self.logger.warning(
                    f"Recent events query exceeded 50ms threshold: {elapsed_ms:.2f}ms for {len(events)} results"
                )
            else:
                self.logger.debug(
                    f"Recent events query returned {len(events)} events in {elapsed_ms:.2f}ms"
                )

            return events

        except sqlite3.Error as e:
            self.logger.error(f"Database recent events query failed: {e}")
            raise DatabaseError(f"Failed to query recent events: {e}") from e

    def count_events(self) -> int:
        """Count total number of events in database.

        Returns:
            Total number of events

        Raises:
            DatabaseError: If database query fails
        """
        if self.conn is None:
            raise DatabaseError("Database not initialized. Call init_database() first.")

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events")
            result = cursor.fetchone()
            return result[0] if result else 0

        except sqlite3.Error as e:
            self.logger.error(f"Database count query failed: {e}")
            raise DatabaseError(f"Failed to count events: {e}") from e

    def get_events_by_camera(self, camera_id: str, limit: int = 100) -> list[Event]:
        """Retrieve recent events for a specific camera.

        Args:
            camera_id: Camera identifier to filter by
            limit: Maximum number of events to return (default 100)

        Returns:
            List of Event objects for the camera ordered by timestamp DESC

        Raises:
            DatabaseError: If database query fails
        """
        if self.conn is None:
            raise DatabaseError("Database not initialized. Call init_database() first.")

        start_time = time.time()

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT event_id, timestamp, camera_id, motion_confidence,
                       detected_objects, llm_description, image_path, json_log_path
                FROM events
                WHERE camera_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (camera_id, limit),
            )

            rows = cursor.fetchall()

            events = []
            for row in rows:
                # Deserialize detected_objects from JSON
                detected_objects_json = row[4]
                detected_objects = [
                    DetectedObject(**obj) for obj in json.loads(detected_objects_json)
                ]

                # Parse timestamp
                timestamp = datetime.fromisoformat(row[1])

                # Create Event object
                event = Event(
                    event_id=row[0],
                    timestamp=timestamp,
                    camera_id=row[2],
                    motion_confidence=row[3],
                    detected_objects=detected_objects,
                    llm_description=row[5],
                    image_path=row[6],
                    json_log_path=row[7],
                )
                events.append(event)

            # Performance monitoring
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms > 50:
                self.logger.warning(
                    f"Camera events query exceeded 50ms threshold: {elapsed_ms:.2f}ms for {len(events)} results"
                )
            else:
                self.logger.debug(
                    f"Camera events query returned {len(events)} events in {elapsed_ms:.2f}ms"
                )

            return events

        except sqlite3.Error as e:
            self.logger.error(f"Database camera events query failed for camera {camera_id}: {e}")
            raise DatabaseError(f"Failed to query events by camera: {e}") from e

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.logger.info("Database connection closed")
