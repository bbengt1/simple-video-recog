"""Unit tests for CoreML detector inference functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import cv2

from core.config import SystemConfig
from core.models import BoundingBox, DetectedObject
from apple_platform.coreml_detector import CoreMLDetector


@pytest.fixture
def sample_config():
    """Sample system configuration for testing."""
    return SystemConfig(
        camera_rtsp_url="rtsp://test:123@192.168.1.100:554/stream1",
        coreml_model_path="models/test.mlmodel",
        min_object_confidence=0.5
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


@pytest.fixture
def sample_frame():
    """Sample frame for testing."""
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)


class TestCoreMLDetectorInference:
    """Test cases for CoreMLDetector inference methods."""

    def test_detect_objects_model_not_loaded(self, sample_config, sample_frame):
        """Test detect_objects raises error when model not loaded."""
        detector = CoreMLDetector(sample_config)

        with pytest.raises(RuntimeError, match="CoreML model not loaded"):
            detector.detect_objects(sample_frame)

    @patch('apple_platform.coreml_detector.CoreMLDetector._preprocess_frame')
    @patch('apple_platform.coreml_detector.CoreMLDetector._postprocess_detections')
    def test_detect_objects_success(self, mock_postprocess, mock_preprocess,
                                   sample_config, mock_coreml_model, sample_frame):
        """Test successful object detection."""
        # Setup
        detector = CoreMLDetector(sample_config)
        detector.model = mock_coreml_model
        detector.is_loaded = True
        detector.model_metadata = {'input_shape': (416, 416, 3)}

        mock_preprocess.return_value = np.random.rand(416, 416, 3).astype(np.float32)
        mock_postprocess.return_value = [
            DetectedObject(label="person", confidence=0.9, bbox=BoundingBox(x=100, y=50, width=80, height=160)),
            DetectedObject(label="car", confidence=0.3, bbox=BoundingBox(x=200, y=100, width=120, height=60))
        ]
        mock_coreml_model.predict.return_value = {'coordinates': [], 'confidence': []}

        # Execute
        with patch.object(detector.logger, 'info'), \
             patch('time.time', side_effect=[0, 0.05]):
            results = detector.detect_objects(sample_frame)

        # Assert
        assert len(results) == 1  # Only high confidence detection
        assert results[0].label == "person"
        assert results[0].confidence == 0.9
        mock_preprocess.assert_called_once()
        mock_postprocess.assert_called_once()

    @patch('apple_platform.coreml_detector.CoreMLDetector._preprocess_frame')
    def test_detect_objects_inference_failure(self, mock_preprocess, sample_config,
                                            mock_coreml_model, sample_frame):
        """Test handling of inference failure."""
        detector = CoreMLDetector(sample_config)
        detector.model = mock_coreml_model
        detector.is_loaded = True
        detector.model_metadata = {'input_shape': (416, 416, 3)}

        mock_preprocess.return_value = np.random.rand(416, 416, 3).astype(np.float32)
        mock_coreml_model.predict.side_effect = Exception("Inference failed")

        with patch.object(detector.logger, 'error') as mock_error:
            with pytest.raises(Exception, match="Inference failed"):
                detector.detect_objects(sample_frame)

        mock_error.assert_called()

    def test_preprocess_frame_bgr_to_rgb(self, sample_config, mock_coreml_model, sample_frame):
        """Test frame preprocessing converts BGR to RGB."""
        detector = CoreMLDetector(sample_config)
        detector.model = mock_coreml_model
        detector.is_loaded = True
        detector.model_metadata = {'input_shape': (416, 416, 3)}

        # Create a test frame with known BGR values
        bgr_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        bgr_frame[:, :, 0] = 255  # Blue channel
        bgr_frame[:, :, 1] = 128  # Green channel
        bgr_frame[:, :, 2] = 64   # Red channel

        processed = detector._preprocess_frame(bgr_frame)

        # Check RGB conversion (BGR -> RGB swaps B and R) and CHW transpose
        assert processed.shape == (3, 416, 416)  # CHW format
        assert processed.dtype == np.float32
        # After conversion: BGR(255,128,64) -> RGB(64,128,255) -> CHW(64,128,255 at [0,0,0])
        assert processed[0, 0, 0] == 64/255.0   # Red channel (first in CHW)
        assert processed[1, 0, 0] == 128/255.0  # Green channel (second in CHW)
        assert processed[2, 0, 0] == 255/255.0  # Blue channel (third in CHW)

    def test_preprocess_frame_resize(self, sample_config, mock_coreml_model):
        """Test frame resizing during preprocessing."""
        detector = CoreMLDetector(sample_config)
        detector.model = mock_coreml_model
        detector.is_loaded = True
        detector.model_metadata = {'input_shape': (208, 208, 3)}  # Different size

        input_frame = np.random.randint(0, 255, (100, 150, 3), dtype=np.uint8)

        processed = detector._preprocess_frame(input_frame)

        assert processed.shape == (3, 208, 208)  # CHW format

    def test_preprocess_frame_default_size(self, sample_config, mock_coreml_model):
        """Test default size when model metadata unavailable."""
        detector = CoreMLDetector(sample_config)
        detector.model = mock_coreml_model
        detector.is_loaded = True
        detector.model_metadata = {}  # No input_shape

        input_frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        processed = detector._preprocess_frame(input_frame)

        assert processed.shape == (3, 416, 416)  # Default size, CHW format

    def test_postprocess_detections_empty_outputs(self, sample_config, mock_coreml_model):
        """Test postprocessing with empty model outputs."""
        detector = CoreMLDetector(sample_config)
        detector.model = mock_coreml_model
        detector.is_loaded = True

        raw_outputs = {}  # No expected keys
        frame_shape = (480, 640, 3)

        results = detector._postprocess_detections(raw_outputs, frame_shape)

        assert results == []

    def test_postprocess_detections_with_mock_data(self, sample_config, mock_coreml_model):
        """Test postprocessing with mock detection data."""
        detector = CoreMLDetector(sample_config)
        detector.model = mock_coreml_model
        detector.is_loaded = True

        # Mock raw outputs
        raw_outputs = {
            'coordinates': np.array([[0.2, 0.3, 0.4, 0.5]]),  # Normalized bbox
            'confidence': np.array([0.8])
        }
        frame_shape = (480, 640, 3)

        with patch.object(detector, '_apply_nms') as mock_nms, \
             patch.object(detector, '_convert_bbox_to_original') as mock_convert:

            mock_nms.return_value = [{
                'bbox': np.array([0.2, 0.3, 0.4, 0.5]),
                'confidence': 0.8,
                'label': 'person'
            }]
            mock_convert.return_value = BoundingBox(x=128, y=144, width=256, height=240)

            results = detector._postprocess_detections(raw_outputs, frame_shape)

            assert len(results) == 1
            assert results[0].label == 'person'
            assert results[0].confidence == 0.8
            mock_nms.assert_called_once()
            mock_convert.assert_called_once()

    def test_apply_nms_simple(self, sample_config, mock_coreml_model):
        """Test basic NMS functionality."""
        detector = CoreMLDetector(sample_config)
        detector.model = mock_coreml_model
        detector.is_loaded = True

        # Mock coordinates and confidences - create more overlapping boxes
        coordinates = np.array([
            [0.1, 0.1, 0.4, 0.4],  # High confidence - large box
            [0.15, 0.15, 0.35, 0.35],  # Overlapping with first, lower confidence - should be suppressed
            [0.6, 0.6, 0.8, 0.8]   # Non-overlapping
        ])
        confidences = np.array([0.9, 0.7, 0.8])

        results = detector._apply_nms(coordinates, confidences, iou_threshold=0.3)

        # Should return 2 detections (first and third, second suppressed due to high IoU)
        assert len(results) == 2
        assert results[0]['confidence'] == 0.9
        assert results[1]['confidence'] == 0.8

    def test_calculate_iou(self, sample_config, mock_coreml_model):
        """Test IoU calculation."""
        detector = CoreMLDetector(sample_config)
        detector.model = mock_coreml_model
        detector.is_loaded = True

        # Perfect overlap
        bbox1 = np.array([0, 0, 10, 10])
        bbox2 = np.array([0, 0, 10, 10])
        iou = detector._calculate_iou(bbox1, bbox2)
        assert iou == 1.0

        # No overlap
        bbox1 = np.array([0, 0, 5, 5])
        bbox2 = np.array([10, 10, 15, 15])
        iou = detector._calculate_iou(bbox1, bbox2)
        assert iou == 0.0

        # Partial overlap
        bbox1 = np.array([0, 0, 10, 10])
        bbox2 = np.array([5, 5, 15, 15])
        iou = detector._calculate_iou(bbox1, bbox2)
        expected_iou = 25 / (100 + 100 - 25)  # intersection / union
        assert abs(iou - expected_iou) < 0.001

    def test_convert_bbox_to_original(self, sample_config, mock_coreml_model):
        """Test bounding box coordinate conversion."""
        detector = CoreMLDetector(sample_config)
        detector.model = mock_coreml_model
        detector.is_loaded = True

        # Normalized bbox [x, y, w, h]
        bbox = np.array([0.25, 0.5, 0.5, 0.25])  # 25% x, 50% y, 50% w, 25% h
        original_shape = (400, 800, 3)  # height=400, width=800

        result = detector._convert_bbox_to_original(bbox, original_shape)

        assert isinstance(result, BoundingBox)
        assert result.x == 200  # 0.25 * 800
        assert result.y == 200  # 0.5 * 400
        assert result.width == 400  # 0.5 * 800
        assert result.height == 100  # 0.25 * 400

    def test_detect_objects_confidence_filtering(self, sample_config, mock_coreml_model, sample_frame):
        """Test confidence threshold filtering."""
        # Set low confidence threshold
        sample_config.min_object_confidence = 0.3

        detector = CoreMLDetector(sample_config)
        detector.model = mock_coreml_model
        detector.is_loaded = True
        detector.model_metadata = {'input_shape': (416, 416, 3)}

        with patch.object(detector, '_preprocess_frame') as mock_preprocess, \
             patch.object(detector, '_postprocess_detections') as mock_postprocess, \
             patch.object(detector.logger, 'info'), \
             patch('time.time', side_effect=[0, 0.05]):

            mock_preprocess.return_value = np.random.rand(416, 416, 3).astype(np.float32)
            mock_coreml_model.predict.return_value = {}

            # Mock postprocessing to return mixed confidence detections
            mock_postprocess.return_value = [
                DetectedObject(label="person", confidence=0.9, bbox=BoundingBox(x=100, y=50, width=80, height=160)),
                DetectedObject(label="car", confidence=0.2, bbox=BoundingBox(x=200, y=100, width=120, height=60)),  # Below threshold
                DetectedObject(label="dog", confidence=0.7, bbox=BoundingBox(x=300, y=150, width=60, height=40))
            ]

            results = detector.detect_objects(sample_frame)

            # Should filter out the low confidence detection
            assert len(results) == 2
            assert all(det.confidence >= 0.3 for det in results)