"""JSON event logger for structured event persistence.

This module provides the JSONEventLogger class for writing events to
structured JSON log files organized by date. Uses JSON Lines format
for programmatic processing and atomic writes for data integrity.
"""

import os
import tempfile
import time
from pathlib import Path

from .config import SystemConfig
from .events import Event
from .logging_config import get_logger


class JSONEventLogger:
    """Logger for writing events to structured JSON files.

    Writes events to date-organized JSON Lines files with atomic operations
    to ensure data integrity. Files are organized as data/events/YYYY-MM-DD/events.json
    with one JSON object per line for easy programmatic processing.

    Attributes:
        config: System configuration instance.
        logger: Configured logger instance.
    """

    def __init__(self, config: SystemConfig) -> None:
        """Initialize the JSON event logger.

        Args:
            config: System configuration containing storage settings.
        """
        self.config = config
        self.logger = get_logger(__name__)

    def log_event(self, event: Event) -> bool:
        """Log an event to the appropriate JSON file.

        Writes the event to a date-organized JSON Lines file using atomic
        write operations. Creates directories as needed and ensures file
        integrity through temp file + rename pattern.

        Args:
            event: Event instance to log.

        Returns:
            True if logging succeeded, False otherwise.
        """
        start_time = time.time()

        try:
            # Extract date from event timestamp
            event_date = event.timestamp.date()
            date_str = event_date.strftime("%Y-%m-%d")

            # Construct file path: data/events/YYYY-MM-DD/events.json
            events_dir = Path("data/events")
            date_dir = events_dir / date_str
            json_file = date_dir / "events.json"

            # Create directories if they don't exist
            date_dir.mkdir(parents=True, exist_ok=True)

            # Serialize event to compact JSON for JSON Lines format
            json_line = event.model_dump_json() + "\n"

            # Perform atomic write operation
            success = self._atomic_append(json_file, json_line)

            if success:
                # Log successful write with performance info
                elapsed_ms = (time.time() - start_time) * 1000
                self.logger.debug(
                    f"Event {event.event_id} logged to {json_file}",
                    extra={"performance_ms": elapsed_ms},
                )

                # Check performance target (<5ms)
                if elapsed_ms > 5.0:
                    self.logger.warning(
                        f"JSON logging exceeded performance target: {elapsed_ms:.2f}ms > 5ms",
                        extra={"event_id": event.event_id, "performance_ms": elapsed_ms},
                    )

            return success

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            self.logger.error(
                f"Failed to log event {event.event_id}: {e}",
                extra={"event_id": event.event_id, "error": str(e), "performance_ms": elapsed_ms},
            )
            return False

    def _atomic_append(self, target_file: Path, content: str) -> bool:
        """Perform atomic append operation using temp file + rename.

        Args:
            target_file: Target file path to append to.
            content: Content to append.

        Returns:
            True if append succeeded, False otherwise.
        """
        try:
            # Create temp file in same directory for atomic rename
            temp_fd = None
            temp_path = None

            try:
                # Create temp file in target directory
                temp_fd, temp_path_str = tempfile.mkstemp(
                    dir=target_file.parent, prefix=".events.json.tmp.", suffix=".tmp"
                )
                temp_path = Path(temp_path_str)

                # If target file exists, copy existing content to temp file
                if target_file.exists():
                    with open(target_file, "r", encoding="utf-8") as existing:
                        temp_path.write_text(existing.read(), encoding="utf-8")

                # Append new content
                with open(temp_path, "a", encoding="utf-8") as temp_file:
                    temp_file.write(content)

                # Set proper permissions (0644)
                temp_path.chmod(0o644)

                # Atomic rename
                temp_path.rename(target_file)

                return True

            finally:
                # Clean up temp file if it still exists
                if temp_fd is not None:
                    try:
                        os.close(temp_fd)
                    except OSError:
                        pass
                if temp_path and temp_path.exists():
                    try:
                        temp_path.unlink()
                    except OSError:
                        pass

        except Exception as e:
            self.logger.error(f"Atomic append failed for {target_file}: {e}")
            return False
