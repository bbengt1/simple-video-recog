# Event API endpoints for querying and retrieving events

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path as FilePath
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import FileResponse

from api.dependencies import get_db_connection
from api.models import BoundingBox, DetectedObject, Event, EventListResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/events", response_model=EventListResponse)
async def list_events(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    start: Optional[datetime] = Query(None, description="Start of time range (ISO 8601)"),
    end: Optional[datetime] = Query(None, description="End of time range (ISO 8601)"),
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    db_conn = Depends(get_db_connection)
):
    """
    List events with pagination and filtering.

    Query events from the database with optional time range and camera filtering.
    Results are ordered by timestamp DESC (newest first).
    """
    request_id = str(uuid.uuid4())[:8]

    try:
        cursor = db_conn.cursor()

        # Build query
        query = "SELECT * FROM events WHERE 1=1"
        params = []

        if start:
            query += " AND timestamp >= ?"
            params.append(start.isoformat())

        if end:
            query += " AND timestamp <= ?"
            params.append(end.isoformat())

        if camera_id:
            query += " AND camera_id = ?"
            params.append(camera_id)

        # Count total
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        # Get paginated results
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert rows to Event models
        events = []
        for row in rows:
            # Parse detected_objects JSON
            detected_objects = json.loads(row['detected_objects']) if row['detected_objects'] else []
            detected_objects = [
                DetectedObject(
                    label=obj['label'],
                    confidence=obj['confidence'],
                    bbox=BoundingBox(**obj['bbox'])
                )
                for obj in detected_objects
            ]

            event = Event(
                event_id=row['event_id'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                camera_id=row['camera_id'],
                motion_confidence=row['motion_confidence'],
                detected_objects=detected_objects,
                llm_description=row['llm_description'],
                image_path=f"/images/{row['image_path'].split('/')[-2]}/{row['image_path'].split('/')[-1]}",
                created_at=datetime.fromisoformat(row['created_at'])
            )
            events.append(event)

        logger.info(f"[{request_id}] Listed {len(events)} events (total: {total}, limit: {limit}, offset: {offset})")

        return EventListResponse(
            events=events,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"[{request_id}] Error listing events: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/events/{event_id}", response_model=Event)
async def get_event(
    event_id: str = Path(..., description="Event identifier"),
    db_conn = Depends(get_db_connection)
):
    """
    Get single event by ID.

    Returns full event details including all detected objects and metadata.
    """
    request_id = str(uuid.uuid4())[:8]

    try:
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
        row = cursor.fetchone()

        if not row:
            logger.warning(f"[{request_id}] Event not found: {event_id}")
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "EVENT_NOT_FOUND",
                    "message": f"Event with ID '{event_id}' not found",
                    "timestamp": datetime.now().isoformat(),
                    "request_id": request_id
                }
            )

        # Parse detected_objects JSON
        detected_objects = json.loads(row['detected_objects']) if row['detected_objects'] else []
        detected_objects = [
            DetectedObject(
                label=obj['label'],
                confidence=obj['confidence'],
                bbox=BoundingBox(**obj['bbox'])
            )
            for obj in detected_objects
        ]

        event = Event(
            event_id=row['event_id'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            camera_id=row['camera_id'],
            motion_confidence=row['motion_confidence'],
            detected_objects=detected_objects,
            llm_description=row['llm_description'],
            image_path=f"/images/{row['image_path'].split('/')[-2]}/{row['image_path'].split('/')[-1]}",
            json_log_path=row['json_log_path'],
            created_at=datetime.fromisoformat(row['created_at'])
        )

        logger.info(f"[{request_id}] Retrieved event: {event_id}")
        return event

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error retrieving event {event_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/events/{event_id}/image")
async def get_event_image(
    event_id: str = Path(..., description="Event identifier"),
    db_conn = Depends(get_db_connection)
):
    """
    Get annotated image for event.

    Returns JPEG image with bounding boxes drawn on detected objects.
    Includes HTTP caching headers for 7-day cache.
    """
    request_id = str(uuid.uuid4())[:8]

    try:
        # Get event to find image path
        cursor = db_conn.cursor()
        cursor.execute("SELECT image_path FROM events WHERE event_id = ?", (event_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "EVENT_NOT_FOUND",
                    "message": f"Event with ID '{event_id}' not found",
                    "timestamp": datetime.now().isoformat(),
                    "request_id": request_id
                }
            )

        image_path = FilePath(row['image_path'])

        if not image_path.exists():
            logger.warning(f"[{request_id}] Image not found for event {event_id}: {image_path}")
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "IMAGE_NOT_FOUND",
                    "message": f"Image for event '{event_id}' not found",
                    "timestamp": datetime.now().isoformat(),
                    "request_id": request_id
                }
            )

        logger.info(f"[{request_id}] Serving image for event {event_id}: {image_path}")

        return FileResponse(
            image_path,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "public, max-age=604800",  # 7 days
                "X-Request-ID": request_id
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error serving image for event {event_id}: {e}")
        raise HTTPException(status_code=500, detail=f"File system error: {str(e)}")
