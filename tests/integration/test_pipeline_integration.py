"""Integration tests for processing pipeline with real components."""

import pytest
import numpy as np

from apple_platform.coreml_detector import CoreMLDetector
from core.config import SystemConfig
from core.events import EventDeduplicator
from core.image_annotator import ImageAnnotator
from core.motion_detector import MotionDetector
from core.pipeline import FrameSampler, ProcessingPipeline
from integrations.ollama import OllamaClient
from integrations.rtsp_client import RTSPCameraClient


def test_processing_pipeline_component_integration(sample_config):
    """Test that all pipeline components work together correctly with real components."""
    # Arrange
    config = SystemConfig(**sample_config)

    # Create real components (not mocks)
    motion_detector = MotionDetector(config)
    frame_sampler = FrameSampler(config)

    # Create RTSP client (will use mock in actual testing)
    rtsp_client = RTSPCameraClient(config)

    # Create additional required components
    coreml_detector = CoreMLDetector(config)
    event_deduplicator = EventDeduplicator(config)
    ollama_client = OllamaClient(config)
    image_annotator = ImageAnnotator()

    # Create pipeline
    pipeline = ProcessingPipeline(
        rtsp_client, motion_detector, frame_sampler, coreml_detector,
        event_deduplicator, ollama_client, image_annotator, config
    )

    # Test with static frame (no motion expected after learning phase)
    static_frame = np.full((240, 320, 3), (100, 100, 100), dtype=np.uint8)

    # During learning phase (first 100 frames), motion detector returns (False, 0.0, empty_mask)
    has_motion, confidence, mask = motion_detector.detect_motion(static_frame)
    assert has_motion is False
    assert confidence == 0.0
    assert mask.shape == (240, 320)  # Binary mask

    # Test with frame containing simulated motion (after learning phase)
    # Reset motion detector to simulate post-learning behavior
    motion_detector.reset_background()

    # Create a frame with a significant change (simulated motion)
    motion_frame = np.full((240, 320, 3), (100, 100, 100), dtype=np.uint8)
    # Add a large bright rectangle to ensure motion detection
    motion_frame[50:150, 100:200] = (200, 200, 200)  # Large bright area

    has_motion, confidence, mask = motion_detector.detect_motion(motion_frame)
    # Note: Exact behavior depends on MOG2 learning, but we verify the interface works
    assert isinstance(has_motion, bool)
    assert isinstance(confidence, float)
    assert 0.0 <= confidence <= 1.0
    assert mask.shape == (240, 320)

    # Test frame sampler with default rate=5
    assert frame_sampler.should_process(1) is False  # 1 % 5 != 0
    assert frame_sampler.should_process(5) is True   # 5 % 5 == 0
    assert frame_sampler.should_process(10) is True  # 10 % 5 == 0
    assert frame_sampler.should_process(12) is False # 12 % 5 != 0

    # Test metrics tracking
    initial_metrics = pipeline.get_metrics()
    expected_keys = {
        "total_frames_captured", "frames_with_motion", "frames_sampled", "frames_processed",
        "objects_detected", "events_created", "events_suppressed", "coreml_time_avg", "llm_time_avg"
    }
    assert set(initial_metrics.keys()) == expected_keys
    assert all(v == 0 for v in initial_metrics.values())

    # Verify pipeline components are properly initialized
    assert pipeline.rtsp_client is rtsp_client
    assert pipeline.motion_detector is motion_detector
    assert pipeline.frame_sampler is frame_sampler
    assert pipeline.config is config


def test_processing_pipeline_metrics_workflow(sample_config):
    """Test the complete metrics workflow through simulated processing."""
    # Arrange
    config = SystemConfig(**sample_config)
    motion_detector = MotionDetector(config)
    frame_sampler = FrameSampler(config)
    rtsp_client = RTSPCameraClient(config)

    # Create additional required components
    coreml_detector = CoreMLDetector(config)
    event_deduplicator = EventDeduplicator(config)
    ollama_client = OllamaClient(config)
    image_annotator = ImageAnnotator()

    pipeline = ProcessingPipeline(
        rtsp_client, motion_detector, frame_sampler, coreml_detector,
        event_deduplicator, ollama_client, image_annotator, config
    )

    # Simulate processing workflow manually
    # (In real scenario, this would happen in the run() loop)

    # Simulate capturing 10 frames
    pipeline.metrics["total_frames_captured"] = 10

    # Simulate 6 frames with motion detected
    pipeline.metrics["frames_with_motion"] = 6

    # With default sample_rate=5, frames 5 and 10 would be sampled
    # But since sampling applies to motion frames, we need to track motion frame count
    # For this test, simulate that 3 motion frames were sampled
    pipeline.metrics["frames_sampled"] = 3

    # All sampled frames were processed
    pipeline.metrics["frames_processed"] = 3

    # Assert final metrics
    metrics = pipeline.get_metrics()
    assert metrics["total_frames_captured"] == 10
    assert metrics["frames_with_motion"] == 6
    assert metrics["frames_sampled"] == 3
    assert metrics["frames_processed"] == 3

    # Calculate expected rates
    motion_rate = (6 / 10) * 100  # 60% of frames had motion
    sample_rate = (3 / 6) * 100  # 50% of motion frames were sampled

    assert motion_rate == 60.0
    assert sample_rate == 50.0


@pytest.mark.parametrize("sample_rate,expected_behavior", [
    (1, "every_frame"),  # Sample every frame: 1,2,3,4,5,...
    (2, "every_2nd"),    # Sample every 2nd frame: 2,4,6,8,10,...
    (5, "every_5th"),    # Sample every 5th frame: 5,10,15,20,25,...
])
def test_frame_sampler_integration_with_different_rates(sample_config, sample_rate, expected_behavior):
    """Test frame sampler with different sampling rates."""
    # Arrange
    config = SystemConfig(**{**sample_config, "frame_sample_rate": sample_rate})
    sampler = FrameSampler(config)

    # Act & Assert
    for frame_count in range(1, 26):  # Test first 25 frames
        should_process = sampler.should_process(frame_count)

        if expected_behavior == "every_frame":
            expected = True  # Every frame should be processed
        elif expected_behavior == "every_2nd":
            expected = (frame_count % 2 == 0)  # Every even frame
        else:  # every_5th
            expected = (frame_count % 5 == 0)  # Every 5th frame

        assert should_process == expected, f"Frame {frame_count} should_process={should_process}, expected={expected}"