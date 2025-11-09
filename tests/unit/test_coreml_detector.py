"""Unit tests for CoreML detector module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from core.config import SystemConfig
from core.exceptions import CoreMLLoadError
from apple_platform.coreml_detector import CoreMLDetector


@pytest.fixture
def sample_config():
    """Sample system configuration for testing."""
    return SystemConfig(
        camera_rtsp_url="rtsp://test:123@192.168.1.100:554/stream1",
        coreml_model_path="models/test.mlmodel"
    )


@pytest.fixture
def mock_coreml_model():
    """Mock CoreML model for testing."""
    model = Mock()
    model.model_name = "TestModel"
    model.compute_unit = "ALL"  # ANE compatible
    model.input_description = {"input": Mock()}
    model.output_description = {"output": Mock()}

    # Mock input shape
    input_desc = Mock()
    input_desc.type.multiArrayType.shape = [1, 416, 416, 3]
    model.input_description = {"input": input_desc}

    return model


class TestCoreMLDetector:
    """Test cases for CoreMLDetector class."""

    def test_init(self, sample_config):
        """Test CoreML detector initialization."""
        detector = CoreMLDetector(sample_config)
        assert detector.config == sample_config
        assert detector.model is None
        assert detector.model_metadata is None
        assert not detector.is_loaded

    @patch('apple_platform.coreml_detector.coremltools.models.MLModel')
    def test_load_model_success_ane_compatible(self, mock_mlmodel_class, sample_config, mock_coreml_model):
        """Test successful model loading with ANE compatibility."""
        mock_mlmodel_class.return_value = mock_coreml_model

        detector = CoreMLDetector(sample_config)

        with patch.object(detector.logger, 'info') as mock_info, \
             patch.object(detector.logger, 'debug') as mock_debug, \
             patch('time.time', side_effect=[0, 0.1]), \
             patch.object(mock_coreml_model, 'predict'):

            detector.load_model("models/test.mlmodel")

            assert detector.is_loaded
            assert detector.model == mock_coreml_model
            assert detector.model_metadata is not None, "model_metadata should be set after successful load_model"
            assert detector.model_metadata['ane_compatible'] is True
            assert detector.model_metadata['model_name'] == "TestModel"
            assert detector.model_metadata['input_shape'] == (1, 416, 416, 3)

            # Check logging calls
            mock_info.assert_any_call("✓ CoreML model loaded: TestModel (ANE-compatible)")
            mock_info.assert_any_call("Model warm-up completed in 0.100s")

    @patch('apple_platform.coreml_detector.coremltools.models.MLModel')
    def test_load_model_cpu_gpu_warning(self, mock_mlmodel_class, sample_config):
        """Test model loading with CPU/GPU compute unit warning."""
        mock_model = Mock()
        mock_model.model_name = "CPUGPUModel"
        mock_model.compute_unit = "CPU_AND_GPU"
        mock_model.input_description = {}
        mock_model.output_description = {}
        mock_mlmodel_class.return_value = mock_model

        detector = CoreMLDetector(sample_config)

        with patch.object(detector.logger, 'warning') as mock_warning, \
             patch.object(detector.logger, 'info'), \
             patch('time.time', side_effect=[0, 0.05]), \
             patch.object(mock_model, 'predict'):

            detector.load_model("models/cpu_gpu.mlmodel")

            mock_warning.assert_called_with(
                "Model will run on CPU/GPU (slower), consider using ANE-optimized model"
            )
            assert detector.model_metadata is not None, "model_metadata should be set after successful load_model"
            assert detector.model_metadata['ane_compatible'] is False

    def test_load_model_file_not_found(self, sample_config):
        """Test error handling for missing model file."""
        detector = CoreMLDetector(sample_config)

        with patch('apple_platform.coreml_detector.coremltools.models.MLModel', side_effect=FileNotFoundError), \
             patch.object(detector.logger, 'error') as mock_error:

            with pytest.raises(CoreMLLoadError, match="CoreML model file not found"):
                detector.load_model("models/missing.mlmodel")

            mock_error.assert_called()

    def test_load_model_corrupted(self, sample_config):
        """Test error handling for corrupted model file."""
        detector = CoreMLDetector(sample_config)

        with patch('apple_platform.coreml_detector.coremltools.models.MLModel', side_effect=Exception("Corrupted model")), \
             patch.object(detector.logger, 'error') as mock_error:

            with pytest.raises(CoreMLLoadError, match="Failed to load CoreML model"):
                detector.load_model("models/corrupted.mlmodel")

            mock_error.assert_called()

    @patch('apple_platform.coreml_detector.coremltools.models.MLModel')
    def test_warmup_inference_failure(self, mock_mlmodel_class, sample_config, mock_coreml_model):
        """Test handling of warm-up inference failure."""
        mock_mlmodel_class.return_value = mock_coreml_model
        mock_coreml_model.predict.side_effect = Exception("Inference failed")

        detector = CoreMLDetector(sample_config)

        with patch.object(detector.logger, 'warning') as mock_warning, \
             patch.object(detector.logger, 'info'), \
             patch('time.time', side_effect=[0, 0.02]):

            detector.load_model("models/test.mlmodel")

            mock_warning.assert_called_with("Model warm-up failed: Inference failed")
            assert detector.model_metadata is not None, "model_metadata should be set after successful load_model"
            assert detector.model_metadata['warmup_time'] == 0.02