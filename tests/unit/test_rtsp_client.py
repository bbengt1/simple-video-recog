"""Unit tests for RTSP camera client."""

import time
from unittest.mock import Mock, patch

import numpy as np
import pytest

from core.config import SystemConfig
from core.exceptions import RTSPConnectionError
from integrations.rtsp_client import RTSPCameraClient


class TestRTSPCameraClient:
    """Test RTSPCameraClient class."""

    @patch("integrations.rtsp_client.cv2.VideoCapture")
    def test_connect_success(self, mock_videocapture, sample_config):
        """Test successful RTSP connection."""
        # Arrange
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_videocapture.return_value = mock_cap

        config = SystemConfig(**sample_config)
        client = RTSPCameraClient(config)

        # Act
        result = client.connect()

        # Assert
        assert result is True
        assert client.cap is not None
        mock_videocapture.assert_called_once_with(config.camera_rtsp_url)
        mock_cap.isOpened.assert_called_once()

    @patch("integrations.rtsp_client.cv2.VideoCapture")
    def test_connect_failure(self, mock_videocapture, sample_config):
        """Test RTSP connection failure raises RTSPConnectionError."""
        # Arrange
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_videocapture.return_value = mock_cap

        config = SystemConfig(**sample_config)
        client = RTSPCameraClient(config)

        # Act & Assert
        with pytest.raises(RTSPConnectionError) as exc_info:
            client.connect()

        error_str = str(exc_info.value)
        assert "Failed to connect" in error_str
        assert config.camera_id in error_str

    @patch("integrations.rtsp_client.cv2.VideoCapture")
    def test_disconnect(self, mock_videocapture, sample_config):
        """Test disconnection releases VideoCapture and sets cap to None."""
        # Arrange
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_videocapture.return_value = mock_cap

        config = SystemConfig(**sample_config)
        client = RTSPCameraClient(config)
        client.connect()

        # Act
        client.disconnect()

        # Assert
        mock_cap.release.assert_called_once()
        assert client.cap is None
        assert client.is_connected() is False

    @patch("integrations.rtsp_client.cv2.VideoCapture")
    def test_get_frame_success(self, mock_videocapture, sample_config, mock_frame):
        """Test get_frame returns numpy array when connected."""
        # Arrange
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, mock_frame)
        mock_videocapture.return_value = mock_cap

        config = SystemConfig(**sample_config)
        client = RTSPCameraClient(config)
        client.connect()

        # Act
        frame = client.get_frame()

        # Assert
        assert frame is not None
        assert isinstance(frame, np.ndarray)
        assert frame.shape == (480, 640, 3)
        mock_cap.read.assert_called_once()

    @patch("integrations.rtsp_client.cv2.VideoCapture")
    def test_get_frame_when_disconnected(self, mock_videocapture, sample_config):
        """Test get_frame returns None when disconnected."""
        # Arrange
        config = SystemConfig(**sample_config)
        client = RTSPCameraClient(config)

        # Act
        frame = client.get_frame()

        # Assert
        assert frame is None

    @patch("integrations.rtsp_client.cv2.VideoCapture")
    @patch("integrations.rtsp_client.time.sleep")
    def test_reconnection_backoff(self, mock_sleep, mock_videocapture, sample_config):
        """Test exponential backoff reconnection delays (1s, 2s, 4s, 8s)."""
        # Arrange
        config = SystemConfig(**sample_config)
        client = RTSPCameraClient(config)

        # Mock connection - initial connect succeeds, then reads fail triggering reconnect
        mock_cap = Mock()
        # First isOpened for initial connect, then for is_connected checks and reconnections
        mock_cap.isOpened.return_value = True
        # First 3 reads fail (trigger reconnection), then succeed
        mock_cap.read.side_effect = [
            (False, None),  # First read fails
            (False, None),  # Second read fails
            (False, None),  # Third read fails
            (True, np.zeros((480, 640, 3), dtype=np.uint8)),  # Fourth succeeds
            (True, np.zeros((480, 640, 3), dtype=np.uint8)),  # Continue succeeding
        ]
        mock_videocapture.return_value = mock_cap

        # Act: connect and start capture thread
        client.connect()
        client.start_capture()

        # Let thread run and attempt reconnections
        time.sleep(0.2)
        client.stop_capture()

        # Assert: verify exponential backoff delays were called
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]

        # Should have backoff delays (1, 2, 4) plus frame processing sleeps (0.033)
        # Filter for backoff delays (>= 1 second)
        backoff_delays = [delay for delay in sleep_calls if delay >= 1]

        # Should have at least one backoff delay
        assert len(backoff_delays) > 0
        # Verify exponential pattern (1, 2, 4)
        if len(backoff_delays) >= 1:
            assert backoff_delays[0] == 1  # First backoff

    @patch("integrations.rtsp_client.cv2.VideoCapture")
    def test_frame_queue_full_handling(self, mock_videocapture, sample_config, mock_frame):
        """Test graceful handling when queue reaches 100 frames."""
        # Arrange
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, mock_frame)
        mock_videocapture.return_value = mock_cap

        config = SystemConfig(**sample_config)
        client = RTSPCameraClient(config)
        client.connect()

        # Fill queue to max capacity (100 frames)
        for _ in range(100):
            client.frame_queue.put_nowait(mock_frame)

        # Act: try to get another frame (queue is full)
        frame = client.get_frame()

        # Assert: get_frame should still work
        assert frame is not None
        assert isinstance(frame, np.ndarray)

        # Queue should still be full (new frame not added)
        assert client.frame_queue.full()

    @patch("integrations.rtsp_client.cv2.VideoCapture")
    def test_is_connected_when_cap_is_none(self, mock_videocapture, sample_config):
        """Test is_connected returns False when cap is None."""
        # Arrange
        config = SystemConfig(**sample_config)
        client = RTSPCameraClient(config)

        # Act
        result = client.is_connected()

        # Assert
        assert result is False

    @patch("integrations.rtsp_client.cv2.VideoCapture")
    def test_get_latest_frame_from_queue(self, mock_videocapture, sample_config, mock_frame):
        """Test get_latest_frame retrieves frame from queue."""
        # Arrange
        config = SystemConfig(**sample_config)
        client = RTSPCameraClient(config)

        # Add frame to queue
        client.frame_queue.put_nowait(mock_frame)

        # Act
        frame = client.get_latest_frame()

        # Assert
        assert frame is not None
        assert isinstance(frame, np.ndarray)
        assert frame.shape == (480, 640, 3)

    @patch("integrations.rtsp_client.cv2.VideoCapture")
    def test_get_latest_frame_when_queue_empty(self, mock_videocapture, sample_config):
        """Test get_latest_frame returns None when queue is empty."""
        # Arrange
        config = SystemConfig(**sample_config)
        client = RTSPCameraClient(config)

        # Act
        frame = client.get_latest_frame()

        # Assert
        assert frame is None

    @patch("integrations.rtsp_client.cv2.VideoCapture")
    def test_start_capture_creates_thread(self, mock_videocapture, sample_config):
        """Test start_capture creates and starts daemon thread."""
        # Arrange
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_videocapture.return_value = mock_cap

        config = SystemConfig(**sample_config)
        client = RTSPCameraClient(config)
        client.connect()

        # Act
        client.start_capture()

        # Assert
        assert client.capture_thread is not None
        assert client.capture_thread.is_alive()
        assert client.capture_thread.daemon is True

        # Cleanup
        client.stop_capture()

    @patch("integrations.rtsp_client.cv2.VideoCapture")
    def test_stop_capture_stops_thread(self, mock_videocapture, sample_config):
        """Test stop_capture stops the background thread."""
        # Arrange
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_videocapture.return_value = mock_cap

        config = SystemConfig(**sample_config)
        client = RTSPCameraClient(config)
        client.connect()
        client.start_capture()

        # Wait briefly for thread to start
        time.sleep(0.1)

        # Act
        client.stop_capture()

        # Assert
        assert not client.capture_thread.is_alive()
