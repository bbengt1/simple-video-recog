"""Plaintext event logger for human-readable event persistence.

This module provides the PlaintextEventLogger class for writing
human-readable event logs with structured formatting for manual review.
"""

import os
import tempfile
import time
from pathlib import Path
from typing import List

from .config import SystemConfig
from .events import Event
from .logging_config import get_logger
from .models import DetectedObject


class PlaintextEventLogger:
    """Logger for writing human-readable plaintext event logs.

    Writes events to date-organized plaintext files with structured,
    human-readable formatting for manual review. Files are organized as
    data/events/YYYY-MM-DD/events.log with one event per block.

    Attributes:
        config: System configuration instance.
        logger: Configured logger instance.
    """

    def __init__(self, config: SystemConfig) -> None:
        """Initialize the plaintext event logger.

        Args:
            config: System configuration containing storage settings.
        """
        self.config = config
        self.logger = get_logger(__name__)

    def log_event(self, event: Event) -> bool:
        """Log an event to the appropriate plaintext file.

        Writes the event to a date-organized plaintext file using atomic
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

            # Construct file path: data/events/YYYY-MM-DD/events.log
            events_dir = Path("data/events")
            date_dir = events_dir / date_str
            log_file = date_dir / "events.log"

            # Create directories if they don't exist
            date_dir.mkdir(parents=True, exist_ok=True)

            # Format event as plaintext
            plaintext_entry = self._format_event(event)

            # Add separator if file already exists and has content
            if log_file.exists() and log_file.stat().st_size > 0:
                plaintext_entry = "\n" + plaintext_entry

            # Perform atomic write operation
            success = self._atomic_append(log_file, plaintext_entry)

            if success:
                # Log successful write with performance info
                elapsed_ms = (time.time() - start_time) * 1000
                self.logger.debug(
                    f"Event {event.event_id} logged to {log_file}",
                    extra={"performance_ms": elapsed_ms},
                )

                # Check performance target (<5ms)
                if elapsed_ms > 5.0:
                    self.logger.warning(
                        f"Plaintext logging exceeded performance target: {elapsed_ms:.2f}ms > 5ms",
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

    def _format_event(self, event: Event) -> str:
        """Format an event as human-readable plaintext.

        Args:
            event: Event to format.

        Returns:
            Formatted plaintext string with newline at end.
        """
        lines = []

        # Format timestamp in local timezone
        local_timestamp = event.timestamp.astimezone()
        timestamp_str = local_timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Create event header line with title
        lines.append(f"[{timestamp_str}] EVENT: {self._get_event_title(event)}")

        # Format detected objects (always include if there are any)
        if event.detected_objects:
            objects_str = self._format_detected_objects(event.detected_objects)
            lines.append(f"  - Objects: {objects_str}")

        # Add LLM description
        lines.append(f"  - Description: {event.llm_description}")

        # Add image path (relative from project root)
        lines.append(f"  - Image: {event.image_path}")

        return "\n".join(lines) + "\n"

    def _get_event_title(self, event: Event) -> str:
        """Generate a human-readable title for the event.

        Args:
            event: Event to generate title for.

        Returns:
            Human-readable event title.
        """
        # Try to create a meaningful title from detected objects
        if event.detected_objects:
            # Get the highest confidence object
            primary_object = max(event.detected_objects, key=lambda obj: obj.confidence)
            confidence_pct = int(primary_object.confidence * 100)
            return f"{primary_object.label.title()} detected (confidence: {confidence_pct}%)"

        # Fallback if no objects detected
        if event.motion_confidence is not None:
            confidence_pct = int(event.motion_confidence * 100)
            return f"Motion detected (confidence: {confidence_pct}%)"

        return "Motion detected"

    def _format_detected_objects(self, objects: List[DetectedObject]) -> str:
        """Format detected objects list for display.

        Args:
            objects: List of detected objects.

        Returns:
            Formatted string of objects with confidence percentages.
        """
        formatted_objects = []
        for obj in objects:
            confidence_pct = int(obj.confidence * 100)
            formatted_objects.append(f"{obj.label} ({confidence_pct}%)")

        return ", ".join(formatted_objects)

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
                    dir=target_file.parent, prefix=".events.log.tmp.", suffix=".tmp"
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
