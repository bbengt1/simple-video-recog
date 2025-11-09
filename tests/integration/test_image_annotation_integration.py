"""Integration tests for image annotation functionality."""

import time

import cv2
import numpy as np
import pytest

from core.image_annotator import ImageAnnotator
from core.models import BoundingBox, DetectedObject


class TestImageAnnotationIntegration:
    """Integration tests for ImageAnnotator with realistic scenarios."""

    @pytest.fixture
    def annotator(self):
        """Create ImageAnnotator instance."""
        return ImageAnnotator()

    @pytest.fixture
    def realistic_frame(self):
        """Create realistic test frame (720p resolution)."""
        # Create a frame with some visual content
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)

        # Add some colored regions to simulate real content
        frame[100:300, 100:400] = [50, 100, 150]  # Blueish region
        frame[400:600, 600:900] = [100, 150, 50]  # Greenish region
        frame[200:400, 800:1100] = [150, 50, 100]  # Reddish region

        return frame

    @pytest.fixture
    def multiple_detections_varying_confidence(self):
        """Create 5+ detections with varying confidence levels."""
        return [
            DetectedObject(
                label="person",
                confidence=0.95,
                bbox=BoundingBox(x=150, y=120, width=200, height=400)
            ),
            DetectedObject(
                label="car",
                confidence=0.72,
                bbox=BoundingBox(x=650, y=420, width=250, height=180)
            ),
            DetectedObject(
                label="bicycle",
                confidence=0.88,
                bbox=BoundingBox(x=850, y=220, width=180, height=280)
            ),
            DetectedObject(
                label="dog",
                confidence=0.45,
                bbox=BoundingBox(x=50, y=500, width=120, height=150)
            ),
            DetectedObject(
                label="backpack",
                confidence=0.62,
                bbox=BoundingBox(x=400, y=100, width=80, height=120)
            ),
            DetectedObject(
                label="umbrella",
                confidence=0.81,
                bbox=BoundingBox(x=1000, y=50, width=100, height=150)
            )
        ]

    def test_annotate_multiple_objects_realistic(
        self,
        annotator,
        realistic_frame,
        multiple_detections_varying_confidence,
        tmp_path
    ):
        """Test annotation with 5+ objects and visual inspection."""
        # Annotate frame
        annotated = annotator.annotate(
            realistic_frame,
            multiple_detections_varying_confidence
        )

        # Verify frame shape matches input
        assert annotated.shape == realistic_frame.shape

        # Verify frame was modified (has annotations)
        assert not np.array_equal(annotated, realistic_frame)

        # Save to temp file for manual inspection
        output_path = tmp_path / "annotated_test_frame.jpg"
        cv2.imwrite(str(output_path), annotated)

        # Verify file was created
        assert output_path.exists()

        # Print path for manual inspection
        print(f"\nAnnotated image saved to: {output_path}")

    def test_performance_10_objects(self, annotator, realistic_frame):
        """Test annotation performance with 10 objects (must be <20ms)."""
        # Create 10 detections
        detections = [
            DetectedObject(
                label=f"object_{i}",
                confidence=0.5 + (i * 0.05),
                bbox=BoundingBox(
                    x=50 + (i * 100),
                    y=50 + (i * 50),
                    width=100,
                    height=150
                )
            )
            for i in range(10)
        ]

        # Measure performance
        start_time = time.perf_counter()
        annotated = annotator.annotate(realistic_frame, detections)
        end_time = time.perf_counter()

        elapsed_ms = (end_time - start_time) * 1000

        # Verify annotation completed
        assert annotated.shape == realistic_frame.shape

        # Verify performance requirement (<20ms)
        print(f"\nAnnotation time for 10 objects: {elapsed_ms:.2f}ms")
        assert elapsed_ms < 20.0, f"Annotation took {elapsed_ms:.2f}ms, exceeds 20ms requirement"

    def test_end_to_end_annotation_workflow(
        self,
        annotator,
        realistic_frame,
        tmp_path
    ):
        """Test complete annotation workflow from detection to output."""
        # Simulate detection results from CoreML
        detections = [
            DetectedObject(
                label="person",
                confidence=0.92,
                bbox=BoundingBox(x=200, y=150, width=300, height=500)
            ),
            DetectedObject(
                label="car",
                confidence=0.88,
                bbox=BoundingBox(x=600, y=400, width=400, height=250)
            )
        ]

        # Annotate frame
        annotated = annotator.annotate(realistic_frame, detections)

        # Verify output
        assert annotated.shape == realistic_frame.shape
        assert annotated.dtype == np.uint8

        # Save annotated image
        output_path = tmp_path / "end_to_end_test.jpg"
        success = cv2.imwrite(str(output_path), annotated)

        assert success
        assert output_path.exists()

    def test_edge_case_all_objects_at_boundaries(
        self,
        annotator,
        realistic_frame
    ):
        """Test annotation with objects at all frame boundaries."""
        h, w = realistic_frame.shape[:2]

        detections = [
            # Top-left corner
            DetectedObject(
                label="top_left",
                confidence=0.9,
                bbox=BoundingBox(x=0, y=0, width=100, height=100)
            ),
            # Top-right corner
            DetectedObject(
                label="top_right",
                confidence=0.85,
                bbox=BoundingBox(x=w-100, y=0, width=100, height=100)
            ),
            # Bottom-left corner
            DetectedObject(
                label="bottom_left",
                confidence=0.75,
                bbox=BoundingBox(x=0, y=h-100, width=100, height=100)
            ),
            # Bottom-right corner
            DetectedObject(
                label="bottom_right",
                confidence=0.65,
                bbox=BoundingBox(x=w-100, y=h-100, width=100, height=100)
            )
        ]

        # Should complete without errors
        annotated = annotator.annotate(realistic_frame, detections)

        assert annotated.shape == realistic_frame.shape

    def test_color_coding_visual_verification(
        self,
        annotator,
        realistic_frame,
        tmp_path
    ):
        """Test color coding with visual verification."""
        # Create detections with different confidence levels
        detections = [
            # High confidence (green)
            DetectedObject(
                label="high_conf",
                confidence=0.95,
                bbox=BoundingBox(x=100, y=100, width=200, height=150)
            ),
            # Medium confidence (yellow)
            DetectedObject(
                label="medium_conf",
                confidence=0.65,
                bbox=BoundingBox(x=400, y=100, width=200, height=150)
            ),
            # Low confidence (red)
            DetectedObject(
                label="low_conf",
                confidence=0.30,
                bbox=BoundingBox(x=700, y=100, width=200, height=150)
            )
        ]

        annotated = annotator.annotate(realistic_frame, detections)

        # Save for visual inspection
        output_path = tmp_path / "color_coding_test.jpg"
        cv2.imwrite(str(output_path), annotated)

        print(f"\nColor coding test image saved to: {output_path}")
        print("Expected: Green (high), Yellow (medium), Red (low)")

        assert output_path.exists()

    def test_overlapping_objects_handling(
        self,
        annotator,
        realistic_frame,
        tmp_path
    ):
        """Test handling of overlapping bounding boxes."""
        # Create overlapping detections
        detections = [
            DetectedObject(
                label="person_1",
                confidence=0.92,
                bbox=BoundingBox(x=300, y=200, width=250, height=400)
            ),
            DetectedObject(
                label="person_2",
                confidence=0.88,
                bbox=BoundingBox(x=350, y=220, width=240, height=380)
            ),
            DetectedObject(
                label="person_3",
                confidence=0.85,
                bbox=BoundingBox(x=320, y=210, width=260, height=390)
            )
        ]

        annotated = annotator.annotate(realistic_frame, detections)

        # Save for visual inspection of label offset handling
        output_path = tmp_path / "overlapping_objects_test.jpg"
        cv2.imwrite(str(output_path), annotated)

        print(f"\nOverlapping objects test image saved to: {output_path}")
        print("Expected: Labels should be vertically offset to avoid collision")

        assert output_path.exists()
        assert annotated.shape == realistic_frame.shape
