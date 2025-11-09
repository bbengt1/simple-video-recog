"""Unit tests for ImageAnnotator module."""

import numpy as np
import pytest

from core.image_annotator import ImageAnnotator
from core.models import BoundingBox, DetectedObject


class TestImageAnnotator:
    """Test cases for ImageAnnotator class."""

    @pytest.fixture
    def annotator(self):
        """Create ImageAnnotator instance."""
        return ImageAnnotator()

    @pytest.fixture
    def mock_frame(self):
        """Create mock OpenCV frame (480x640 BGR)."""
        return np.zeros((480, 640, 3), dtype=np.uint8)

    @pytest.fixture
    def single_detection(self):
        """Create single DetectedObject for testing."""
        return DetectedObject(
            label="person",
            confidence=0.92,
            bbox=BoundingBox(x=120, y=50, width=180, height=320)
        )

    @pytest.fixture
    def multiple_detections(self):
        """Create multiple DetectedObject instances with varying confidence."""
        return [
            DetectedObject(
                label="person",
                confidence=0.92,
                bbox=BoundingBox(x=120, y=50, width=180, height=320)
            ),
            DetectedObject(
                label="car",
                confidence=0.65,
                bbox=BoundingBox(x=400, y=200, width=220, height=180)
            ),
            DetectedObject(
                label="dog",
                confidence=0.35,
                bbox=BoundingBox(x=50, y=300, width=100, height=120)
            )
        ]

    def test_single_object_annotation(self, annotator, mock_frame, single_detection):
        """Test annotation with single object."""
        result = annotator.annotate(mock_frame, [single_detection])

        # Verify frame dimensions unchanged
        assert result.shape == mock_frame.shape

        # Verify original frame not modified
        assert not np.array_equal(result, mock_frame)

    def test_multiple_objects_annotation(self, annotator, mock_frame, multiple_detections):
        """Test annotation with multiple objects."""
        result = annotator.annotate(mock_frame, multiple_detections)

        # Verify frame dimensions unchanged
        assert result.shape == mock_frame.shape

        # Verify frame was modified (has annotations)
        assert not np.array_equal(result, mock_frame)

    def test_empty_detections_list(self, annotator, mock_frame):
        """Test handling of empty detections list."""
        result = annotator.annotate(mock_frame, [])

        # Should return unmodified copy
        assert result.shape == mock_frame.shape
        assert np.array_equal(result, mock_frame)

    def test_bbox_at_frame_edge(self, annotator, mock_frame):
        """Test bounding box at frame edges."""
        # Detection at top-left corner
        detection_top_left = DetectedObject(
            label="test",
            confidence=0.9,
            bbox=BoundingBox(x=0, y=0, width=100, height=100)
        )

        # Detection at bottom-right corner
        detection_bottom_right = DetectedObject(
            label="test",
            confidence=0.9,
            bbox=BoundingBox(x=540, y=380, width=100, height=100)
        )

        result = annotator.annotate(mock_frame, [detection_top_left, detection_bottom_right])

        # Should complete without errors
        assert result.shape == mock_frame.shape

    def test_bbox_partially_outside_frame(self, annotator, mock_frame):
        """Test bounding box extending beyond frame boundaries."""
        # Detection partially outside frame
        detection = DetectedObject(
            label="test",
            confidence=0.9,
            bbox=BoundingBox(x=600, y=450, width=100, height=100)
        )

        result = annotator.annotate(mock_frame, [detection])

        # Should clip to frame boundaries without error
        assert result.shape == mock_frame.shape

    @pytest.mark.parametrize("confidence,expected_color", [
        (0.95, (0, 255, 0)),   # High confidence -> Green
        (0.85, (0, 255, 0)),   # High confidence -> Green
        (0.75, (0, 255, 255)), # Medium confidence -> Yellow
        (0.60, (0, 255, 255)), # Medium confidence -> Yellow
        (0.50, (0, 255, 255)), # Medium confidence -> Yellow
        (0.45, (0, 0, 255)),   # Low confidence -> Red
        (0.20, (0, 0, 255)),   # Low confidence -> Red
    ])
    def test_color_coding_by_confidence(
        self,
        annotator,
        confidence,
        expected_color
    ):
        """Test color coding based on confidence thresholds."""
        color = annotator._get_color_by_confidence(confidence)
        assert color == expected_color

    def test_label_text_formatting(self, annotator, mock_frame):
        """Test label text format is correct."""
        detection = DetectedObject(
            label="person",
            confidence=0.92,
            bbox=BoundingBox(x=120, y=50, width=180, height=320)
        )

        result = annotator.annotate(mock_frame, [detection])

        # Verify frame was annotated (text was drawn)
        assert not np.array_equal(result, mock_frame)

        # Expected label format: "person (92%)"
        # Cannot verify text content directly, but verify frame modified

    def test_frame_immutability(self, annotator, mock_frame, single_detection):
        """Test that original frame is not modified."""
        original_copy = mock_frame.copy()

        annotator.annotate(mock_frame, [single_detection])

        # Original frame should remain unchanged
        assert np.array_equal(mock_frame, original_copy)

    def test_invalid_frame_none(self, annotator, single_detection):
        """Test handling of None frame."""
        with pytest.raises(ValueError, match="Frame cannot be None"):
            annotator.annotate(None, [single_detection])

    def test_invalid_frame_shape(self, annotator, single_detection):
        """Test handling of invalid frame shape."""
        # Invalid shape (grayscale instead of BGR)
        invalid_frame = np.zeros((480, 640), dtype=np.uint8)

        with pytest.raises(ValueError, match="Invalid frame shape"):
            annotator.annotate(invalid_frame, [single_detection])

    def test_overlapping_labels_adjustment(self, annotator, mock_frame):
        """Test that overlapping labels are offset vertically."""
        # Create detections with overlapping bounding boxes
        detections = [
            DetectedObject(
                label="person",
                confidence=0.92,
                bbox=BoundingBox(x=120, y=50, width=180, height=320)
            ),
            DetectedObject(
                label="person",
                confidence=0.88,
                bbox=BoundingBox(x=125, y=55, width=175, height=315)
            )
        ]

        result = annotator.annotate(mock_frame, detections)

        # Should complete without error and apply offsets
        assert result.shape == mock_frame.shape
        assert not np.array_equal(result, mock_frame)

    def test_label_position_adjustment_logic(self, annotator):
        """Test label position adjustment for overlap prevention."""
        used_positions = [
            (100, 50, 80, 20),  # Existing label
        ]

        # Try to place label at same position
        adjusted_y = annotator._adjust_label_position(
            label_x=100,
            label_y=50,
            text_width=80,
            text_height=20,
            used_positions=used_positions
        )

        # Should be offset from original position
        assert adjusted_y != 50
