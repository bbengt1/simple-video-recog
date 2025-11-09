"""Shared pytest fixtures for all tests."""

from unittest.mock import Mock

import numpy as np
import pytest


@pytest.fixture
def sample_config():
    """Valid configuration dictionary for testing."""
    return {
        "camera_rtsp_url": "rtsp://admin:password@192.168.1.100:554/stream1",
        "camera_id": "test_camera",
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
        "metrics_interval": 60,
    }


@pytest.fixture
def temp_config_file(tmp_path, sample_config):
    """Create temporary config file for testing."""
    import yaml

    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(sample_config, f)
    return config_file


@pytest.fixture
def mock_frame():
    """Create mock OpenCV frame (numpy array)."""
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def mock_video_capture():
    """Create mock cv2.VideoCapture for testing RTSP client."""
    mock_cap = Mock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
    mock_cap.release.return_value = None
    return mock_cap


@pytest.fixture
def mock_rtsp_camera(sample_config, mock_video_capture):
    """Create mock RTSPCameraClient for testing."""
    from unittest.mock import patch
    from integrations.rtsp_client import RTSPCameraClient

    with patch('cv2.VideoCapture', return_value=mock_video_capture):
        camera = RTSPCameraClient(sample_config)
        return camera
