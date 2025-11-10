# Health check endpoint for API

import time
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.dependencies import get_db_connection

router = APIRouter()

# Module-level startup time
startup_time = time.time()

class HealthResponse(BaseModel):
    status: str
    database: str
    uptime_seconds: int
    version: str
    timestamp: datetime

@router.get("/health", response_model=HealthResponse)
async def health_check(db_conn = Depends(get_db_connection)):
    """
    Health check endpoint.

    Returns service status including database connectivity and uptime.
    """
    # Check database
    db_status = "ok"
    try:
        cursor = db_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        cursor.fetchone()
    except Exception:
        db_status = "error"

    # Calculate uptime
    uptime = int(time.time() - startup_time)

    # Determine overall status
    overall_status = "healthy" if db_status == "ok" else "degraded"

    return HealthResponse(
        status=overall_status,
        database=db_status,
        uptime_seconds=uptime,
        version="1.0.0",
        timestamp=datetime.now()
    )
