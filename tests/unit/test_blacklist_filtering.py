"""Unit tests for blacklist filtering functionality."""

import pytest
from unittest.mock import patch

from core.config import SystemConfig
from core.models import BoundingBox, DetectedObject
from apple_platform.coreml_detector import CoreMLDetector


@pytest.fixture
def sample_config():
    """Sample system configuration for testing."""
    return SystemConfig(
        camera_rtsp_url="rtsp://test:123@192.168.1.100:554/stream1",
        coreml_model_path="models/test.mlmodel",
        min_object_confidence=0.5,
        blacklist_objects=["cat", "bird"]
    )


@pytest.fixture
def empty_blacklist_config():
    """Configuration with empty blacklist."""
    return SystemConfig(
        camera_rtsp_url="rtsp://test:123@192.168.1.100:554/stream1",
        coreml_model_path="models/test.mlmodel",
        min_object_confidence=0.5,
        blacklist_objects=[]
    )


@pytest.fixture
def sample_detections():
    """Sample detected objects for testing."""
    return [
        DetectedObject(label="person", confidence=0.9, bbox=BoundingBox(x=100, y=50, width=80, height=160)),
        DetectedObject(label="cat", confidence=0.8, bbox=BoundingBox(x=200, y=100, width=60, height=40)),
        DetectedObject(label="dog", confidence=0.7, bbox=BoundingBox(x=300, y=150, width=70, height=50)),
        DetectedObject(label="bird", confidence=0.6, bbox=BoundingBox(x=400, y=200, width=40, height=30)),
        DetectedObject(label="car", confidence=0.85, bbox=BoundingBox(x=50, y=75, width=120, height=80))
    ]


