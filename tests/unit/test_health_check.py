"""Unit tests for health check and status reporting functionality.

Tests cover health check logic, status display formatting, and error handling.
"""

import pytest
import logging
from unittest.mock import Mock, MagicMock, patch

from core.config import SystemConfig
from core.health_check import HealthChecker, StatusReporter
from core.motion_detector import MotionDetector
from integrations.rtsp_client import RTSPCameraClient


class TestHealthChecker:
    """Test the HealthChecker class."""

    @pytest.fixture(autouse=True)
    def setup_logging(self):
        """Set up logging for tests."""
        # Configure logging to capture all messages
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    @pytest.fixture
    def sample_config(self):
        """Create a sample system configuration."""
        return SystemConfig(
            camera_rtsp_url="rtsp://test:pass@192.168.1.100:554/stream1",
            camera_id="test_camera"
        )

    @pytest.fixture
    def mock_rtsp_client(self):
        """Create a mock RTSP client."""
        client = Mock(spec=RTSPCameraClient)
        client.is_connected.return_value = True
        # Mock frame queue
        mock_queue = Mock()
        mock_queue.qsize.return_value = 0
        mock_queue.maxsize = 100
        client.frame_queue = mock_queue
        return client

    @pytest.fixture
    def mock_motion_detector(self):
        """Create a mock motion detector."""
        detector = Mock(spec=MotionDetector)
        detector.bg_subtractor = Mock()  # Simulate initialized detector
        return detector

    @pytest.fixture
    def health_checker(self, sample_config, mock_rtsp_client, mock_motion_detector):
        """Create a HealthChecker instance for testing."""
        return HealthChecker(sample_config, mock_rtsp_client, mock_motion_detector)

    @patch('core.health_check.logger')
    def test_all_checks_pass(self, mock_logger, health_checker, mock_rtsp_client, mock_motion_detector):
        """Test health check when all checks pass."""
        # Configure mocks to succeed
        mock_rtsp_client.is_connected.return_value = True
        mock_motion_detector.bg_subtractor = Mock()

        # Run checks
        result = health_checker.run_checks()

        assert result is True

        # Verify log messages were called
        mock_logger.info.assert_any_call("===== System Health Check =====")
        mock_logger.info.assert_any_call("✓ Configuration loaded: test_camera")
        mock_logger.info.assert_any_call("✓ RTSP stream: Connected (test_camera)")
        mock_logger.info.assert_any_call("✓ Motion detector: Initialized")
        mock_logger.info.assert_any_call("✓ Frame queue: Ready (0/100)")
        mock_logger.info.assert_any_call("===== System Ready =====")

    @patch('core.health_check.logger')
    def test_rtsp_check_fails(self, mock_logger, health_checker, mock_rtsp_client):
        """Test health check when RTSP connection fails."""
        # Configure RTSP to fail
        mock_rtsp_client.is_connected.return_value = False

        # Run checks
        result = health_checker.run_checks()

        assert result is False

        # Verify log messages
        mock_logger.info.assert_any_call("===== System Health Check =====")
        mock_logger.info.assert_any_call("✓ Configuration loaded: test_camera")
        mock_logger.info.assert_any_call("✗ RTSP stream: Not connected (test_camera)")
        mock_logger.error.assert_any_call("===== System NOT Ready =====")

    @patch('core.health_check.logger')
    def test_motion_detector_check_fails(self, mock_logger, health_checker, mock_motion_detector):
        """Test health check when motion detector is not initialized."""
        # Configure motion detector to fail
        mock_motion_detector.bg_subtractor = None

        # Run checks
        result = health_checker.run_checks()

        assert result is False

        # Verify log messages
        mock_logger.info.assert_any_call("===== System Health Check =====")
        mock_logger.info.assert_any_call("✓ Configuration loaded: test_camera")
        mock_logger.info.assert_any_call("✗ Motion detector: Not initialized")
        mock_logger.error.assert_any_call("===== System NOT Ready =====")

    def test_config_check_fails_missing_url(self, mock_rtsp_client, mock_motion_detector):
        """Test health check when configuration is missing required camera_rtsp_url."""
        # Create config with empty URL (simulating missing/invalid config)
        config = SystemConfig(
            camera_rtsp_url="",  # Empty URL should fail validation
            camera_id="test_camera"
        )

        health_checker = HealthChecker(config, mock_rtsp_client, mock_motion_detector)
        result = health_checker.run_checks()

        assert result is False

    @patch('core.health_check.logger')
    def test_multiple_checks_fail(self, mock_logger, health_checker, mock_rtsp_client, mock_motion_detector):
        """Test health check when multiple checks fail."""
        # Configure multiple failures
        mock_rtsp_client.is_connected.return_value = False
        mock_motion_detector.bg_subtractor = None

        # Run checks
        result = health_checker.run_checks()

        assert result is False

        # Verify both failures are logged
        mock_logger.info.assert_any_call("✗ RTSP stream: Not connected (test_camera)")
        mock_logger.info.assert_any_call("✗ Motion detector: Not initialized")
        mock_logger.error.assert_any_call("===== System NOT Ready =====")


