# Key Metrics

## Frontend Metrics (Phase 2)

**Core Web Vitals:**
- **LCP (Largest Contentful Paint):** <2.5s (time until main content is visible)
- **FID (First Input Delay):** <100ms (time until page is interactive)
- **CLS (Cumulative Layout Shift):** <0.1 (visual stability score)

**Application Metrics:**
- **Page Load Time:** Time from navigation to interactive (<500ms target)
- **API Response Time:** Time for API calls to complete (<100ms for event list)
- **WebSocket Latency:** Time from server send to client receive (<50ms)
- **JavaScript Errors:** Count of unhandled exceptions (target: 0)
- **API Error Rate:** Percentage of failed API calls (target: <1%)

**Collection Method:**
```javascript
// Performance measurement
performance.mark('events-fetch-start')
const events = await api.events()
performance.mark('events-fetch-end')
performance.measure('events-fetch', 'events-fetch-start', 'events-fetch-end')

const measure = performance.getEntriesByName('events-fetch')[0]
console.log(`Events fetch took ${measure.duration}ms`)
```

---

## Backend Metrics

**Processing Pipeline Metrics:**
- **frames_processed**: Total frames captured from RTSP stream
- **motion_detected**: Count of frames with motion (hit rate: motion/total)
- **events_created**: Total events generated (after filtering and de-duplication)
- **events_suppressed**: Count of events suppressed by de-duplication logic

**Performance Metrics:**
- **coreml_inference_time**: CoreML object detection time in ms (p50, p95, p99)
  - **Target:** p95 <100ms (NFR requirement)
- **llm_inference_time**: Ollama LLM inference time in seconds (p50, p95, p99)
  - **Target:** p95 <3s (NFR requirement)
- **frame_processing_latency**: End-to-end time from motion detection to event logged (ms)
  - **Target:** <5s average
- **db_write_time**: Database insert operation time (ms)
  - **Target:** <10ms average

**Resource Metrics:**
- **cpu_usage**: Current CPU usage percentage (0-100%)
  - **Target:** <50% sustained on M1
- **memory_usage_mb**: Current memory usage in MB
  - **Target:** <2GB
- **storage_usage_gb**: Total storage used by data/events directory
  - **Target:** <4GB (hard limit)
- **storage_percentage**: Percentage of max_storage_gb used
  - **Warning:** >80% (triggers log rotation)
  - **Critical:** >100% (triggers graceful shutdown)

**Availability Metrics:**
- **uptime_seconds**: Time since pipeline started
- **system_availability**: Uptime as percentage (target: >99% during 24/7 operation)
- **rtsp_connection_failures**: Count of RTSP reconnection attempts
- **ollama_failures**: Count of Ollama service unavailable errors

**Metrics Collection Example:**

```python
# core/metrics.py
from dataclasses import dataclass
from datetime import datetime
from typing import List
import numpy as np
import psutil
import time

@dataclass
class MetricsSnapshot:
    """Snapshot of system metrics at a point in time."""
    timestamp: datetime
    frames_processed: int
    motion_detected: int
    events_created: int
    events_suppressed: int
    coreml_inference_avg: float
    coreml_inference_p95: float
    llm_inference_avg: float
    llm_inference_p95: float
    cpu_usage: float
    memory_usage_mb: int
    storage_usage_gb: float
    uptime_seconds: int


class MetricsCollector:
    """Collects and logs system performance metrics."""

    def __init__(self, interval: int = 60):
        self.interval = interval
        self.start_time = time.time()

        # Counters
        self.frames_processed = 0
        self.motion_detected = 0
        self.events_created = 0
        self.events_suppressed = 0

        # Performance metrics (rolling window)
        self.coreml_times: List[float] = []
        self.llm_times: List[float] = []
        self.max_samples = 1000  # Keep last 1000 samples

    def record_inference_time(self, component: str, time_ms: float):
        """Record inference time for CoreML or LLM."""
        if component == "coreml":
            self.coreml_times.append(time_ms)
            if len(self.coreml_times) > self.max_samples:
                self.coreml_times.pop(0)
        elif component == "llm":
            self.llm_times.append(time_ms)
            if len(self.llm_times) > self.max_samples:
                self.llm_times.pop(0)

    def increment_counter(self, metric: str):
        """Increment a counter metric."""
        if metric == "frames_processed":
            self.frames_processed += 1
        elif metric == "motion_detected":
            self.motion_detected += 1
        elif metric == "events_created":
            self.events_created += 1
        elif metric == "events_suppressed":
            self.events_suppressed += 1

    def collect(self) -> MetricsSnapshot:
        """Collect current metrics snapshot."""
        # Calculate percentiles
        coreml_avg = np.mean(self.coreml_times) if self.coreml_times else 0.0
        coreml_p95 = np.percentile(self.coreml_times, 95) if self.coreml_times else 0.0
        llm_avg = np.mean(self.llm_times) if self.llm_times else 0.0
        llm_p95 = np.percentile(self.llm_times, 95) if self.llm_times else 0.0

        # Get system resources
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory_usage_mb = psutil.Process().memory_info().rss / (1024 * 1024)

        # Calculate storage usage
        storage_usage_gb = self._calculate_storage_usage()

        # Calculate uptime
        uptime_seconds = int(time.time() - self.start_time)

        return MetricsSnapshot(
            timestamp=datetime.utcnow(),
            frames_processed=self.frames_processed,
            motion_detected=self.motion_detected,
            events_created=self.events_created,
            events_suppressed=self.events_suppressed,
            coreml_inference_avg=coreml_avg,
            coreml_inference_p95=coreml_p95,
            llm_inference_avg=llm_avg,
            llm_inference_p95=llm_p95,
            cpu_usage=cpu_usage,
            memory_usage_mb=int(memory_usage_mb),
            storage_usage_gb=storage_usage_gb,
            uptime_seconds=uptime_seconds
        )

    def _calculate_storage_usage(self) -> float:
        """Calculate total storage usage in GB."""
        from pathlib import Path
        total_bytes = sum(
            f.stat().st_size
            for f in Path("data/events").rglob("*")
            if f.is_file()
        )
        return total_bytes / (1024 ** 3)  # Convert to GB
```

**Metrics Logging:**

```python
# Log metrics to JSON Lines file every 60 seconds
import json

def log_metrics(metrics: MetricsSnapshot):
    """Log metrics snapshot to metrics.json."""
    with open("logs/metrics.json", "a") as f:
        f.write(json.dumps({
            "timestamp": metrics.timestamp.isoformat(),
            "frames_processed": metrics.frames_processed,
            "motion_detected": metrics.motion_detected,
            "events_created": metrics.events_created,
            "events_suppressed": metrics.events_suppressed,
            "coreml_inference_avg": round(metrics.coreml_inference_avg, 2),
            "coreml_inference_p95": round(metrics.coreml_inference_p95, 2),
            "llm_inference_avg": round(metrics.llm_inference_avg, 2),
            "llm_inference_p95": round(metrics.llm_inference_p95, 2),
            "cpu_usage": round(metrics.cpu_usage, 1),
            "memory_usage_mb": metrics.memory_usage_mb,
            "storage_usage_gb": round(metrics.storage_usage_gb, 2),
            "uptime_seconds": metrics.uptime_seconds
        }) + "\n")
```

---
