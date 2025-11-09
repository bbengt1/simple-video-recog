# MetricsSnapshot

**Purpose:** Performance metrics collected periodically and logged to logs/metrics.json for monitoring system health and validating NFR targets.

**Key Attributes:**
- `timestamp` (datetime): When metrics were collected
- `frames_processed` (int): Total frames processed
- `motion_detected` (int): Frames with motion detected
- `events_created` (int): Total events created
- `events_suppressed` (int): Events suppressed by de-duplication
- `coreml_inference_avg` (float): Average CoreML inference time (ms)
- `llm_inference_avg` (float): Average LLM inference time (ms)
- `cpu_usage` (float): Current CPU usage percentage
- `memory_usage_mb` (int): Current memory usage in MB
- `storage_usage_gb` (float): Current storage usage in GB

## Pydantic Schema

```python
class MetricsSnapshot(BaseModel):
    """Performance metrics snapshot logged periodically."""

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Metrics collection timestamp"
    )

    # Processing Statistics
    frames_processed: int = Field(default=0, description="Total frames processed")
    motion_detected: int = Field(default=0, description="Frames with motion")
    events_created: int = Field(default=0, description="Events created")
    events_suppressed: int = Field(default=0, description="Events suppressed by de-duplication")

    # Performance Metrics
    coreml_inference_avg: float = Field(
        default=0.0,
        description="Average CoreML inference time (ms)"
    )
    coreml_inference_p95: float = Field(
        default=0.0,
        description="95th percentile CoreML inference time (ms)"
    )
    llm_inference_avg: float = Field(
        default=0.0,
        description="Average LLM inference time (ms)"
    )
    llm_inference_p95: float = Field(
        default=0.0,
        description="95th percentile LLM inference time (ms)"
    )

    # System Resources
    cpu_usage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="CPU usage percentage"
    )
    memory_usage_mb: int = Field(
        default=0,
        ge=0,
        description="Memory usage in MB"
    )
    storage_usage_gb: float = Field(
        default=0.0,
        ge=0,
        description="Storage usage in GB"
    )

    # Uptime
    uptime_seconds: int = Field(
        default=0,
        ge=0,
        description="System uptime in seconds"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-08T14:32:00Z",
                "frames_processed": 1500,
                "motion_detected": 120,
                "events_created": 15,
                "events_suppressed": 5,
                "coreml_inference_avg": 85.3,
                "coreml_inference_p95": 95.7,
                "llm_inference_avg": 2400.0,
                "llm_inference_p95": 2850.0,
                "cpu_usage": 45.2,
                "memory_usage_mb": 1850,
                "storage_usage_gb": 1.2,
                "uptime_seconds": 86400
            }
        }
```

## Relationships
- **Logged to** logs/metrics.json in JSON Lines format
- **Collected by** MetricsCollector component every 60 seconds

---
