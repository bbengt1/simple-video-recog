"""Performance metrics collection and logging for the video recognition system."""

import time
from collections import deque
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import psutil
from pydantic import BaseModel, Field

from .config import SystemConfig
from .logging_config import get_logger
from .version import get_version_info


class MetricsSnapshot(BaseModel):
    """Snapshot of system performance metrics at a point in time."""

    timestamp: float = Field(description="Unix timestamp when metrics were collected")
    version: str = Field(description="Application version")

    # Processing statistics
    frames_processed: int = Field(default=0, description="Total frames processed")
    motion_detected: int = Field(default=0, description="Frames where motion was detected")
    motion_hit_rate: float = Field(default=0.0, description="Percentage of frames with motion")
    events_created: int = Field(default=0, description="Total events created")
    events_suppressed: int = Field(default=0, description="Events suppressed by de-duplication")

    # Performance metrics (in milliseconds)
    coreml_inference_avg: float = Field(default=0.0, description="Average CoreML inference time")
    coreml_inference_min: float = Field(default=0.0, description="Minimum CoreML inference time")
    coreml_inference_max: float = Field(default=0.0, description="Maximum CoreML inference time")
    coreml_inference_p95: float = Field(
        default=0.0, description="95th percentile CoreML inference time"
    )

    llm_inference_avg: float = Field(default=0.0, description="Average LLM inference time")
    llm_inference_min: float = Field(default=0.0, description="Minimum LLM inference time")
    llm_inference_max: float = Field(default=0.0, description="Maximum LLM inference time")
    llm_inference_p95: float = Field(default=0.0, description="95th percentile LLM inference time")

    frame_processing_latency_avg: float = Field(
        default=0.0, description="Average end-to-end frame processing latency"
    )
    frame_processing_latency_min: float = Field(
        default=0.0, description="Minimum end-to-end frame processing latency"
    )
    frame_processing_latency_max: float = Field(
        default=0.0, description="Maximum end-to-end frame processing latency"
    )
    frame_processing_latency_p95: float = Field(
        default=0.0, description="95th percentile end-to-end frame processing latency"
    )

    # System resources
    cpu_usage_current: float = Field(default=0.0, description="Current CPU usage percentage")
    cpu_usage_avg: float = Field(default=0.0, description="Average CPU usage percentage")
    memory_usage_mb: float = Field(default=0.0, description="Current memory usage in MB")
    memory_usage_gb: float = Field(default=0.0, description="Current memory usage in GB")
    memory_usage_percent: float = Field(default=0.0, description="Current memory usage percentage")

    # System availability
    system_uptime_percent: float = Field(default=100.0, description="System uptime percentage")
    system_start_time: float = Field(default=0.0, description="System start time (Unix timestamp)")

    # Performance overhead
    metrics_collection_overhead_percent: float = Field(
        default=0.0, description="CPU overhead of metrics collection"
    )


