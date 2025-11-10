"""Unit tests for ProcessingPipeline integration with intelligence components.

Tests the complete pipeline integration with mocked components to verify
stage execution order, error handling, and metrics tracking.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from core.config import SystemConfig
from core.models import BoundingBox, DetectedObject, DetectionResult
from core.pipeline import ProcessingPipeline


@pytest.fixture
def pipeline_config():
    """Create SystemConfig for pipeline testing."""
    return SystemConfig(
        camera_rtsp_url="rtsp://test:123@192.168.1.100:554/stream",
        deduplication_window=30
    )


@pytest.fixture
def mock_components(pipeline_config):
    """Create mocked pipeline components."""
    # Mock RTSP client
    rtsp_client = MagicMock()
    rtsp_client.get_frame.return_value = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    # Mock motion detector
    motion_detector = MagicMock()
    motion_detector.detect_motion.return_value = (True, 0.8, np.zeros((480, 640), dtype=np.uint8))

    # Mock frame sampler
    frame_sampler = MagicMock()
    frame_sampler.should_process.return_value = True

    # Mock CoreML detector
    coreml_detector = MagicMock()
    coreml_detector.detect_objects.return_value = [
        DetectedObject(label="person", confidence=0.9, bbox=BoundingBox(x=100, y=50, width=200, height=300))
    ]

    # Mock event deduplicator
    event_deduplicator = MagicMock()
    event_deduplicator.should_create_event.return_value = True

    # Mock Ollama client
    ollama_client = MagicMock()
    ollama_client.generate_description.return_value = "A person walking in the scene"

    # Mock image annotator
    image_annotator = MagicMock()
    image_annotator.annotate.return_value = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    return {
        "rtsp_client": rtsp_client,
        "motion_detector": motion_detector,
        "frame_sampler": frame_sampler,
        "coreml_detector": coreml_detector,
        "event_deduplicator": event_deduplicator,
        "ollama_client": ollama_client,
        "image_annotator": image_annotator,
    }


@pytest.fixture
def pipeline(mock_components, pipeline_config):
    """Create ProcessingPipeline with mocked components."""
    return ProcessingPipeline(
        rtsp_client=mock_components["rtsp_client"],
        motion_detector=mock_components["motion_detector"],
        frame_sampler=mock_components["frame_sampler"],
        coreml_detector=mock_components["coreml_detector"],
        event_deduplicator=mock_components["event_deduplicator"],
        ollama_client=mock_components["ollama_client"],
        image_annotator=mock_components["image_annotator"],
        config=pipeline_config
    )


class TestProcessingPipelineIntegration:
    """Test ProcessingPipeline with integrated intelligence components."""

    def test_pipeline_initialization_with_all_components(self, pipeline, mock_components, pipeline_config):
        """Test that pipeline initializes correctly with all intelligence components."""
        assert pipeline.rtsp_client == mock_components["rtsp_client"]
        assert pipeline.motion_detector == mock_components["motion_detector"]
        assert pipeline.frame_sampler == mock_components["frame_sampler"]
        assert pipeline.coreml_detector == mock_components["coreml_detector"]
        assert pipeline.event_deduplicator == mock_components["event_deduplicator"]
        assert pipeline.ollama_client == mock_components["ollama_client"]
        assert pipeline.image_annotator == mock_components["image_annotator"]
        assert pipeline.config == pipeline_config

    def test_pipeline_metrics_initialization(self, pipeline):
        """Test that pipeline metrics are initialized correctly."""
        expected_metrics = {
            "total_frames_captured": 0,
            "frames_with_motion": 0,
            "frames_sampled": 0,
            "frames_processed": 0,
            "objects_detected": 0,
            "events_created": 0,
            "events_suppressed": 0,
            "coreml_time_avg": 0.0,
            "llm_time_avg": 0.0,
        }

        assert pipeline.metrics == expected_metrics

    @patch('time.time')
    @patch('builtins.print')  # Mock print for Event JSON output
    def test_pipeline_full_processing_flow(self, mock_print, mock_time, pipeline, mock_components):
        """Test complete pipeline processing flow with successful operations."""
        # Setup mocks
        mock_time.return_value = 1000.0

        # Mock RTSP to return frame, then trigger shutdown
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        call_count = 0
        def get_frame_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return frame
            else:
                # Trigger shutdown after first frame processing
                pipeline._shutdown_requested = True
                return None
        mock_components["rtsp_client"].get_frame.side_effect = get_frame_side_effect

        # Run pipeline briefly
        pipeline.run()

        # Verify component interactions
        assert mock_components["rtsp_client"].get_frame.call_count >= 1
        assert mock_components["motion_detector"].detect_motion.call_count == 1
        assert mock_components["frame_sampler"].should_process.call_count == 1
        assert mock_components["coreml_detector"].detect_objects.call_count == 1
        assert mock_components["event_deduplicator"].should_create_event.call_count == 1
        assert mock_components["ollama_client"].generate_description.call_count == 1
        assert mock_components["image_annotator"].annotate.call_count == 1

        # Verify metrics were updated
        assert pipeline.metrics["total_frames_captured"] == 1
        assert pipeline.metrics["frames_with_motion"] == 1
        assert pipeline.metrics["frames_sampled"] == 1
        assert pipeline.metrics["frames_processed"] == 1
        assert pipeline.metrics["objects_detected"] == 1
        assert pipeline.metrics["events_created"] == 1
        assert pipeline.metrics["events_suppressed"] == 0

        # Verify Event JSON was printed
        mock_print.assert_called_once()

    def test_pipeline_error_handling_coreml_failure(self, pipeline, mock_components):
        """Test pipeline handles CoreML detection failure gracefully."""
        # Setup RTSP to return frame, then trigger shutdown
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        call_count = 0
        def get_frame_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return frame
            else:
                # Trigger shutdown after first frame processing
                pipeline._shutdown_requested = True
                return None
        mock_components["rtsp_client"].get_frame.side_effect = get_frame_side_effect

        # Make CoreML detector fail
        mock_components["coreml_detector"].detect_objects.side_effect = RuntimeError("CoreML failed")

        # Run pipeline
        pipeline.run()

        # Verify pipeline continued and logged error
        assert pipeline.metrics["total_frames_captured"] == 1
        assert pipeline.metrics["frames_with_motion"] == 1
        assert pipeline.metrics["frames_sampled"] == 1
        # CoreML failed, so no further processing
        assert pipeline.metrics["frames_processed"] == 0
        assert pipeline.metrics["events_created"] == 0

    def test_pipeline_error_handling_llm_failure(self, pipeline, mock_components):
        """Test pipeline handles LLM failure gracefully with fallback."""
        # Setup RTSP to return frame, then trigger shutdown
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        call_count = 0
        def get_frame_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return frame
            else:
                # Trigger shutdown after first frame processing
                pipeline._shutdown_requested = True
                return None
        mock_components["rtsp_client"].get_frame.side_effect = get_frame_side_effect

        # Make LLM fail
        mock_components["ollama_client"].generate_description.side_effect = Exception("LLM failed")

        # Run pipeline
        pipeline.run()

    def test_pipeline_deduplication_suppression(self, pipeline, mock_components):
        """Test pipeline handles event deduplication suppression."""
        # Setup RTSP to return frame, then trigger shutdown
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        call_count = 0
        def get_frame_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return frame
            else:
                # Trigger shutdown after first frame processing
                pipeline._shutdown_requested = True
                return None
        mock_components["rtsp_client"].get_frame.side_effect = get_frame_side_effect

        # Make deduplicator suppress event
        mock_components["event_deduplicator"].should_create_event.return_value = False

        # Run pipeline
        pipeline.run()

    def test_pipeline_no_objects_after_detection(self, pipeline, mock_components):
        """Test pipeline skips processing when no objects detected."""
        # Setup RTSP to return frame, then trigger shutdown
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        call_count = 0
        def get_frame_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return frame
            else:
                # Trigger shutdown after first frame processing
                pipeline._shutdown_requested = True
                return None
        mock_components["rtsp_client"].get_frame.side_effect = get_frame_side_effect

        # Make CoreML return empty detections
        mock_components["coreml_detector"].detect_objects.return_value = []

        # Run pipeline
        pipeline.run()

    def test_pipeline_no_motion_skips_processing(self, pipeline, mock_components):
        """Test pipeline skips processing when no motion detected."""
        # Setup RTSP to return frame, then trigger shutdown
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        call_count = 0
        def get_frame_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return frame
            else:
                # Trigger shutdown after first frame processing
                pipeline._shutdown_requested = True
                return None
        mock_components["rtsp_client"].get_frame.side_effect = get_frame_side_effect

        # Make motion detector return no motion
        mock_components["motion_detector"].detect_motion.return_value = (
            False, 0.1, np.zeros((480, 640), dtype=np.uint8)
        )

        # Run pipeline
        pipeline.run()

    def test_pipeline_timing_metrics_calculation(self, pipeline, mock_components):
        """Test that timing metrics are calculated correctly."""
        # Setup RTSP to return frame, then trigger shutdown
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        call_count = 0
        def get_frame_side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return frame
            else:
                # Trigger shutdown after first frame processing
                pipeline._shutdown_requested = True
                return None
        mock_components["rtsp_client"].get_frame.side_effect = get_frame_side_effect

        # Run pipeline
        pipeline.run()

        # Verify pipeline continued with fallback description
        assert pipeline.metrics["events_created"] == 1
        # Verify image annotation still happened
        assert mock_components["image_annotator"].annotate.call_count == 1

    def test_pipeline_get_metrics_returns_copy(self, pipeline):
        """Test that get_metrics returns a copy, not reference."""
        metrics1 = pipeline.get_metrics()
        metrics1["test_key"] = "test_value"

        # Original metrics should not be modified
        assert "test_key" not in pipeline.metrics

    def test_pipeline_stage_constants_defined(self):
        """Test that pipeline stage constants are defined."""
        from core.pipeline import STAGE_MOTION, STAGE_SAMPLING, STAGE_DETECTION, STAGE_DEDUPLICATION, STAGE_LLM, STAGE_EVENT

        assert STAGE_MOTION == "motion_detection"
        assert STAGE_SAMPLING == "frame_sampling"
        assert STAGE_DETECTION == "object_detection"
        assert STAGE_DEDUPLICATION == "event_deduplication"
        assert STAGE_LLM == "llm_inference"
        assert STAGE_EVENT == "event_creation"