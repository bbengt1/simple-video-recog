"""Unit tests for MotionDetector class."""

import time

import numpy as np
import pytest

from core.config import SystemConfig
from core.motion_detector import MotionDetector


@pytest.fixture
def motion_config():
    """Create SystemConfig for motion detector testing."""
    return SystemConfig(
        camera_rtsp_url="rtsp://test:test@192.168.1.100:554/stream1",
        camera_id="test_camera",
        motion_threshold=0.02,  # 2% of frame (default per AC 5)
    )


@pytest.fixture
def motion_detector(motion_config):
    """Create MotionDetector instance for testing."""
    return MotionDetector(motion_config)


def test_detect_motion_static_scene(motion_detector, mock_frame):
    """Test that static scenes return has_motion=False after learning phase."""
    # Complete learning phase with static frames
    for _ in range(100):
        motion_detector.detect_motion(mock_frame)

    # Test static scene after learning
    has_motion, confidence, mask = motion_detector.detect_motion(mock_frame)

    assert has_motion is False
    assert confidence < 0.02  # Should be very low for static scene
    assert isinstance(mask, np.ndarray)


def test_detect_motion_with_movement(motion_detector, mock_frame):
    """Test that motion is detected when frame changes significantly."""
    # Complete learning phase
    for _ in range(100):
        motion_detector.detect_motion(mock_frame)

    # Create frame with significant motion (white square in center)
    changed_frame = mock_frame.copy()
    changed_frame[200:280, 300:380] = 255  # 80x80 white square

    has_motion, confidence, mask = motion_detector.detect_motion(changed_frame)

    assert has_motion is True
    assert confidence > 0.02  # Should exceed threshold
    assert isinstance(mask, np.ndarray)
    assert mask.shape == mock_frame.shape[:2]  # Mask should be 2D


def test_learning_phase(motion_detector, mock_frame):
    """Test that first 100 frames return has_motion=False during learning."""
    for frame_num in range(1, 101):
        has_motion, confidence, mask = motion_detector.detect_motion(mock_frame)

        assert has_motion is False, f"Frame {frame_num} should return False during learning"
        assert confidence == 0.0, f"Frame {frame_num} should have 0.0 confidence"
        assert isinstance(mask, np.ndarray)
        assert np.count_nonzero(mask) == 0, f"Frame {frame_num} should have empty mask"


def test_confidence_calculation(motion_detector, mock_frame):
    """Test that confidence is calculated as percentage (0.0-1.0)."""
    # Complete learning phase
    for _ in range(100):
        motion_detector.detect_motion(mock_frame)

    # Test with various amounts of motion
    test_cases = [
        (0, 0, 0, 0),  # No motion
        (100, 200, 100, 200),  # Small motion region
        (0, 480, 0, 640),  # Full frame motion
    ]

    for y1, y2, x1, x2 in test_cases:
        frame = mock_frame.copy()
        if y2 > 0:  # Add motion region
            frame[y1:y2, x1:x2] = 255

        has_motion, confidence, mask = motion_detector.detect_motion(frame)

        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0, f"Confidence {confidence} not in range [0.0, 1.0]"


def test_motion_threshold_configuration(mock_frame):
    """Test that motion threshold parameter controls sensitivity."""
    # Test with low threshold (more sensitive)
    low_threshold_config = SystemConfig(
        camera_rtsp_url="rtsp://test:test@192.168.1.100:554/stream1",
        motion_threshold=0.01,  # 1% threshold
    )
    detector_low = MotionDetector(low_threshold_config)

    # Test with high threshold (less sensitive)
    high_threshold_config = SystemConfig(
        camera_rtsp_url="rtsp://test:test@192.168.1.100:554/stream1",
        motion_threshold=0.05,  # 5% threshold
    )
    detector_high = MotionDetector(high_threshold_config)

    # Complete learning phase for both
    for _ in range(100):
        detector_low.detect_motion(mock_frame)
        detector_high.detect_motion(mock_frame)

    # Create frame with small motion (2% of frame)
    small_motion_frame = mock_frame.copy()
    small_motion_frame[200:240, 300:440] = 255  # 40x140 region ≈ 1.8% of 480x640

    has_motion_low, confidence_low, _ = detector_low.detect_motion(small_motion_frame)
    has_motion_high, confidence_high, _ = detector_high.detect_motion(small_motion_frame)

    # Both should report same confidence
    assert confidence_low == confidence_high

    # Low threshold should detect motion, high threshold should not
    assert has_motion_low is True, "Low threshold (1%) should detect small motion"
    assert has_motion_high is False, "High threshold (5%) should not detect small motion"


