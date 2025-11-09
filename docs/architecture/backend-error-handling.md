# Backend Error Handling

## FastAPI Error Handler

```python
# api/server.py
"""FastAPI server with centralized error handling."""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime
import logging
import traceback
import uuid

from core.exceptions import (
    VideoRecognitionError,
    DatabaseError,
    RTSPConnectionError,
    CoreMLInferenceError,
    OllamaServiceError
)

logger = logging.getLogger(__name__)
app = FastAPI()


# Standard error response model
class ErrorResponse:
    """Standard error response format."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        details: dict = None,
        request_id: str = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.request_id = request_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self):
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "timestamp": self.timestamp,
                "requestId": self.request_id
            }
        }


# Exception handlers

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors (invalid request parameters)."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    # Extract validation error details
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(
        f"Validation error: {errors}",
        extra={"request_id": request_id, "path": request.url.path}
    )

    error_response = ErrorResponse(
        code="INVALID_PARAMETERS",
        message="Request validation failed",
        status_code=400,
        details={"errors": errors},
        request_id=request_id
    )

    return JSONResponse(
        status_code=400,
        content=error_response.to_dict()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTPException (404, 403, etc.)."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    # Map status codes to error codes
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "RESOURCE_NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "RATE_LIMIT_EXCEEDED"
    }

    error_code = code_map.get(exc.status_code, "HTTP_ERROR")

    logger.warning(
        f"{exc.status_code} error: {exc.detail}",
        extra={"request_id": request_id, "path": request.url.path}
    )

    error_response = ErrorResponse(
        code=error_code,
        message=exc.detail,
        status_code=exc.status_code,
        details=getattr(exc, "details", {}),
        request_id=request_id
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.to_dict()
    )


@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    """Handle database-related errors."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    logger.error(
        f"Database error: {exc}",
        exc_info=True,
        extra={"request_id": request_id, "path": request.url.path}
    )

    error_response = ErrorResponse(
        code="DATABASE_ERROR",
        message="Failed to retrieve data from database",
        status_code=500,
        details={"retryable": True},
        request_id=request_id
    )

    return JSONResponse(
        status_code=500,
        content=error_response.to_dict()
    )


@app.exception_handler(OllamaServiceError)
async def ollama_error_handler(request: Request, exc: OllamaServiceError):
    """Handle Ollama LLM service errors."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    logger.error(
        f"Ollama service error: {exc}",
        exc_info=True,
        extra={"request_id": request_id}
    )

    error_response = ErrorResponse(
        code="SERVICE_UNAVAILABLE",
        message="LLM service is unavailable",
        status_code=503,
        details={
            "service": "ollama",
            "retryAfter": 60
        },
        request_id=request_id
    )

    return JSONResponse(
        status_code=503,
        content=error_response.to_dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unexpected errors."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    # Log full traceback for debugging
    logger.critical(
        f"Unexpected error: {exc}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )

    # Don't expose internal error details to client
    error_response = ErrorResponse(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please try again later.",
        status_code=500,
        details={
            "requestId": request_id  # Include for support/debugging
        },
        request_id=request_id
    )

    return JSONResponse(
        status_code=500,
        content=error_response.to_dict()
    )
```

## Raising HTTP Exceptions in Endpoints

```python
# api/endpoints.py
from fastapi import HTTPException
from core.database import DatabaseManager
from core.exceptions import DatabaseError

@app.get("/api/v1/events/{event_id}")
async def get_event(event_id: str, db: DatabaseManager = Depends(get_db)):
    """Get event by ID."""
    try:
        event = db.get_event_by_id(event_id)

        if event is None:
            # Resource not found - raise 404
            raise HTTPException(
                status_code=404,
                detail="Event not found",
                # Optional: Add custom details
                # details={"event_id": event_id, "resource_type": "Event"}
            )

        return event.model_dump()

    except DatabaseError as e:
        # Database error - will be caught by database_error_handler
        raise

    except Exception as e:
        # Unexpected error - will be caught by general_exception_handler
        logger.error(f"Error retrieving event {event_id}: {e}", exc_info=True)
        raise
```

## Custom Exception Raising in Business Logic

```python
# core/database.py
from core.exceptions import DatabaseError

class DatabaseManager:
    """Database manager with proper error handling."""

    def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """Get event by ID with error handling."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM events WHERE event_id = ?",
                (event_id,)
            )
            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_event(row)

        except sqlite3.Error as e:
            # Wrap SQLite error in custom exception
            logger.error(
                f"Database query failed: {e}",
                exc_info=True,
                extra={"event_id": event_id}
            )
            raise DatabaseError(f"Failed to retrieve event {event_id}") from e

        except Exception as e:
            # Unexpected error
            logger.critical(
                f"Unexpected error in get_event_by_id: {e}",
                exc_info=True
            )
            raise
```

---
