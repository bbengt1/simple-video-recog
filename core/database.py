"""Database manager for event persistence.

This module provides SQLite database operations for storing and retrieving
video recognition events. Handles schema initialization, migrations, and
atomic event insertion with proper error handling.
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional

from core.events import Event
from core.exceptions import DatabaseError
from core.logging_config import get_logger


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
            with open(migration_path, 'r') as f:
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
            DatabaseError: If insertion fails
        """
        if self.conn is None:
            raise DatabaseError("Database not initialized. Call init_database() first.")

        try:
            # Serialize detected_objects to JSON
            detected_objects_json = json.dumps([
                obj.model_dump() for obj in event.detected_objects
            ])

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
            cursor.execute("""
                INSERT INTO events (
                    event_id, timestamp, camera_id, motion_confidence,
                    detected_objects, llm_description, image_path, json_log_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, data)

            self.conn.commit()
            self.logger.debug(f"Inserted event: {event.event_id}")
            return True

        except sqlite3.IntegrityError:
            # UNIQUE constraint violation (duplicate event_id)
            self.conn.rollback()
            self.logger.warning(f"Duplicate event not inserted: {event.event_id}")
            return False
        except sqlite3.Error as e:
            self.conn.rollback()
            self.logger.error(f"Database insertion failed: {e}")
            raise DatabaseError(f"Failed to insert event: {e}") from e

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.logger.info("Database connection closed")
