"""Integration tests for event deduplication functionality.

Tests end-to-end deduplication behavior with simulated video processing
pipeline to ensure duplicate events are properly suppressed.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from core.config import SystemConfig
from core.events import EventDeduplicator
from core.models import BoundingBox, DetectedObject, DetectionResult


@pytest.fixture
def deduplication_config():
    """Create SystemConfig with deduplication window for testing."""
    return SystemConfig(
        camera_rtsp_url="rtsp://test:123@192.168.1.100:554/stream",
        deduplication_window=30  # Default window for realistic testing
    )


@pytest.fixture
def deduplicator(deduplication_config):
    """Create EventDeduplicator for integration testing."""
    return EventDeduplicator(deduplication_config)


@pytest.fixture
def person_detection():
    """Create DetectionResult with person detection."""
    return DetectionResult(
        objects=[
            DetectedObject(
                label="person",
                confidence=0.9,
                bbox=BoundingBox(x=100, y=50, width=200, height=300)
            )
        ],
        inference_time=0.05,
        frame_shape=(480, 640, 3)
    )


class TestEventDeduplicationIntegration:
    """Integration tests for event deduplication in processing context."""

    @patch('core.events.time.time')
    def test_continuous_person_detection_creates_single_event(
        self, mock_time, deduplicator, person_detection
    ):
        """Test that continuous person detection creates only one event."""
        # Simulate 10 seconds of video at 1 FPS (10 frames)
        # Person appears in all frames - should create only 1 event

        events_created = 0
        events_suppressed = 0

        for frame_num in range(10):
            # Advance time by 1 second per frame
            mock_time.return_value = float(frame_num)

            # Simulate motion detection triggering every frame
            # In real pipeline, this would be after motion detection + sampling
            should_create = deduplicator.should_create_event(person_detection)

            if should_create:
                events_created += 1
            else:
                events_suppressed += 1

        # Should create exactly 1 event, suppress 9
        assert events_created == 1
        assert events_suppressed == 9

        # Verify cache contains the person entry
        assert "person" in deduplicator._cache

    @patch('core.events.time.time')
    def test_person_detection_with_gaps_creates_multiple_events(
        self, mock_time, deduplicator, person_detection
    ):
        """Test that person detection with time gaps creates multiple events."""
        events_created = 0

        # Frame 1: Person detected (time = 0)
        mock_time.return_value = 0.0
        if deduplicator.should_create_event(person_detection):
            events_created += 1

        # Frames 2-5: Person still there but within window (times 1-4)
        for t in range(1, 5):
            mock_time.return_value = float(t)
            if deduplicator.should_create_event(person_detection):
                events_created += 1

        # Frame 6: Person detected after window expiry (time = 31 > 30)
        mock_time.return_value = 31.0
        if deduplicator.should_create_event(person_detection):
            events_created += 1

        # Should create 2 events (first and after window expiry)
        assert events_created == 2

    @patch('core.events.time.time')
    def test_multiple_different_objects_create_separate_events(
        self, mock_time, deduplicator
    ):
        """Test that different objects create separate events."""
        events_created = 0

        # Create detection results for different objects
        person_detection = DetectionResult(
            objects=[DetectedObject(label="person", confidence=0.9, bbox=BoundingBox(x=0, y=0, width=10, height=10))],
            inference_time=0.05,
            frame_shape=(480, 640, 3)
        )

        car_detection = DetectionResult(
            objects=[DetectedObject(label="car", confidence=0.9, bbox=BoundingBox(x=0, y=0, width=10, height=10))],
            inference_time=0.05,
            frame_shape=(480, 640, 3)
        )

        # Both detections at same time - should create separate events
        mock_time.return_value = 0.0

        if deduplicator.should_create_event(person_detection):
            events_created += 1

        if deduplicator.should_create_event(car_detection):
            events_created += 1

        # Should create 2 events for different objects
        assert events_created == 2
        assert "person" in deduplicator._cache
        assert "car" in deduplicator._cache

    @patch('core.events.time.time')
    def test_mixed_object_sequence_with_deduplication(
        self, mock_time, deduplicator
    ):
        """Test complex sequence with mixed objects and deduplication."""
        events_created = 0

        # Helper to create detection
        def create_detection(label, confidence=0.9):
            return DetectionResult(
                objects=[DetectedObject(label=label, confidence=confidence, bbox=BoundingBox(x=0, y=0, width=10, height=10))],
                inference_time=0.05,
                frame_shape=(480, 640, 3)
            )

        # Sequence: person, person, car, person, car
        sequence = [
            ("person", 0.0),
            ("person", 1.0),  # Should be suppressed
            ("car", 2.0),     # Different object - create event
            ("person", 3.0),  # Person again, but within window - suppress
            ("car", 4.0),     # Car again, within window - suppress
            ("person", 31.0), # Person after window expiry - create event
        ]

        for label, timestamp in sequence:
            mock_time.return_value = timestamp
            detection = create_detection(label)
            if deduplicator.should_create_event(detection):
                events_created += 1

        # Should create 3 events: person@0, car@2, person@31
        assert events_created == 3

    @patch('core.events.time.time')
    def test_cache_cleanup_integration(self, mock_time, deduplicator, person_detection):
        """Test that cache cleanup works in integration scenario."""
        # Initial detection
        mock_time.return_value = 0.0
        deduplicator.should_create_event(person_detection)

        # Verify person is in cache
        assert "person" in deduplicator._cache

        # Advance time beyond cleanup threshold (2x window = 60 seconds)
        mock_time.return_value = 61.0

        # New detection should trigger cleanup
        car_detection = DetectionResult(
            objects=[DetectedObject(label="car", confidence=0.9, bbox=BoundingBox(x=0, y=0, width=10, height=10))],
            inference_time=0.05,
            frame_shape=(480, 640, 3)
        )
        deduplicator.should_create_event(car_detection)

        # Person entry should be cleaned up
        assert "person" not in deduplicator._cache
        assert "car" in deduplicator._cache

    def test_deduplication_with_realistic_confidence_values(self, deduplicator):
        """Test deduplication with realistic confidence values."""
        # Create detections with varying confidence
        detections = [
            DetectionResult(
                objects=[DetectedObject(label="person", confidence=conf, bbox=BoundingBox(x=0, y=0, width=10, height=10))],
                inference_time=0.05,
                frame_shape=(480, 640, 3)
            )
            for conf in [0.95, 0.92, 0.88, 0.91]  # Realistic confidence range
        ]

        events_created = 0
        for detection in detections:
            if deduplicator.should_create_event(detection):
                events_created += 1

        # Should create only 1 event despite 4 detections
        assert events_created == 1