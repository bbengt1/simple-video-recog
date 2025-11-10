# API models for request/response validation

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Bounding box coordinates for detected objects."""
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)


class DetectedObject(BaseModel):
    """Object detected by CoreML."""
    label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: BoundingBox


class Event(BaseModel):
    """Event response model."""
    event_id: str
    timestamp: datetime
    camera_id: str
    motion_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    detected_objects: List[DetectedObject]
    llm_description: str
    image_path: str
    json_log_path: Optional[str] = None
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "evt_1699459335_a7b3c",
                "timestamp": "2025-11-08T14:32:15Z",
                "camera_id": "front_door",
                "motion_confidence": 0.87,
                "detected_objects": [
                    {
                        "label": "person",
                        "confidence": 0.92,
                        "bbox": {"x": 120, "y": 50, "width": 180, "height": 320}
                    }
                ],
                "llm_description": "Person in blue shirt carrying package",
                "image_path": "/images/2025-11-08/evt_1699459335_a7b3c.jpg",
                "created_at": "2025-11-08T14:32:16Z"
            }
        }


class EventListResponse(BaseModel):
    """Event list response with pagination."""
    events: List[Event]
    total: int = Field(..., ge=0)
    limit: int = Field(..., ge=1, le=1000)
    offset: int = Field(..., ge=0)


class MetricsResponse(BaseModel):
    """System metrics response."""
    timestamp: datetime
    frames_processed: int
    motion_detected: int
    motion_hit_rate: float
    events_created: int
    events_suppressed: int
    coreml_inference_avg: float
    coreml_inference_min: float
    coreml_inference_max: float
    coreml_inference_p95: float
    llm_inference_avg: float
    llm_inference_min: float
    llm_inference_max: float
    llm_inference_p95: float
    frame_processing_latency_avg: float
    cpu_usage_current: float
    cpu_usage_avg: float
    memory_usage_mb: float
    memory_usage_gb: float
    memory_usage_percent: float
    system_uptime_percent: float
    version: str


class ConfigResponse(BaseModel):
    """Sanitized system configuration (excludes sensitive fields)."""
    camera_id: str
    motion_threshold: float
    frame_sample_rate: int
    blacklist_objects: List[str]
    min_object_confidence: float
    ollama_model: str
    max_storage_gb: float
    min_retention_days: int
    log_level: str
    metrics_interval: int
    version: str


class ErrorDetail(BaseModel):
    """Error response detail."""
    code: str
    message: str
    timestamp: datetime
    request_id: str


class ErrorResponse(BaseModel):
    """Error response wrapper."""
    error: ErrorDetail