class MetricsCollector:
    """Collects and logs system performance metrics."""

    def __init__(self, config: SystemConfig):
        """Initialize the metrics collector.

        Args:
            config: System configuration containing metrics settings
        """
        self.config = config
        self.logger = get_logger(__name__)

        # Get version info once at initialization
        self.version_info = get_version_info()

        # Rolling window for timing measurements (last 1000 events)
        self.rolling_window_size = 1000
        self.coreml_times: deque[float] = deque(maxlen=self.rolling_window_size)
        self.llm_times: deque[float] = deque(maxlen=self.rolling_window_size)
        self.frame_latencies: deque[float] = deque(maxlen=self.rolling_window_size)

        # Counters
        self.frames_processed = 0
        self.motion_detected = 0
        self.events_created = 0
        self.events_suppressed = 0

        # System monitoring
        self.system_start_time = time.time()
        self.cpu_usage_history: deque[float] = deque(maxlen=100)  # Last 100 measurements

        # Metrics logging
        self.metrics_log_path = Path("logs/metrics.json")
        self.metrics_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.last_log_time = 0.0

    def increment_counter(self, metric_name: str) -> None:
        """Increment a counter metric.

        Args:
            metric_name: Name of the counter to increment
        """
        if metric_name == "frames_processed":
            self.frames_processed += 1
        elif metric_name == "motion_detected":
            self.motion_detected += 1
        elif metric_name == "events_created":
            self.events_created += 1
        elif metric_name == "events_suppressed":
            self.events_suppressed += 1
        else:
            self.logger.warning(f"Unknown counter metric: {metric_name}")

    def record_inference_time(self, component: str, time_ms: float) -> None:
        """Record inference timing for CoreML or LLM.

        Args:
            component: Either 'coreml' or 'llm'
            time_ms: Inference time in milliseconds
        """
        if component == "coreml":
            self.coreml_times.append(time_ms)
        elif component == "llm":
            self.llm_times.append(time_ms)
        else:
            self.logger.warning(f"Unknown component for inference timing: {component}")

    def record_frame_latency(self, latency_ms: float) -> None:
        """Record end-to-end frame processing latency.

        Args:
            latency_ms: Processing latency in milliseconds
        """
        self.frame_latencies.append(latency_ms)

    def _calculate_percentiles(self, data: deque) -> tuple[float, float, float, float]:
        """Calculate min, max, avg, and p95 from data.

        Args:
            data: Collection of timing measurements

        Returns:
            Tuple of (min, max, avg, p95) or (0, 0, 0, 0) if no data
        """
        if not data:
            return 0.0, 0.0, 0.0, 0.0

        data_list = list(data)
        min_val = min(data_list)
        max_val = max(data_list)
        avg_val = sum(data_list) / len(data_list)
        p95_val = float(np.percentile(data_list, 95))

        return min_val, max_val, avg_val, p95_val

    def _get_system_metrics(self) -> Dict[str, float]:
        """Get current system resource usage.

        Returns:
            Dictionary with CPU and memory metrics
        """
        # CPU usage (measure over 0.1 second interval)
        cpu_current = psutil.cpu_percent(interval=0.1)
        self.cpu_usage_history.append(cpu_current)
        cpu_avg = (
            sum(self.cpu_usage_history) / len(self.cpu_usage_history)
            if self.cpu_usage_history
            else 0.0
        )

        # Memory usage
        memory = psutil.virtual_memory()
        memory_mb = memory.used / (1024 * 1024)  # Convert to MB
        memory_gb = memory.used / (1024 * 1024 * 1024)  # Convert to GB
        memory_percent = memory.percent

        return {
            "cpu_current": cpu_current,
            "cpu_avg": cpu_avg,
            "memory_mb": memory_mb,
            "memory_gb": memory_gb,
            "memory_percent": memory_percent,
        }

    def _calculate_uptime_percent(self) -> float:
        """Calculate system uptime percentage.

        Returns:
            Uptime percentage (0-100)
        """
        current_time = time.time()
        total_runtime = current_time - self.system_start_time

        # For simplicity, assume system has been running continuously
        # In a real implementation, you'd track actual downtime events
        return 100.0 if total_runtime > 0 else 0.0

    def collect(self) -> MetricsSnapshot:
        """Collect current metrics snapshot.

        Returns:
            MetricsSnapshot with all current metric values
        """
        collection_start = time.time()

        # Calculate timing percentiles
        coreml_min, coreml_max, coreml_avg, coreml_p95 = self._calculate_percentiles(
            self.coreml_times
        )
        llm_min, llm_max, llm_avg, llm_p95 = self._calculate_percentiles(self.llm_times)
        latency_min, latency_max, latency_avg, latency_p95 = self._calculate_percentiles(
            self.frame_latencies
        )

        # Get system metrics
        system_metrics = self._get_system_metrics()

        # Calculate uptime
        uptime_percent = self._calculate_uptime_percent()

        # Calculate motion hit rate
        motion_hit_rate = (
            (self.motion_detected / self.frames_processed * 100)
            if self.frames_processed > 0
            else 0.0
        )

        # Create snapshot
        snapshot = MetricsSnapshot(
            timestamp=time.time(),
            version=self.version_info.version,
            frames_processed=self.frames_processed,
            motion_detected=self.motion_detected,
            motion_hit_rate=motion_hit_rate,
            events_created=self.events_created,
            events_suppressed=self.events_suppressed,
            coreml_inference_avg=coreml_avg,
            coreml_inference_min=coreml_min,
            coreml_inference_max=coreml_max,
            coreml_inference_p95=coreml_p95,
            llm_inference_avg=llm_avg,
            llm_inference_min=llm_min,
            llm_inference_max=llm_max,
            llm_inference_p95=llm_p95,
            frame_processing_latency_avg=latency_avg,
            frame_processing_latency_min=latency_min,
            frame_processing_latency_max=latency_max,
            frame_processing_latency_p95=latency_p95,
            cpu_usage_current=system_metrics["cpu_current"],
            cpu_usage_avg=system_metrics["cpu_avg"],
            memory_usage_mb=system_metrics["memory_mb"],
            memory_usage_gb=system_metrics["memory_gb"],
            memory_usage_percent=system_metrics["memory_percent"],
            system_uptime_percent=uptime_percent,
            system_start_time=self.system_start_time,
        )

        # Calculate collection overhead
        collection_end = time.time()
        collection_time = collection_end - collection_start
        overhead_percent = (collection_time / 0.1) * 100  # Assuming 0.1s CPU measurement interval
        snapshot.metrics_collection_overhead_percent = min(overhead_percent, 100.0)  # Cap at 100%

        # Log warning if overhead is too high
        if overhead_percent > 1.0:
            self.logger.warning(".2f")

        return snapshot

    def log_metrics(self, snapshot: Optional[MetricsSnapshot] = None) -> None:
        """Log metrics snapshot to file.

        Args:
            snapshot: Metrics snapshot to log, or None to collect current metrics
        """
        if snapshot is None:
            snapshot = self.collect()

        try:
            # Ensure directory exists
            self.metrics_log_path.parent.mkdir(parents=True, exist_ok=True)

            # Append to the metrics file (JSON Lines format)
            with open(self.metrics_log_path, "a", encoding="utf-8") as f:
                json_line = snapshot.model_dump_json()
                f.write(json_line + "\n")

        except Exception as e:
            self.logger.error(f"Failed to log metrics: {e}")

    def should_log_metrics(self) -> bool:
        """Check if metrics should be logged based on interval.

        Returns:
            True if enough time has passed since last log
        """
        current_time = time.time()
        if current_time - self.last_log_time >= self.config.metrics_interval:
            self.last_log_time = current_time
            return True
        return False

    def get_status_display(self) -> str:
        """Get formatted status display string for console output.

        Returns:
            Formatted string with key metrics
        """
        snapshot = self.collect()

        # Format uptime
        uptime_seconds = time.time() - self.system_start_time
        uptime_str = ""
        if uptime_seconds < 60:
            uptime_str = ".0f"
        elif uptime_seconds < 3600:
            uptime_str = ".0f"
        else:
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            uptime_str = f"{hours}h {minutes}m"

        lines = [
            "├─────────────────────────────────────────────────────────────────┤",
            f"│ Runtime Metrics - {time.strftime('%Y-%m-%d %H:%M:%S')} (uptime: {uptime_str})     │",
            "├─────────────────────────────────────────────────────────────────┤",
            "│ Processing:                                                      │",
            f"│   Frames processed:        {snapshot.frames_processed:,}                               │",
            f"│   Motion detected:         {snapshot.motion_detected:,} ({snapshot.motion_hit_rate:.1f}% hit rate)                 │",
            f"│   Events created:          {snapshot.events_created:,}                                  │",
            f"│   Events suppressed:       {snapshot.events_suppressed:,} (de-duplication)                  │",
            "│                                                                  │",
            "│ Performance:                                                     │",
            f"│   CoreML inference:        avg {snapshot.coreml_inference_avg:.0f}ms, p95 {snapshot.coreml_inference_p95:.0f}ms, max {snapshot.coreml_inference_max:.0f}ms │",
            f"│   LLM inference:           avg {snapshot.llm_inference_avg:.1f}s, p95 {snapshot.llm_inference_p95:.1f}s, max {snapshot.llm_inference_max:.1f}s │",
            f"│   End-to-end latency:      avg {snapshot.frame_processing_latency_avg:.1f}s, p95 {snapshot.frame_processing_latency_p95:.1f}s │",
            "│                                                                  │",
            "│ Resources:                                                       │",
            f"│   CPU usage:               avg {snapshot.cpu_usage_avg:.1f}%, current {snapshot.cpu_usage_current:.1f}%                 │",
            f"│   Memory usage:            {snapshot.memory_usage_gb:.1f}GB ({snapshot.memory_usage_percent:.1f}%)                    │",
            "│                                                                  │",
            "│ Availability:                                                    │",
            f"│   System uptime:           {snapshot.system_uptime_percent:.1f}%                               │",
            "│                                                                  │",
            "│ [✓] = Meeting NFR target  [⚠] = Approaching limit  [✗] = Failed │",
            "└─────────────────────────────────────────────────────────────────┘",
        ]

        return "\n".join(lines)

    def reset(self) -> None:
        """Reset all metrics (useful for testing)."""
        self.frames_processed = 0
        self.motion_detected = 0
        self.events_created = 0
        self.events_suppressed = 0
        self.coreml_times.clear()
        self.llm_times.clear()
        self.frame_latencies.clear()
        self.cpu_usage_history.clear()
        self.system_start_time = time.time()
        self.last_log_time = 0.0
