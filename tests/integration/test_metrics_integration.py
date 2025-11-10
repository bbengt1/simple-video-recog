"""Integration tests for metrics collection and logging."""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.config import SystemConfig
from core.metrics import MetricsCollector


@pytest.fixture
def metrics_config():
    """Create a test configuration for metrics integration testing."""
    return SystemConfig(
        camera_rtsp_url="rtsp://test:123@192.168.1.100:554/stream",
        motion_threshold=0.5,
        frame_sample_rate=10,
        metrics_interval=10,  # Minimum allowed interval for testing
    )


@pytest.fixture
def metrics_collector(metrics_config, tmp_path):
    """Create a metrics collector with temporary log path."""
    collector = MetricsCollector(metrics_config)
    # Override log path for testing
    collector.metrics_log_path = tmp_path / "metrics.json"
    return collector


class TestMetricsIntegration:
    """Integration tests for metrics collection."""

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_metrics_collection_over_time(self, mock_memory, mock_cpu, metrics_collector):
        """Test that metrics are collected correctly over a period of time."""
        # Mock system calls
        mock_cpu.return_value = 25.0
        mock_memory.return_value = MagicMock()
        mock_memory.return_value.used = 1024 * 1024 * 1024  # 1GB
        mock_memory.return_value.percent = 20.0

        # Simulate processing activity
        start_time = time.time()

        # Record some processing activity
        for i in range(100):
            metrics_collector.increment_counter("frames_processed")
            if i % 4 == 0:  # 25% motion detection rate
                metrics_collector.increment_counter("motion_detected")
            if i % 20 == 0:  # 5 events
                metrics_collector.increment_counter("events_created")
                # Record some inference times
                metrics_collector.record_inference_time("coreml", 80.0 + (i % 20))
                metrics_collector.record_inference_time("llm", 1500.0 + (i % 100))
                metrics_collector.record_frame_latency(2000.0 + (i % 200))

        # Collect metrics
        snapshot = metrics_collector.collect()

        # Verify metrics were collected correctly
        assert snapshot.frames_processed == 100
        assert snapshot.motion_detected == 25  # Every 4th frame
        assert snapshot.motion_hit_rate == 25.0  # 25/100 * 100
        assert snapshot.events_created == 5

        # Verify timing metrics
        assert snapshot.coreml_inference_avg > 0
        assert snapshot.llm_inference_avg > 0
        assert snapshot.frame_processing_latency_avg > 0

        # Verify system metrics
        assert snapshot.cpu_usage_current == 25.0
        assert snapshot.memory_usage_gb == 1.0
        assert snapshot.memory_usage_percent == 20.0

        # Verify uptime
        assert snapshot.system_uptime_percent == 100.0
        assert snapshot.system_start_time > 0

        # Verify collection took reasonable time
        collection_time = time.time() - start_time
        assert collection_time < 1.0  # Should be fast

    def test_metrics_logging_integration(self, metrics_collector):
        """Test that metrics are logged to file correctly."""
        # Collect and log some metrics
        snapshot1 = metrics_collector.collect()
        metrics_collector.log_metrics(snapshot1)

        # Wait a bit and log another snapshot
        time.sleep(0.1)
        snapshot2 = metrics_collector.collect()
        metrics_collector.log_metrics(snapshot2)

        # Verify log file exists and contains correct data
        assert metrics_collector.metrics_log_path.exists()

        with open(metrics_collector.metrics_log_path, 'r') as f:
            lines = f.readlines()

        assert len(lines) == 2  # Two log entries

        # Parse and verify first entry
        data1 = json.loads(lines[0])
        assert "timestamp" in data1
        assert "frames_processed" in data1
        assert data1["frames_processed"] == snapshot1.frames_processed

        # Parse and verify second entry
        data2 = json.loads(lines[1])
        assert "timestamp" in data2
        assert data2["timestamp"] > data1["timestamp"]  # Time should increase

    def test_periodic_logging_logic(self, metrics_collector):
        """Test the periodic logging timing logic."""
        # Initially should log
        assert metrics_collector.should_log_metrics() is True

        # Immediately after should not log (interval is 10 seconds)
        assert metrics_collector.should_log_metrics() is False

        # Simulate time passing (more than 10 seconds)
        metrics_collector.last_log_time = time.time() - 11

        # Should log again
        assert metrics_collector.should_log_metrics() is True

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_status_display_formatting(self, mock_memory, mock_cpu, metrics_collector):
        """Test that status display is properly formatted."""
        # Setup some test data
        metrics_collector.frames_processed = 1500
        metrics_collector.motion_detected = 225
        metrics_collector.events_created = 45
        metrics_collector.events_suppressed = 10

        # Add some timing data
        for i in range(20):
            metrics_collector.record_inference_time("coreml", 85.0 + i)
            metrics_collector.record_inference_time("llm", 1400.0 + i * 10)
            metrics_collector.record_frame_latency(1800.0 + i * 20)

        # Mock system metrics
        mock_cpu.return_value = 35.0
        mock_memory.return_value = MagicMock()
        mock_memory.return_value.used = 1.5 * 1024 * 1024 * 1024  # 1.5GB
        mock_memory.return_value.percent = 18.75

        display = metrics_collector.get_status_display()

        # Verify display contains expected elements
        assert "Runtime Metrics" in display
        assert "Frames processed:        1,500" in display
        assert "Motion detected:         225" in display
        assert "Events created:          45" in display
        assert "Events suppressed:       10" in display
        assert "CoreML inference:" in display
        assert "LLM inference:" in display
        assert "End-to-end latency:" in display
        assert "CPU usage:" in display
        assert "Memory usage:" in display
        assert "[✓] = Meeting NFR target" in display

        # Verify it's properly formatted as a box
        lines = display.split('\n')
        assert len(lines) > 10
        assert any("├" in line or "└" in line for line in lines)  # Contains box drawing characters

    def test_metrics_file_rotation_simulation(self, metrics_collector, tmp_path):
        """Test that metrics logging handles file operations correctly."""
        # Override with a different path for this test
        test_log_path = tmp_path / "test_metrics_rotation.json"
        metrics_collector.metrics_log_path = test_log_path

        # Log multiple entries
        for i in range(10):
            snapshot = metrics_collector.collect()
            snapshot.frames_processed = i * 10  # Vary the data
            metrics_collector.log_metrics(snapshot)
            time.sleep(0.01)  # Small delay

        # Verify all entries are in the file
        assert test_log_path.exists()

        with open(test_log_path, 'r') as f:
            lines = f.readlines()

        assert len(lines) == 10

        # Verify entries are in order and contain varying data
        for i, line in enumerate(lines):
            data = json.loads(line)
            assert data["frames_processed"] == i * 10

    @patch('time.time')
    def test_uptime_calculation_edge_cases(self, mock_time, metrics_collector):
        """Test uptime calculation in various scenarios."""
        # Test with time passage
        mock_time.return_value = 1000000060.0  # 60 seconds later
        metrics_collector.system_start_time = 1000000000.0

        uptime = metrics_collector._calculate_uptime_percent()
        assert uptime == 100.0  # Any positive runtime = 100% uptime

        # Test with time passage
        mock_time.return_value = 1000000060.0  # 60 seconds later
        uptime = metrics_collector._calculate_uptime_percent()
        assert uptime == 100.0  # Still 100% for simplicity

    def test_metrics_reset_integration(self, metrics_collector):
        """Test that reset works correctly in integration scenarios."""
        # Build up some state
        for i in range(50):
            metrics_collector.increment_counter("frames_processed")
            metrics_collector.record_inference_time("coreml", 100.0)
            metrics_collector.record_inference_time("llm", 2000.0)

        # Verify state exists
        assert metrics_collector.frames_processed == 50
        assert len(metrics_collector.coreml_times) == 50
        assert len(metrics_collector.llm_times) == 50

        # Reset
        metrics_collector.reset()

        # Verify clean state
        assert metrics_collector.frames_processed == 0
        assert len(metrics_collector.coreml_times) == 0
        assert len(metrics_collector.llm_times) == 0
        assert len(metrics_collector.cpu_usage_history) == 0

        # Verify reset doesn't break subsequent operations
        metrics_collector.increment_counter("frames_processed")
        assert metrics_collector.frames_processed == 1