"""Unit tests for metrics collection functionality."""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.config import SystemConfig
from core.metrics import MetricsCollector, MetricsSnapshot


@pytest.fixture
def sample_config():
    """Create a sample system configuration for testing."""
    return SystemConfig(
        camera_rtsp_url="rtsp://test:123@192.168.1.100:554/stream",
        motion_threshold=0.5,
        frame_sample_rate=10,
        metrics_interval=60,
    )


@pytest.fixture
def metrics_collector(sample_config):
    """Create a metrics collector instance for testing."""
    collector = MetricsCollector(sample_config)
    collector.reset()  # Start with clean state
    return collector


class TestMetricsSnapshot:
    """Test the MetricsSnapshot data model."""

    def test_default_values(self):
        """Test that MetricsSnapshot has correct default values."""
        snapshot = MetricsSnapshot(timestamp=1234567890.0, version="1.0.0")

        assert snapshot.timestamp == 1234567890.0
        assert snapshot.frames_processed == 0
        assert snapshot.motion_detected == 0
        assert snapshot.motion_hit_rate == 0.0
        assert snapshot.events_created == 0
        assert snapshot.events_suppressed == 0
        assert snapshot.coreml_inference_avg == 0.0
        assert snapshot.cpu_usage_current == 0.0
        assert snapshot.system_uptime_percent == 100.0

    def test_json_serialization(self):
        """Test that MetricsSnapshot can be serialized to JSON."""
        snapshot = MetricsSnapshot(
            timestamp=1234567890.0,
            version="1.0.0",
            frames_processed=100,
            motion_detected=20,
            events_created=5,
        )

        json_str = snapshot.model_dump_json()
        data = json.loads(json_str)

        assert data["timestamp"] == 1234567890.0
        assert data["frames_processed"] == 100
        assert data["motion_detected"] == 20
        assert data["events_created"] == 5


