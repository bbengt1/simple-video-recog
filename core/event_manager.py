# Event manager for creating and broadcasting events

from typing import Optional, Union
import logging

from core.database import DatabaseManager
from core.events import Event
from core.logging_config import get_logger

logger = get_logger(__name__)


class EventManager:
    """
    Manages event creation, persistence, and broadcasting.

    Updated in Story 5.3 to support WebSocket broadcasting for real-time updates.
    """

    def __init__(
        self,
        database_manager: DatabaseManager,
        websocket_manager=None  # Optional WebSocket support
    ):
        """Initialize EventManager with dependencies.

        Args:
            database_manager: Database manager for persistence
            websocket_manager: Optional WebSocket manager for broadcasting
        """
        self.database_manager = database_manager
        self.websocket_manager = websocket_manager

    def create_event(
        self,
        event_id: str,
        timestamp,
        camera_id: str,
        motion_confidence: Optional[float],
        detected_objects,
        llm_description: str,
        image_path: str,
        json_log_path: str,
        metadata: Optional[dict] = None
    ) -> Optional[Event]:
        """
        Create and persist an event.

        Args:
            event_id: Unique event identifier
            timestamp: Event timestamp
            camera_id: Camera identifier
            motion_confidence: Motion detection confidence
            detected_objects: List of detected objects
            llm_description: LLM-generated description
            image_path: Path to annotated image
            json_log_path: Path to JSON log file
            metadata: Additional event metadata

        Returns:
            Created Event object, or None if creation failed
        """
        try:
            # Create Event object
            event = Event(
                event_id=event_id,
                timestamp=timestamp,
                camera_id=camera_id,
                motion_confidence=motion_confidence,
                detected_objects=detected_objects,
                llm_description=llm_description,
                image_path=image_path,
                json_log_path=json_log_path,
                metadata=metadata or {}
            )

            # Persist to database
            try:
                self.database_manager.insert_event(event)
                logger.debug(f"Inserted event into database: {event_id}")
            except Exception as e:
                logger.error(f"Failed to persist event {event_id} to database: {e}")
                return None

            logger.info(f"Event created: {event_id}, objects={len(detected_objects)}")

            # Broadcast to WebSocket clients (Story 5.3)
            if self.websocket_manager:
                try:
                    # Convert Event to dict for JSON serialization
                    event_dict = event.model_dump(mode='json')

                    # Broadcast asynchronously (non-blocking)
                    import asyncio
                    asyncio.create_task(
                        self.websocket_manager.broadcast_event(event_dict)
                    )
                    logger.debug(f"Event broadcast to WebSocket: {event_id}")

                except Exception as e:
                    # WebSocket errors should not fail event creation
                    logger.warning(f"WebSocket broadcast failed for event {event_id}: {e}")

            return event

        except Exception as e:
            logger.error(f"Failed to create event {event_id}: {e}")
            return None