"""Event data models for the video recognition system.

This module defines the Event model and related functionality for
representing motion-triggered detection events with all metadata.
"""

import secrets
import time
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from core.config import SystemConfig
from core.logging_config import get_logger
from core.models import DetectedObject, DetectionResult


class Event(BaseModel):
    """Core event entity representing a motion-triggered detection.

    Represents a single motion-triggered event captured from the camera,
    processed through the pipeline, and ready for storage. Contains all
    information about detected objects and semantic descriptions.
    """

    event_id: str = Field(
        ...,
        description="Unique event identifier"
    )
    timestamp: datetime = Field(
        ...,
        description="Event occurrence time (UTC)"
    )
    camera_id: str = Field(
        ...,
        description="Camera identifier",
        examples=["camera_1"]
    )
    llm_description: str = Field(
        ...,
        description="Semantic description from Ollama LLM",
        examples=["Person in blue shirt carrying brown package approaching front door"]
    )
    image_path: str = Field(
        ...,
        description="Path to annotated image",
        examples=["data/events/2025-11-08/evt_1699459335_a7b3c.jpg"]
    )
    json_log_path: str = Field(
        ...,
        description="Path to JSON log file containing this event",
        examples=["data/events/2025-11-08/events.json"]
    )
    motion_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Motion detection confidence score"
    )
    detected_objects: List[DetectedObject] = Field(
        default_factory=list,
        description="Objects detected by CoreML"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional event metadata"
    )

    model_config = ConfigDict()

    @classmethod
    def generate_event_id(cls) -> str:
        """Generate a unique event ID.

        Creates a unique identifier using timestamp (milliseconds) and
        random suffix to ensure uniqueness across multiple events.

        Returns:
            Unique event ID string in format "evt_{timestamp}_{random}"
        """
        timestamp_ms = int(time.time() * 1000)
        random_suffix = secrets.token_hex(2)  # 4 characters
        return f"evt_{timestamp_ms}_{random_suffix}"

    def to_json(self) -> str:
        """Serialize Event to JSON string.

        Returns:
            JSON string representation with proper formatting
        """
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        """Deserialize JSON string to Event object.

        Args:
            json_str: JSON string representation of an Event

        Returns:
            Event object reconstructed from JSON
        """
        return cls.model_validate_json(json_str)


class EventDeduplicator:
    """Deduplicates events based on object detection results.

    Prevents alert spam by suppressing events for the same primary object
    within a configurable time window. Uses highest-confidence detected
    object as the primary key for deduplication.
    """

    def __init__(self, config: SystemConfig):
        """Initialize deduplicator with configuration.

        Args:
            config: System configuration containing deduplication settings
        """
        self.config = config
        self.deduplication_window = config.deduplication_window
        self._cache: dict[str, float] = {}  # {object_label: last_timestamp}
        self.logger = get_logger(__name__)

    def should_create_event(self, detections: DetectionResult) -> bool:
        """Check if event should be created based on deduplication rules.

        Uses the highest-confidence detected object as the primary key.
        If this object was detected within the deduplication window,
        the event is suppressed.

        Args:
            detections: CoreML detection results

        Returns:
            True if event should be created, False if suppressed
        """
        if not detections.objects:
            return False  # No objects detected, no event to deduplicate

        # Find primary object (highest confidence)
        primary_object = max(detections.objects, key=lambda obj: obj.confidence)
        current_time = time.time()

        # Check if primary object was recently detected
        last_detection = self._cache.get(primary_object.label)
        if last_detection is not None:
            time_since_last = current_time - last_detection
            if time_since_last < self.deduplication_window:
                # Suppress event - log at DEBUG level
                self.logger.debug(
                    f"Event suppressed: {primary_object.label} detected "
                    f"{time_since_last:.1f}s ago (within {self.deduplication_window}s window)"
                )
                return False

        # Create event - update cache with current timestamp
        self._cache[primary_object.label] = current_time

        # Periodic cache cleanup to prevent memory leaks
        self._cleanup_cache(current_time)

        return True

    def _cleanup_cache(self, current_time: float) -> None:
        """Remove old entries from cache to prevent unbounded memory growth.

        Removes entries older than 2x deduplication_window to ensure
        memory usage remains bounded while allowing for reasonable
        deduplication behavior.

        Args:
            current_time: Current timestamp for cleanup calculation
        """
        cleanup_threshold = current_time - (self.deduplication_window * 2)
        expired_keys = [
            key for key, timestamp in self._cache.items()
            if timestamp < cleanup_threshold
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            self.logger.debug(f"Cache cleanup: removed {len(expired_keys)} expired entries")
