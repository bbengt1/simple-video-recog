"""Integration tests for blacklist filtering in the detection pipeline."""

import pytest
from unittest.mock import patch, MagicMock

from core.config import SystemConfig
from core.models import BoundingBox, DetectedObject
from apple_platform.coreml_detector import CoreMLDetector


@pytest.fixture
def integration_config():
    """Configuration for integration testing."""
    return SystemConfig(
        camera_rtsp_url="rtsp://test:123@192.168.1.100:554/stream1",
        coreml_model_path="models/test.mlmodel",
        min_object_confidence=0.5,
        blacklist_objects=["cat", "bird"]
    )


class TestBlacklistIntegration:
    """Integration tests for blacklist filtering in the detection pipeline."""

    def test_blacklist_filtering_called_in_pipeline(self, integration_config):
        """Test that blacklist filtering is called in the detection pipeline."""
        detector = CoreMLDetector(integration_config)
        detector.is_loaded = True

        # Mock the methods that come before filtering
        with patch.object(detector, '_preprocess_frame') as mock_preprocess, \
             patch.object(detector, 'model') as mock_model, \
             patch.object(detector, '_postprocess_detections') as mock_postprocess, \
             patch.object(detector, '_filter_blacklisted_objects') as mock_filter:

            # Setup mocks
            mock_preprocess.return_value = MagicMock()
            mock_model.predict.return_value = {}
            mock_postprocess.return_value = [
                DetectedObject(label="person", confidence=0.9, bbox=BoundingBox(x=100, y=50, width=80, height=160)),
                DetectedObject(label="cat", confidence=0.8, bbox=BoundingBox(x=200, y=100, width=60, height=40))
            ]
            mock_filter.return_value = [
                DetectedObject(label="person", confidence=0.9, bbox=BoundingBox(x=100, y=50, width=80, height=160))
            ]

            # Mock frame
            mock_frame = MagicMock()

            # Run detection
            result = detector.detect_objects(mock_frame)

            # Verify filtering was called with confidence-filtered detections
            mock_filter.assert_called_once()
            called_args = mock_filter.call_args[0][0]  # First positional argument
            assert len(called_args) == 2  # Both detections passed to filtering
            assert called_args[0].label == "person"
            assert called_args[1].label == "cat"

            # Verify result comes from filter
            assert len(result) == 1
            assert result[0].label == "person"

    def test_blacklist_filtering_with_empty_blacklist(self):
        """Test that filtering is skipped when blacklist is empty."""
        config = SystemConfig(
            camera_rtsp_url="rtsp://test:123@192.168.1.100:554/stream1",
            coreml_model_path="models/test.mlmodel",
            min_object_confidence=0.5,
            blacklist_objects=[]
        )

        detector = CoreMLDetector(config)
        detector.is_loaded = True

        # Mock the methods
        with patch.object(detector, '_preprocess_frame') as mock_preprocess, \
             patch.object(detector, 'model') as mock_model, \
             patch.object(detector, '_postprocess_detections') as mock_postprocess, \
             patch.object(detector, '_filter_blacklisted_objects') as mock_filter:

            # Setup mocks
            mock_preprocess.return_value = MagicMock()
            mock_model.predict.return_value = {}
            confidence_filtered = [
                DetectedObject(label="person", confidence=0.9, bbox=BoundingBox(x=100, y=50, width=80, height=160)),
                DetectedObject(label="cat", confidence=0.8, bbox=BoundingBox(x=200, y=100, width=60, height=40))
            ]
            mock_postprocess.return_value = confidence_filtered
            mock_filter.return_value = confidence_filtered  # Should return same list

            mock_frame = MagicMock()

            result = detector.detect_objects(mock_frame)

            # Verify filtering was called but returned the same detections
            mock_filter.assert_called_once_with(confidence_filtered)
            assert len(result) == 2
            assert result[0].label == "person"
            assert result[1].label == "cat"

    def test_blacklist_filtering_integration_with_logging(self, integration_config):
        """Test that blacklist filtering logging works in the pipeline."""
        detector = CoreMLDetector(integration_config)
        detector.is_loaded = True

        # Mock the methods
        with patch.object(detector, '_preprocess_frame') as mock_preprocess, \
             patch.object(detector, 'model') as mock_model, \
             patch.object(detector, '_postprocess_detections') as mock_postprocess, \
             patch.object(detector, 'logger') as mock_logger:

            # Setup mocks
            mock_preprocess.return_value = MagicMock()
            mock_model.predict.return_value = {}
            mock_postprocess.return_value = [
                DetectedObject(label="person", confidence=0.9, bbox=BoundingBox(x=100, y=50, width=80, height=160)),
                DetectedObject(label="cat", confidence=0.8, bbox=BoundingBox(x=200, y=100, width=60, height=40))
            ]

            mock_frame = MagicMock()

            result = detector.detect_objects(mock_frame)

            # Verify logging was called
            mock_logger.info.assert_called()
            info_call = mock_logger.info.call_args[0][0]
            assert "Object detection completed" in info_call
            assert "1 objects detected" in info_call

    def test_blacklist_filtering_order_with_confidence(self, integration_config):
        """Test that confidence filtering happens before blacklist filtering."""
        detector = CoreMLDetector(integration_config)
        detector.is_loaded = True

        # Mock the methods
        with patch.object(detector, '_preprocess_frame') as mock_preprocess, \
             patch.object(detector, 'model') as mock_model, \
             patch.object(detector, '_postprocess_detections') as mock_postprocess, \
             patch.object(detector, '_filter_blacklisted_objects') as mock_filter:

            # Setup mocks - postprocess returns mixed confidence detections
            mock_preprocess.return_value = MagicMock()
            mock_model.predict.return_value = {}
            mock_postprocess.return_value = [
                DetectedObject(label="person", confidence=0.9, bbox=BoundingBox(x=100, y=50, width=80, height=160)),
                DetectedObject(label="cat", confidence=0.3, bbox=BoundingBox(x=200, y=100, width=60, height=40)),  # Below threshold
                DetectedObject(label="dog", confidence=0.8, bbox=BoundingBox(x=300, y=150, width=70, height=50))
            ]
            # Filter should only receive high-confidence detections
            mock_filter.return_value = [
                DetectedObject(label="person", confidence=0.9, bbox=BoundingBox(x=100, y=50, width=80, height=160)),
                DetectedObject(label="dog", confidence=0.8, bbox=BoundingBox(x=300, y=150, width=70, height=50))
            ]

            mock_frame = MagicMock()

            result = detector.detect_objects(mock_frame)

            # Verify filtering was called with only high-confidence detections
            mock_filter.assert_called_once()
            called_args = mock_filter.call_args[0][0]
            assert len(called_args) == 2  # cat was filtered out by confidence
            assert called_args[0].label == "person"
            assert called_args[1].label == "dog"

            assert len(result) == 2
            assert result[0].confidence == 0.9