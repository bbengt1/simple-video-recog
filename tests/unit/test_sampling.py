"""Unit tests for FrameSampler class."""

import pytest

from core.config import SystemConfig
from core.pipeline import FrameSampler


@pytest.fixture
def sampling_config():
    """Create SystemConfig for frame sampling testing."""
    return SystemConfig(
        camera_rtsp_url="rtsp://test:test@192.168.1.100:554/stream1",
        camera_id="test_camera",
        frame_sample_rate=10,  # Sample every 10th frame
    )


@pytest.fixture
def frame_sampler(sampling_config):
    """Create FrameSampler instance for testing."""
    return FrameSampler(sampling_config)


def test_sampling_rate_1_processes_all_frames():
    """Test that sampling rate of 1 processes every frame."""
    config = SystemConfig(
        camera_rtsp_url="rtsp://test:test@192.168.1.100:554/stream1",
        frame_sample_rate=1,
    )
    sampler = FrameSampler(config)

    for frame_count in range(1, 21):  # Test 20 frames
        should_process = sampler.should_process(frame_count)
        assert should_process is True, f"Frame {frame_count} should be processed with rate=1"


def test_sampling_rate_10_processes_every_10th_frame(frame_sampler):
    """Test that sampling rate of 10 processes every 10th frame."""
    expected_frames = [10, 20, 30, 40, 50]  # Frames that should be processed

    for frame_count in range(1, 51):  # Test 50 frames
        should_process = frame_sampler.should_process(frame_count)
        if frame_count in expected_frames:
            assert should_process is True, f"Frame {frame_count} should be processed"
        else:
            assert should_process is False, f"Frame {frame_count} should not be processed"


def test_sampling_rate_30_processes_every_30th_frame():
    """Test that sampling rate of 30 processes every 30th frame."""
    config = SystemConfig(
        camera_rtsp_url="rtsp://test:test@192.168.1.100:554/stream1",
        frame_sample_rate=30,
    )
    sampler = FrameSampler(config)

    expected_frames = [30, 60, 90, 120, 150]

    for frame_count in range(1, 151):  # Test 150 frames
        should_process = sampler.should_process(frame_count)
        if frame_count in expected_frames:
            assert should_process is True, f"Frame {frame_count} should be processed"
        else:
            assert should_process is False, f"Frame {frame_count} should not be processed"


def test_sampling_rate_5_processes_correct_frames():
    """Test that sampling rate of 5 processes frames 5, 10, 15, 20, etc."""
    config = SystemConfig(
        camera_rtsp_url="rtsp://test:test@192.168.1.100:554/stream1",
        frame_sample_rate=5,
    )
    sampler = FrameSampler(config)

    expected_frames = [5, 10, 15, 20, 25, 30]

    for frame_count in range(1, 31):  # Test 30 frames
        should_process = sampler.should_process(frame_count)
        if frame_count in expected_frames:
            assert should_process is True, f"Frame {frame_count} should be processed"
        else:
            assert should_process is False, f"Frame {frame_count} should not be processed"


def test_frame_count_starts_from_1():
    """Test that frame counting starts from 1 (not 0)."""
    config = SystemConfig(
        camera_rtsp_url="rtsp://test:test@192.168.1.100:554/stream1",
        frame_sample_rate=5,
    )
    sampler = FrameSampler(config)

    # Frame 1 should be processed (1 % 5 == 1, not 0)
    assert sampler.should_process(1) is False, "Frame 1 should not be processed with rate=5"
    assert sampler.should_process(5) is True, "Frame 5 should be processed with rate=5"
    assert sampler.should_process(6) is False, "Frame 6 should not be processed with rate=5"


def test_different_sampling_rates():
    """Test various sampling rates work correctly."""
    test_cases = [
        (1, list(range(1, 26))),  # Process all frames 1-25
        (2, [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24]),  # Process even frames
        (3, [3, 6, 9, 12, 15, 18, 21, 24]),  # Process every 3rd frame
        (5, [5, 10, 15, 20, 25]),  # Process every 5th frame
    ]

    for rate, expected_frames in test_cases:
        config = SystemConfig(
            camera_rtsp_url="rtsp://test:test@192.168.1.100:554/stream1",
            frame_sample_rate=rate,
        )
        sampler = FrameSampler(config)

        for frame_count in range(1, 26):  # Test 25 frames
            should_process = sampler.should_process(frame_count)
            if frame_count in expected_frames:
                assert should_process is True, f"Rate {rate}: Frame {frame_count} should be processed"
            else:
                assert should_process is False, f"Rate {rate}: Frame {frame_count} should not be processed"


def test_frame_sampler_initialization(sampling_config):
    """Test that FrameSampler initializes correctly with config."""
    sampler = FrameSampler(sampling_config)

    # Verify the sampling rate is set from config
    assert sampler.frame_sample_rate == 10

    # Test that it processes the correct frames
    assert sampler.should_process(10) is True
    assert sampler.should_process(11) is False
    assert sampler.should_process(20) is True


def test_frame_sampler_with_different_configs():
    """Test FrameSampler with different configuration values."""
    configs_and_expectations = [
        (1, list(range(1, 51))),  # Rate 1: all frames 1-50
        (2, [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50]),  # Rate 2: even frames
        (10, [10, 20, 30, 40, 50]),  # Rate 10: every 10th
    ]

    for rate, expected_frames in configs_and_expectations:
        config = SystemConfig(
            camera_rtsp_url="rtsp://test:test@192.168.1.100:554/stream1",
            frame_sample_rate=rate,
        )
        sampler = FrameSampler(config)

        for frame_count in range(1, 51):  # Test 50 frames
            should_process = sampler.should_process(frame_count)
            if frame_count in expected_frames:
                assert should_process is True, f"Rate {rate}: Frame {frame_count} should be processed"
            else:
                assert should_process is False, f"Rate {rate}: Frame {frame_count} should not be processed"