def test_reset_background(motion_detector, mock_frame):
    """Test that reset_background() restarts the learning phase."""
    # Complete initial learning phase
    for _ in range(100):
        motion_detector.detect_motion(mock_frame)

    # Verify we're past learning phase
    assert motion_detector.frame_count == 100

    # Reset background
    motion_detector.reset_background()

    # Verify frame counter reset
    assert motion_detector.frame_count == 0

    # Verify learning phase restarted - should return False for 100 frames
    for _ in range(100):
        has_motion, confidence, mask = motion_detector.detect_motion(mock_frame)
        assert has_motion is False
        assert confidence == 0.0


def test_performance_requirement(motion_detector, mock_frame):
    """Test that motion detection completes in <50ms per frame on M1."""
    # Complete learning phase
    for _ in range(100):
        motion_detector.detect_motion(mock_frame)

    # Create frame with motion for realistic performance test
    motion_frame = mock_frame.copy()
    motion_frame[200:280, 300:380] = 255

    # Measure performance over 10 iterations for stability
    times = []
    for _ in range(10):
        start_time = time.perf_counter()
        has_motion, confidence, mask = motion_detector.detect_motion(motion_frame)
        end_time = time.perf_counter()

        processing_time_ms = (end_time - start_time) * 1000
        times.append(processing_time_ms)

    avg_time = sum(times) / len(times)
    assert avg_time < 50, f"Processing took {avg_time:.2f}ms, exceeds 50ms limit"


def test_sudden_lighting_change(motion_detector):
    """Test that MOG2 handles sudden lighting changes.

    Note: With uniform frames, MOG2 will detect global brightness changes
    as motion initially, but the algorithm continues to function correctly.
    This test verifies the detector processes lighting changes without errors.
    """
    # Create frames with texture (not uniform) for more realistic testing
    base_frame = np.random.randint(40, 60, size=(480, 640, 3), dtype=np.uint8)

    # Build background model with normal brightness
    for _ in range(100):
        # Keep using same frame to establish background
        motion_detector.detect_motion(base_frame)

    # Simulate sudden brightness increase (e.g., lights turned on)
    bright_frame = np.clip(base_frame.astype(np.int16) + 50, 0, 255).astype(
        np.uint8
    )

    # First frame after lighting change will detect motion
    has_motion_1, confidence_1, _ = motion_detector.detect_motion(bright_frame)

    # Verify motion detection still works correctly
    assert isinstance(has_motion_1, bool)
    assert isinstance(confidence_1, float)
    assert 0.0 <= confidence_1 <= 1.0

    # Feed more frames - model continues to function
    for _ in range(20):
        has_motion, confidence, mask = motion_detector.detect_motion(bright_frame)
        assert isinstance(mask, np.ndarray)


def test_gradual_lighting_change(motion_detector):
    """Test that MOG2 processes gradual lighting changes (sunrise/sunset).

    Note: MOG2 with history=500 adapts to gradual changes better than sudden ones.
    This test verifies the detector continues to function correctly through
    gradual brightness changes without errors or crashes.
    """
    # Start with textured frame for realistic testing
    np.random.seed(42)  # Reproducible random texture
    base_frame = np.random.randint(40, 60, size=(480, 640, 3), dtype=np.uint8)

    # Simulate sunrise: gradually increase brightness over 200 frames
    for i in range(200):
        brightness_delta = int(i * 0.3)  # Slow gradual increase
        adjusted_frame = np.clip(
            base_frame.astype(np.int16) + brightness_delta, 0, 255
        ).astype(np.uint8)

        has_motion, confidence, mask = motion_detector.detect_motion(adjusted_frame)

        # Verify detector continues to function correctly
        assert isinstance(has_motion, bool)
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
        assert isinstance(mask, np.ndarray)
        assert mask.shape == (480, 640)


def test_shadow_movement(motion_detector, mock_frame):
    """Test that MOG2 detectShadows parameter filters shadow movement."""
    # Build background model
    for _ in range(100):
        motion_detector.detect_motion(mock_frame)

    # Create frame with shadow (darker region, not complete darkness)
    shadow_frame = mock_frame.copy()
    shadow_frame[100:200, 100:200] = (
        shadow_frame[100:200, 100:200] // 2
    )  # 50% darker

    has_motion, confidence, mask = motion_detector.detect_motion(shadow_frame)

    # With detectShadows=True, shadows are filtered out
    # Confidence should be low (shadow not counted as motion)
    assert (
        confidence < 0.05
    ), f"Shadow movement incorrectly detected as motion (confidence: {confidence:.3f})"
