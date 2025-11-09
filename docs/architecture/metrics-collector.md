# Metrics Collector

**Responsibility:** Collects system performance metrics (frame processing, inference times, CPU/memory usage), calculates percentiles, logs to metrics.json.

**Key Interfaces:**
- `collect() -> MetricsSnapshot`: Gather current metrics
- `record_inference_time(component: str, time_ms: float) -> None`: Track inference time
- `increment_counter(metric: str) -> None`: Increment event/frame counters

**Dependencies:**
- psutil (for CPU/memory monitoring)
- Pydantic MetricsSnapshot model
- SystemConfig (for metrics_interval)

**Technology Stack:**
- Python 3.10+, psutil library
- Module path: `core/metrics.py`
- Class: `MetricsCollector`

**Implementation Notes:**
- Metrics logged every 60 seconds (configurable via metrics_interval)
- Inference times stored in rolling window (last 1000 events)
- Percentiles calculated using numpy.percentile (p95)
- Metrics file: logs/metrics.json (JSON Lines format)
- Overhead target: <1% CPU (measured via profiling)

---
