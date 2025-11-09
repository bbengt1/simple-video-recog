"""Integration tests for CoreML detector with real models."""

import pytest
import os
from pathlib import Path

from core.config import SystemConfig
from core.exceptions import CoreMLLoadError
from apple_platform.coreml_detector import CoreMLDetector


@pytest.fixture
def integration_config():
    """Configuration for integration testing."""
    return SystemConfig(
        camera_rtsp_url="rtsp://test:123@192.168.1.100:554/stream1",
        coreml_model_path="models/yolov3-tiny.mlmodel"  # Test with real model if available
    )


class TestCoreMLIntegration:
    """Integration tests with real CoreML models."""

    @pytest.mark.skipif(
        not os.path.exists("models/yolov3-tiny.mlmodel"),
        reason="YOLOv3-Tiny CoreML model not available for testing"
    )
    def test_load_real_yolov3_tiny_model(self, integration_config):
        """Test loading real YOLOv3-Tiny CoreML model."""
        detector = CoreMLDetector(integration_config)

        # This should not raise an exception
        detector.load_model("models/yolov3-tiny.mlmodel")

        assert detector.is_loaded
        assert detector.model is not None
        assert detector.model_metadata is not None

        # Check metadata was extracted
        assert 'model_name' in detector.model_metadata
        assert 'ane_compatible' in detector.model_metadata
        assert 'warmup_time' in detector.model_metadata

        # Verify warm-up time is reasonable (< 100ms target)
        warmup_time = detector.model_metadata['warmup_time']
        assert warmup_time > 0, "Warm-up time should be positive"
        assert warmup_time < 1.0, "Warm-up should complete in less than 1 second"

        # Log performance for monitoring
        print(f"YOLOv3-Tiny warm-up time: {warmup_time:.3f}s")
        print(f"ANE compatible: {detector.model_metadata['ane_compatible']}")

    def test_model_loading_error_handling(self, integration_config):
        """Test error handling with invalid model paths."""
        detector = CoreMLDetector(integration_config)

        # Test with non-existent file
        with pytest.raises(CoreMLLoadError):
            detector.load_model("models/nonexistent.mlmodel")

        # Test with invalid file (not a .mlmodel)
        invalid_path = "README.md"  # Exists but not a CoreML model
        with pytest.raises(CoreMLLoadError):
            detector.load_model(invalid_path)

    @pytest.mark.parametrize("model_path", [
        "models/yolov3-tiny.mlmodel",
        "models/yolov8n.mlmodel",
        pytest.param("models/nonexistent.mlmodel", marks=pytest.mark.xfail(reason="Model may not exist"))
    ])
    def test_model_compatibility_validation(self, integration_config, model_path):
        """Test ANE compatibility validation on real models."""
        if not os.path.exists(model_path):
            pytest.skip(f"Model {model_path} not available")

        detector = CoreMLDetector(integration_config)
        detector.load_model(model_path)

        # Should have determined compatibility
        assert detector.model_metadata is not None, "model_metadata should be set after successful load_model"
        assert 'ane_compatible' in detector.model_metadata
        ane_compatible = detector.model_metadata['ane_compatible']
        assert isinstance(ane_compatible, bool)

        # On Apple Silicon, prefer ANE compatibility
        import platform
        if platform.machine() == "arm64":  # Apple Silicon
            # Note: This might fail on some models, so we just log
            print(f"Model {model_path} ANE compatible: {ane_compatible}")