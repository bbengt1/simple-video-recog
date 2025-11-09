# SystemConfig

**Purpose:** Configuration data loaded from YAML file, validated using Pydantic to ensure type safety and provide clear error messages for invalid configurations.

**Key Attributes:**
- `camera_rtsp_url` (str): RTSP stream URL
- `camera_id` (str): Camera identifier
- `motion_threshold` (float): Motion detection sensitivity
- `frame_sample_rate` (int): Frames to process per second
- `blacklist_objects` (list[str]): Object labels to filter out
- `ollama_base_url` (str): Ollama API endpoint
- `ollama_model` (str): LLM model name
- `db_path` (str): SQLite database file path
- `max_storage_gb` (float): Storage limit
- `log_level` (str): Logging verbosity

## Pydantic Schema

```python
from pydantic import BaseModel, Field, HttpUrl
from typing import List

class SystemConfig(BaseModel):
    """System configuration loaded from config/config.yaml."""

    # Camera Configuration
    camera_rtsp_url: str = Field(
        ...,
        description="RTSP stream URL",
        example="rtsp://admin:password@192.168.1.100:554/stream1"
    )
    camera_id: str = Field(
        default="camera_1",
        description="Camera identifier for multi-camera support"
    )

    # Motion Detection
    motion_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Motion detection sensitivity (0=very sensitive, 1=less sensitive)"
    )
    frame_sample_rate: int = Field(
        default=5,
        ge=1,
        le=30,
        description="Frames per second to process during motion"
    )

    # Object Detection
    coreml_model_path: str = Field(
        default="models/yolov8n.mlmodel",
        description="Path to CoreML model file"
    )
    blacklist_objects: List[str] = Field(
        default_factory=lambda: ["bird", "cat"],
        description="Object labels to ignore"
    )
    min_object_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence to include detected object"
    )

    # LLM Configuration
    ollama_base_url: HttpUrl = Field(
        default="http://localhost:11434",
        description="Ollama API endpoint"
    )
    ollama_model: str = Field(
        default="llava:7b",
        description="LLM model name (llava or moondream)"
    )
    llm_timeout: int = Field(
        default=10,
        ge=1,
        le=60,
        description="LLM request timeout in seconds"
    )

    # Storage
    db_path: str = Field(
        default="data/events.db",
        description="SQLite database file path"
    )
    max_storage_gb: float = Field(
        default=4.0,
        gt=0,
        description="Maximum storage limit in GB"
    )
    min_retention_days: int = Field(
        default=7,
        ge=1,
        description="Minimum days to retain events"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging verbosity (DEBUG, INFO, WARNING, ERROR)"
    )
    metrics_interval: int = Field(
        default=60,
        ge=10,
        description="Metrics collection interval in seconds"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "camera_rtsp_url": "rtsp://admin:password@192.168.1.100:554/stream1",
                "camera_id": "front_door",
                "motion_threshold": 0.5,
                "frame_sample_rate": 5,
                "coreml_model_path": "models/yolov8n.mlmodel",
                "blacklist_objects": ["bird", "cat"],
                "min_object_confidence": 0.5,
                "ollama_base_url": "http://localhost:11434",
                "ollama_model": "llava:7b",
                "llm_timeout": 10,
                "db_path": "data/events.db",
                "max_storage_gb": 4.0,
                "min_retention_days": 7,
                "log_level": "INFO",
                "metrics_interval": 60
            }
        }
```

## Relationships
- **Loaded from** config/config.yaml file
- **Validated on** application startup

---