class TestBlacklistFiltering:
    """Test cases for blacklist filtering functionality."""

    def test_filter_blacklisted_objects_with_blacklist(self, sample_config, sample_detections):
        """Test filtering with active blacklist."""
        detector = CoreMLDetector(sample_config)
        detector.is_loaded = True

        result = detector._filter_blacklisted_objects(sample_detections)

        # Should filter out "cat" and "bird", keep "person", "dog", "car"
        assert len(result) == 3
        labels = [det.label for det in result]
        assert "person" in labels
        assert "dog" in labels
        assert "car" in labels
        assert "cat" not in labels
        assert "bird" not in labels

    def test_filter_blacklisted_objects_empty_blacklist(self, empty_blacklist_config, sample_detections):
        """Test filtering with empty blacklist (no filtering)."""
        detector = CoreMLDetector(empty_blacklist_config)
        detector.is_loaded = True

        result = detector._filter_blacklisted_objects(sample_detections)

        # Should return all detections unchanged
        assert len(result) == len(sample_detections)
        assert result == sample_detections

    def test_filter_blacklisted_objects_case_insensitive(self, sample_config):
        """Test case-insensitive filtering."""
        detector = CoreMLDetector(sample_config)
        detector.is_loaded = True

        # Test with mixed case detections
        detections = [
            DetectedObject(label="PERSON", confidence=0.9, bbox=BoundingBox(x=100, y=50, width=80, height=160)),
            DetectedObject(label="Cat", confidence=0.8, bbox=BoundingBox(x=200, y=100, width=60, height=40)),
            DetectedObject(label="BIRD", confidence=0.7, bbox=BoundingBox(x=300, y=150, width=70, height=50))
        ]

        result = detector._filter_blacklisted_objects(detections)

        # Should filter out "Cat" and "BIRD" (case-insensitive), keep "PERSON"
        assert len(result) == 1
        assert result[0].label == "PERSON"

    def test_filter_blacklisted_objects_word_boundaries(self, sample_config):
        """Test word boundary matching (not substring matching)."""
        detector = CoreMLDetector(sample_config)
        detector.is_loaded = True

        # Create detections that might cause false positives
        detections = [
            DetectedObject(label="cattle", confidence=0.8, bbox=BoundingBox(x=100, y=50, width=80, height=160)),  # Should NOT match "cat"
            DetectedObject(label="scattered", confidence=0.7, bbox=BoundingBox(x=200, y=100, width=60, height=40)),  # Should NOT match "cat"
            DetectedObject(label="bird", confidence=0.6, bbox=BoundingBox(x=300, y=150, width=70, height=50)),  # Should match "bird"
            DetectedObject(label="birdcage", confidence=0.5, bbox=BoundingBox(x=400, y=200, width=40, height=30))  # Should NOT match "bird"
        ]

        result = detector._filter_blacklisted_objects(detections)

        # Should only filter out exact "bird", keep "cattle", "scattered", "birdcage"
        assert len(result) == 3
        labels = [det.label for det in result]
        assert "cattle" in labels
        assert "scattered" in labels
        assert "birdcage" in labels
        assert "bird" not in labels

    def test_filter_blacklisted_objects_all_filtered(self, sample_config):
        """Test when all detections are blacklisted."""
        detector = CoreMLDetector(sample_config)
        detector.is_loaded = True

        # All detections are blacklisted
        detections = [
            DetectedObject(label="cat", confidence=0.8, bbox=BoundingBox(x=100, y=50, width=80, height=160)),
            DetectedObject(label="bird", confidence=0.7, bbox=BoundingBox(x=200, y=100, width=60, height=40))
        ]

        result = detector._filter_blacklisted_objects(detections)

        # Should return empty list
        assert len(result) == 0
        assert result == []

    def test_filter_blacklisted_objects_no_detections(self, sample_config):
        """Test filtering with empty detection list."""
        detector = CoreMLDetector(sample_config)
        detector.is_loaded = True

        result = detector._filter_blacklisted_objects([])

        # Should return empty list
        assert len(result) == 0
        assert result == []

    def test_filter_blacklisted_objects_logging(self, sample_config, sample_detections):
        """Test that filtering logs blacklisted objects."""
        detector = CoreMLDetector(sample_config)
        detector.is_loaded = True

        with patch.object(detector, 'logger') as mock_logger:
            detector._filter_blacklisted_objects(sample_detections)

            # Should log the filtered objects (order may vary)
            mock_logger.debug.assert_called_once()
            log_call = mock_logger.debug.call_args[0][0]
            assert "Filtered 2 blacklisted objects:" in log_call
            assert "cat" in log_call
            assert "bird" in log_call

    def test_filter_blacklisted_objects_no_logging_when_none_filtered(self, sample_config):
        """Test that no logging occurs when no objects are filtered."""
        detector = CoreMLDetector(sample_config)
        detector.is_loaded = True

        # Detections that are not blacklisted
        detections = [
            DetectedObject(label="person", confidence=0.9, bbox=BoundingBox(x=100, y=50, width=80, height=160)),
            DetectedObject(label="car", confidence=0.8, bbox=BoundingBox(x=200, y=100, width=60, height=40))
        ]

        with patch.object(detector, 'logger') as mock_logger:
            detector._filter_blacklisted_objects(detections)

            # Should not log anything
            mock_logger.debug.assert_not_called()

    def test_filter_blacklisted_objects_mixed_case_blacklist(self):
        """Test filtering with mixed case blacklist entries."""
        config = SystemConfig(
            camera_rtsp_url="rtsp://test:123@192.168.1.100:554/stream1",
            coreml_model_path="models/test.mlmodel",
            blacklist_objects=["Cat", "BIRD"]
        )
        detector = CoreMLDetector(config)
        detector.is_loaded = True

        detections = [
            DetectedObject(label="cat", confidence=0.8, bbox=BoundingBox(x=100, y=50, width=80, height=160)),
            DetectedObject(label="bird", confidence=0.7, bbox=BoundingBox(x=200, y=100, width=60, height=40)),
            DetectedObject(label="person", confidence=0.9, bbox=BoundingBox(x=300, y=150, width=70, height=50))
        ]

        result = detector._filter_blacklisted_objects(detections)

        # Should filter out "cat" and "bird" (case-insensitive), keep "person"
        assert len(result) == 1
        assert result[0].label == "person"