class TestMetricsCollector:
    """Test the MetricsCollector class."""

    def test_initialization(self, sample_config):
        """Test that MetricsCollector initializes correctly."""
        collector = MetricsCollector(sample_config)

        assert collector.config == sample_config
        assert collector.frames_processed == 0
        assert collector.motion_detected == 0
        assert collector.events_created == 0
        assert collector.events_suppressed == 0
        assert len(collector.coreml_times) == 0
        assert len(collector.llm_times) == 0
        assert len(collector.frame_latencies) == 0

    def test_increment_counter(self, metrics_collector):
        """Test counter increment functionality."""
        # Test valid counters
        metrics_collector.increment_counter("frames_processed")
        metrics_collector.increment_counter("motion_detected")
        metrics_collector.increment_counter("events_created")
        metrics_collector.increment_counter("events_suppressed")

        assert metrics_collector.frames_processed == 1
        assert metrics_collector.motion_detected == 1
        assert metrics_collector.events_created == 1
        assert metrics_collector.events_suppressed == 1

        # Test unknown counter (should not crash)
        metrics_collector.increment_counter("unknown_counter")
        assert metrics_collector.frames_processed == 1  # Unchanged

    def test_record_inference_time(self, metrics_collector):
        """Test inference time recording."""
        # Record CoreML times
        metrics_collector.record_inference_time("coreml", 50.0)
        metrics_collector.record_inference_time("coreml", 60.0)
        metrics_collector.record_inference_time("coreml", 70.0)

        # Record LLM times
        metrics_collector.record_inference_time("llm", 1000.0)
        metrics_collector.record_inference_time("llm", 1200.0)

        assert len(metrics_collector.coreml_times) == 3
        assert len(metrics_collector.llm_times) == 2
        assert list(metrics_collector.coreml_times) == [50.0, 60.0, 70.0]
        assert list(metrics_collector.llm_times) == [1000.0, 1200.0]

        # Test unknown component (should not crash)
        metrics_collector.record_inference_time("unknown", 100.0)
        assert len(metrics_collector.coreml_times) == 3  # Unchanged

    def test_record_frame_latency(self, metrics_collector):
        """Test frame latency recording."""
        metrics_collector.record_frame_latency(500.0)
        metrics_collector.record_frame_latency(600.0)

        assert len(metrics_collector.frame_latencies) == 2
        assert list(metrics_collector.frame_latencies) == [500.0, 600.0]

    def test_calculate_percentiles_empty_data(self, metrics_collector):
        """Test percentile calculation with empty data."""
        result = metrics_collector._calculate_percentiles(metrics_collector.coreml_times)
        assert result == (0.0, 0.0, 0.0, 0.0)

    def test_calculate_percentiles_with_data(self, metrics_collector):
        """Test percentile calculation with data."""
        # Add test data
        test_data = [10.0, 20.0, 30.0, 40.0, 50.0]
        for value in test_data:
            metrics_collector.coreml_times.append(value)

        min_val, max_val, avg_val, p95_val = metrics_collector._calculate_percentiles(metrics_collector.coreml_times)

        assert min_val == 10.0
        assert max_val == 50.0
        assert avg_val == 30.0
        assert p95_val == 48.0  # 95th percentile of [10,20,30,40,50]

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_get_system_metrics(self, mock_memory, mock_cpu, metrics_collector):
        """Test system metrics collection."""
        # Mock psutil calls
        mock_cpu.return_value = 45.5
        mock_memory.return_value = MagicMock()
        mock_memory.return_value.used = 1024 * 1024 * 1024  # 1GB in bytes
        mock_memory.return_value.percent = 25.0

        metrics = metrics_collector._get_system_metrics()

        assert metrics["cpu_current"] == 45.5
        assert metrics["cpu_avg"] == 45.5  # First measurement
        assert metrics["memory_mb"] == 1024.0  # 1GB = 1024MB
        assert metrics["memory_gb"] == 1.0
        assert metrics["memory_percent"] == 25.0

    def test_calculate_uptime_percent(self, metrics_collector):
        """Test uptime percentage calculation."""
        # Should return 100% for a newly started system
        uptime = metrics_collector._calculate_uptime_percent()
        assert uptime == 100.0

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_collect_full_snapshot(self, mock_memory, mock_cpu, metrics_collector):
        """Test collecting a full metrics snapshot."""
        # Setup test data
        metrics_collector.frames_processed = 100
        metrics_collector.motion_detected = 20
        metrics_collector.events_created = 5
        metrics_collector.events_suppressed = 2

        # Add timing data
        for i in range(10):
            metrics_collector.record_inference_time("coreml", 50.0 + i)
            metrics_collector.record_inference_time("llm", 1000.0 + i * 10)
            metrics_collector.record_frame_latency(500.0 + i * 20)

        # Mock system calls
        mock_cpu.return_value = 30.0
        mock_memory.return_value = MagicMock()
        mock_memory.return_value.used = 512 * 1024 * 1024  # 512MB
        mock_memory.return_value.percent = 12.5

        snapshot = metrics_collector.collect()

        # Verify snapshot structure
        assert isinstance(snapshot, MetricsSnapshot)
        assert snapshot.frames_processed == 100
        assert snapshot.motion_detected == 20
        assert snapshot.motion_hit_rate == 20.0  # 20/100 * 100
        assert snapshot.events_created == 5
        assert snapshot.events_suppressed == 2

        # Verify timing calculations
        assert snapshot.coreml_inference_avg > 0
        assert snapshot.llm_inference_avg > 0
        assert snapshot.frame_processing_latency_avg > 0

        # Verify system metrics
        assert snapshot.cpu_usage_current == 30.0
        assert snapshot.memory_usage_mb == 512.0
        assert snapshot.memory_usage_gb == 0.5
        assert snapshot.memory_usage_percent == 12.5

    def test_log_metrics(self, metrics_collector, tmp_path):
        """Test metrics logging to file."""
        # Override the log path for testing
        metrics_collector.metrics_log_path = tmp_path / "test_metrics.json"

        # Create a test snapshot
        snapshot = MetricsSnapshot(timestamp=1234567890.0, version="1.0.0", frames_processed=42)

        # Log metrics
        metrics_collector.log_metrics(snapshot)

        # Verify file was created and contains correct data
        assert metrics_collector.metrics_log_path.exists()

        with open(metrics_collector.metrics_log_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1
            data = json.loads(lines[0])
            assert data["frames_processed"] == 42
            assert data["timestamp"] == 1234567890.0

    def test_should_log_metrics(self, metrics_collector):
        """Test periodic logging logic."""
        # Initially should log
        assert metrics_collector.should_log_metrics() is True

        # Immediately after should not log
        assert metrics_collector.should_log_metrics() is False

        # After interval should log again
        metrics_collector.last_log_time = time.time() - 70  # 70 seconds ago
        assert metrics_collector.should_log_metrics() is True

    def test_get_status_display(self, metrics_collector):
        """Test status display formatting."""
        # Setup some test data
        metrics_collector.frames_processed = 1000
        metrics_collector.motion_detected = 150
        metrics_collector.events_created = 25

        display = metrics_collector.get_status_display()

        # Verify display contains expected elements
        assert "Runtime Metrics" in display
        assert "Frames processed:        1,000" in display
        assert "Motion detected:         150" in display
        assert "Events created:          25" in display
        assert "[✓] = Meeting NFR target" in display

    def test_reset(self, metrics_collector):
        """Test metrics reset functionality."""
        # Setup some data
        metrics_collector.frames_processed = 100
        metrics_collector.record_inference_time("coreml", 50.0)
        metrics_collector.record_inference_time("llm", 1000.0)

        # Reset
        metrics_collector.reset()

        # Verify everything is reset
        assert metrics_collector.frames_processed == 0
        assert metrics_collector.motion_detected == 0
        assert metrics_collector.events_created == 0
        assert metrics_collector.events_suppressed == 0
        assert len(metrics_collector.coreml_times) == 0
        assert len(metrics_collector.llm_times) == 0
        assert len(metrics_collector.frame_latencies) == 0
        assert len(metrics_collector.cpu_usage_history) == 0

    def test_rolling_window_limit(self, metrics_collector):
        """Test that rolling windows respect the maximum size."""
        # Add more than the rolling window size
        for i in range(1100):  # More than 1000
            metrics_collector.record_inference_time("coreml", float(i))

        # Should only keep the last 1000
        assert len(metrics_collector.coreml_times) == 1000
        assert list(metrics_collector.coreml_times)[0] == 100.0  # First should be 100 (after 100 additions)
        assert list(metrics_collector.coreml_times)[-1] == 1099.0  # Last should be most recent