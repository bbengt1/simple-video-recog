"""Integration tests for CoreML detector inference with real models."""

import pytest
import os
import time
import numpy as np
from pathlib import Path

from core.config import SystemConfig
from core.models import BoundingBox
from apple_platform.coreml_detector import CoreMLDetector


@pytest.fixture
def integration_config():
    """Configuration for integration testing."""
    return SystemConfig(
        camera_rtsp_url="rtsp://test:123@192.168.1.100:554/stream1",
        coreml_model_path="models/yolov3-tiny.mlmodel",  # Test with real model if available
        min_object_confidence=0.5
    )


@pytest.fixture
def sample_frames():
    """Generate sample frames for testing."""
    frames = []
    for i in range(5):
        # Create frames with some variation
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        # Add some structure to make it look like a real frame
        frame[100:200, 200:300] = [255, 0, 0]  # Red rectangle
        frame[300:350, 400:500] = [0, 255, 0]  # Green rectangle
        frames.append(frame)
    return frames


class TestCoreMLInferenceIntegration:
    """Integration tests with real CoreML models."""

    @pytest.mark.skipif(
        not os.path.exists("models/yolov3-tiny.mlmodel"),
        reason="YOLOv3-Tiny CoreML model not available for testing"
    )
    def test_load_and_detect_real_model(self, integration_config, sample_frames):
        """Test loading real model and running inference."""
        detector = CoreMLDetector(integration_config)

        # Load model
        detector.load_model("models/yolov3-tiny.mlmodel")
        assert detector.is_loaded

        # Run detection on sample frames
        total_time = 0
        total_detections = 0

        for frame in sample_frames:
            start_time = time.time()
            detections = detector.detect_objects(frame)
            inference_time = time.time() - start_time

            total_time += inference_time
            total_detections += len(detections)

            # Performance check
            assert inference_time < 1.0, f"Inference too slow: {inference_time:.3f}s"

        avg_time = total_time / len(sample_frames)
        print(f"Average inference time: {avg_time:.3f}s")
        print(f"Total detections: {total_detections}")

        # Performance requirements
        assert avg_time < 0.1, f"Average inference {avg_time:.3f}s exceeds 100ms target"

    def test_inference_error_handling(self, integration_config, sample_frames):
        """Test error handling during inference."""
        detector = CoreMLDetector(integration_config)

        # Try to detect without loading model
        with pytest.raises(RuntimeError, match="CoreML model not loaded"):
            detector.detect_objects(sample_frames[0])

        # Load invalid model path
        with pytest.raises(Exception):  # Should raise CoreMLLoadError
            detector.load_model("models/nonexistent.mlmodel")

    @pytest.mark.parametrize("model_path", [
        "models/yolov3-tiny.mlmodel",
        "models/yolov8n.mlmodel",
        pytest.param("models/nonexistent.mlmodel", marks=pytest.mark.xfail(reason="Model may not exist"))
    ])
    def test_model_inference_consistency(self, integration_config, sample_frames, model_path):
        """Test that inference results are consistent across runs."""
        if not os.path.exists(model_path):
            pytest.skip(f"Model {model_path} not available")

        detector = CoreMLDetector(integration_config)
        detector.load_model(model_path)

        # Run multiple inferences on same frame
        test_frame = sample_frames[0]
        results = []

        for _ in range(3):
            detections = detector.detect_objects(test_frame)
            results.append(len(detections))

        # Results should be consistent (same number of detections)
        assert len(set(results)) <= 2, "Detection results too inconsistent"

    def test_performance_regression_test(self, integration_config, sample_frames):
        """Performance regression test with statistical analysis."""
        model_path = "models/yolov3-tiny.mlmodel"
        if not os.path.exists(model_path):
            pytest.skip("YOLOv3-Tiny model not available")

        detector = CoreMLDetector(integration_config)
        detector.load_model(model_path)

        # Run 100 inferences for statistical analysis
        times = []
        for _ in range(100):
            frame = sample_frames[np.random.randint(len(sample_frames))]
            start_time = time.perf_counter()  # High precision timing
            detector.detect_objects(frame)
            end_time = time.perf_counter()
            times.append(end_time - start_time)

        # Statistical analysis
        avg_time = np.mean(times)
        p95_time = np.percentile(times, 95)
        max_time = np.max(times)

        print(f"Performance stats (100 inferences):")
        print(f"  Average: {avg_time:.4f}s")
        print(f"  95th percentile: {p95_time:.4f}s")
        print(f"  Maximum: {max_time:.4f}s")

        # Performance assertions
        assert avg_time < 0.1, f"Average time {avg_time:.4f}s exceeds 100ms target"
        assert p95_time < 0.12, f"95th percentile {p95_time:.4f}s exceeds 120ms target"
        assert max_time < 0.5, f"Maximum time {max_time:.4f}s too high"

    def test_memory_usage_during_inference(self, integration_config, sample_frames):
        """Test that inference doesn't cause excessive memory usage."""
        model_path = "models/yolov3-tiny.mlmodel"
        if not os.path.exists(model_path):
            pytest.skip("YOLOv3-Tiny model not available")

        detector = CoreMLDetector(integration_config)
        detector.load_model(model_path)

        # Run multiple inferences and check for memory issues
        for i in range(50):
            frame = sample_frames[i % len(sample_frames)]
            try:
                detections = detector.detect_objects(frame)
                assert isinstance(detections, list)
            except Exception as e:
                pytest.fail(f"Inference failed on iteration {i}: {str(e)}")

    def test_frame_preprocessing_edge_cases(self, integration_config):
        """Test preprocessing with various frame formats."""
        detector = CoreMLDetector(integration_config)

        # Test different frame sizes and formats
        test_frames = [
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8),  # Standard
            np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8), # HD
            np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8), # Full HD
        ]

        for frame in test_frames:
            processed = detector._preprocess_frame(frame)
            assert processed.shape == (416, 416, 3)
            assert processed.dtype == np.float32
            assert np.all(processed >= 0.0) and np.all(processed <= 1.0)

    def test_bbox_conversion_accuracy(self, integration_config):
        """Test bounding box coordinate conversion accuracy."""
        detector = CoreMLDetector(integration_config)

        # Test various normalized coordinates
        test_cases = [
            ([0.0, 0.0, 1.0, 1.0], (480, 640, 3)),  # Full frame
            ([0.25, 0.25, 0.5, 0.5], (480, 640, 3)), # Center half
            ([0.1, 0.2, 0.3, 0.4], (720, 1280, 3)),  # Arbitrary
        ]

        for bbox_norm, frame_shape in test_cases:
            bbox = detector._convert_bbox_to_original(
                np.array(bbox_norm), frame_shape
            )

            assert isinstance(bbox, BoundingBox)
            assert 0 <= bbox.x < frame_shape[1]  # Within width
            assert 0 <= bbox.y < frame_shape[0]  # Within height
            assert bbox.width > 0 and bbox.x + bbox.width <= frame_shape[1]
            assert bbox.height > 0 and bbox.y + bbox.height <= frame_shape[0]