class TestStatusReporter:
    """Test the StatusReporter class."""

    @pytest.fixture
    def sample_config(self):
        """Create a sample system configuration."""
        return SystemConfig(
            camera_rtsp_url="rtsp://test:pass@192.168.1.100:554/stream1",
            camera_id="test_camera",
            metrics_interval=60
        )

    @pytest.fixture
    def status_reporter(self, sample_config):
        """Create a StatusReporter instance for testing."""
        return StatusReporter(sample_config)

    @patch('core.health_check.logger')
    def test_display_status_full_metrics(self, mock_logger, status_reporter):
        """Test status display with complete metrics."""
        metrics = {
            'frames_captured': 1847,
            'motion_detected': 127,
            'frames_sampled': 13,
            'queue_size': 3,
            'queue_max': 100,
            'elapsed_time': 60.0,
            'frame_sample_rate': 10
        }

        status_reporter.display_status(metrics)

        # Verify log message was called with expected content
        mock_logger.info.assert_called_once()
        status_message = mock_logger.info.call_args[0][0]

        assert "[INFO] Runtime Status (60s interval)" in status_message
        assert "Frames Captured: 1,847 (30.8 fps)" in status_message
        assert "Motion Detected: 127 (6.9% hit rate)" in status_message
        assert "Frames Sampled: 13 (sampling rate: 1/10)" in status_message
        assert "Queue Size: 3/100" in status_message

    @patch('core.health_check.logger')
    def test_display_status_zero_values(self, mock_logger, status_reporter):
        """Test status display with zero values."""
        metrics = {
            'frames_captured': 0,
            'motion_detected': 0,
            'frames_sampled': 0,
            'queue_size': 0,
            'queue_max': 100,
            'elapsed_time': 1.0,
            'frame_sample_rate': 1
        }

        status_reporter.display_status(metrics)

        status_message = mock_logger.info.call_args[0][0]

        assert "Frames Captured: 0 (0.0 fps)" in status_message
        assert "Motion Detected: 0 (0.0% hit rate)" in status_message

    @patch('core.health_check.logger')
    def test_display_status_missing_metrics(self, mock_logger, status_reporter):
        """Test status display with missing metrics (uses defaults)."""
        metrics = {}  # Empty metrics

        status_reporter.display_status(metrics)

        status_message = mock_logger.info.call_args[0][0]

        assert "Frames Captured: 0 (0.0 fps)" in status_message
        assert "Motion Detected: 0 (0.0% hit rate)" in status_message
        assert "Frames Sampled: 0 (sampling rate: 1/1)" in status_message
        assert "Queue Size: 0/100" in status_message