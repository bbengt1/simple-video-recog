"""Unit tests for Event model and JSON operations."""

import json
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from core.config import SystemConfig
from core.events import Event, EventDeduplicator
from core.models import BoundingBox, DetectedObject, DetectionResult


@pytest.fixture
def sample_detected_object():
    """Create sample DetectedObject for testing."""
    return DetectedObject(
        label="person",
        confidence=0.92,
        bbox=BoundingBox(x=120, y=50, width=180, height=320)
    )


@pytest.fixture
def sample_event(sample_detected_object):
    """Create sample Event for testing."""
    return Event(
        event_id="evt_1699459335_a7b3c",
        timestamp=datetime(2025, 11, 8, 14, 32, 15, tzinfo=timezone.utc),
        camera_id="camera_1",
        motion_confidence=0.87,
        detected_objects=[sample_detected_object],
        llm_description="Person in blue shirt carrying brown package approaching front door",
        image_path="data/events/2025-11-08/evt_1699459335_a7b3c.jpg",
        json_log_path="data/events/2025-11-08/events.json",
        metadata={
            "coreml_inference_time": 0.05,
            "llm_inference_time": 2.34,
            "frame_number": 150,
            "motion_threshold_used": 0.15
        }
    )


class TestEventModel:
    """Test cases for Event model functionality."""

    def test_event_creation_with_all_fields(self, sample_event):
        """Test Event creation with all required fields."""
        assert sample_event.event_id == "evt_1699459335_a7b3c"
        assert sample_event.camera_id == "camera_1"
        assert sample_event.motion_confidence == 0.87
        assert len(sample_event.detected_objects) == 1
        assert sample_event.llm_description == "Person in blue shirt carrying brown package approaching front door"
        assert sample_event.image_path == "data/events/2025-11-08/evt_1699459335_a7b3c.jpg"
        assert sample_event.metadata["coreml_inference_time"] == 0.05

    def test_event_creation_minimal_fields(self):
        """Test Event creation with minimal required fields."""
        event = Event(
            event_id="evt_test",
            timestamp=datetime(2025, 11, 8, 12, 0, 0, tzinfo=timezone.utc),
            camera_id="camera_1",
            llm_description="Test description",
            image_path="test.jpg",
            json_log_path="test.json"
        )

        assert event.event_id == "evt_test"
        assert event.detected_objects == []  # default empty list
        assert event.metadata == {}  # default empty dict
        assert event.motion_confidence is None  # optional field

        assert event.event_id == "evt_test"
        assert event.detected_objects == []  # default empty list
        assert event.metadata == {}  # default empty dict
        assert event.motion_confidence is None  # optional field

    def test_event_validation_confidence_range(self):
        """Test validation of motion_confidence range."""
        # Valid confidence
        Event(
            event_id="evt_test",
            timestamp=datetime(2025, 11, 8, 12, 0, 0, tzinfo=timezone.utc),
            camera_id="camera_1",
            motion_confidence=0.5,
            llm_description="Test",
            image_path="test.jpg",
            json_log_path="test.json"
        )

        # Invalid confidence - too low
        with pytest.raises(ValueError):
            Event(
                event_id="evt_test",
                timestamp=datetime(2025, 11, 8, 12, 0, 0, tzinfo=timezone.utc),
                camera_id="camera_1",
                motion_confidence=-0.1,
                llm_description="Test",
                image_path="test.jpg",
                json_log_path="test.json"
            )

        # Invalid confidence - too high
        with pytest.raises(ValueError):
            Event(
                event_id="evt_test",
                timestamp=datetime(2025, 11, 8, 12, 0, 0, tzinfo=timezone.utc),
                camera_id="camera_1",
                motion_confidence=1.5,
                llm_description="Test",
                image_path="test.jpg",
                json_log_path="test.json"
            )


class TestEventIdGeneration:
    """Test cases for event ID generation."""

    @patch('core.events.time.time')
    @patch('core.events.secrets.token_hex')
    def test_generate_event_id_format(self, mock_token_hex, mock_time):
        """Test event ID generation format."""
        mock_time.return_value = 1699459335.123  # Fixed timestamp
        mock_token_hex.return_value = "a7b3c"     # Fixed random suffix

        event_id = Event.generate_event_id()
        expected = "evt_1699459335123_a7b3c"

        assert event_id == expected
        assert event_id.startswith("evt_")
        assert "_a7b3c" in event_id

    @patch('core.events.time.time')
    @patch('core.events.secrets.token_hex')
    def test_generate_event_id_uniqueness(self, mock_token_hex, mock_time):
        """Test that generated IDs are unique."""
        # Simulate different timestamps and random values
        call_count = 0

        def time_side_effect():
            nonlocal call_count
            call_count += 1
            return 1699459335.0 + call_count * 0.001

        def token_side_effect(length):
            return f"test{call_count:04x}"

        mock_time.side_effect = time_side_effect
        mock_token_hex.side_effect = token_side_effect

        ids = set()
        for i in range(5):
            event_id = Event.generate_event_id()
            assert event_id not in ids, f"Duplicate ID generated: {event_id}"
            ids.add(event_id)

        assert len(ids) == 5


class TestEventJsonSerialization:
    """Test cases for JSON serialization and deserialization."""

    def test_to_json_basic(self, sample_event):
        """Test basic JSON serialization."""
        json_str = sample_event.to_json()

        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["event_id"] == "evt_1699459335_a7b3c"
        assert parsed["camera_id"] == "camera_1"
        assert parsed["llm_description"] == "Person in blue shirt carrying brown package approaching front door"

    def test_to_json_datetime_format(self, sample_event):
        """Test that datetime is serialized in ISO format."""
        json_str = sample_event.to_json()
        parsed = json.loads(json_str)

        # Should be ISO format with Z suffix for UTC
        assert parsed["timestamp"] == "2025-11-08T14:32:15Z"

    def test_to_json_nested_objects(self, sample_event):
        """Test serialization of nested DetectedObject."""
        json_str = sample_event.to_json()
        parsed = json.loads(json_str)

        detected_obj = parsed["detected_objects"][0]
        assert detected_obj["label"] == "person"
        assert detected_obj["confidence"] == 0.92
        assert detected_obj["bbox"]["x"] == 120
        assert detected_obj["bbox"]["y"] == 50

    def test_from_json_round_trip(self, sample_event):
        """Test JSON serialization and deserialization round-trip."""
        # Serialize to JSON
        json_str = sample_event.to_json()

        # Deserialize back to Event
        reconstructed = Event.from_json(json_str)

        # Verify all fields match
        assert reconstructed.event_id == sample_event.event_id
        assert reconstructed.timestamp == sample_event.timestamp
        assert reconstructed.camera_id == sample_event.camera_id
        assert reconstructed.motion_confidence == sample_event.motion_confidence
        assert reconstructed.llm_description == sample_event.llm_description
        assert reconstructed.image_path == sample_event.image_path
        assert reconstructed.metadata == sample_event.metadata

        # Verify nested objects
        assert len(reconstructed.detected_objects) == 1
        orig_obj = sample_event.detected_objects[0]
        recon_obj = reconstructed.detected_objects[0]
        assert recon_obj.label == orig_obj.label
        assert recon_obj.confidence == orig_obj.confidence
        assert recon_obj.bbox.x == orig_obj.bbox.x

    def test_from_json_invalid_json(self):
        """Test from_json with invalid JSON."""
        with pytest.raises(ValueError):
            Event.from_json("invalid json")

    def test_from_json_missing_required_field(self):
        """Test from_json with missing required field."""
        invalid_json = json.dumps({
            "timestamp": "2025-11-08T14:32:15Z",
            "camera_id": "camera_1",
            "llm_description": "Test",
            "image_path": "test.jpg"
            # Missing event_id
        })

        with pytest.raises(ValueError):
            Event.from_json(invalid_json)


class TestEventMetadata:
    """Test cases for Event metadata handling."""

    def test_metadata_empty_by_default(self):
        """Test that metadata defaults to empty dict."""
        event = Event(
            event_id="evt_test",
            timestamp=datetime(2025, 11, 8, 12, 0, 0, tzinfo=timezone.utc),
            camera_id="camera_1",
            llm_description="Test",
            image_path="test.jpg",
            json_log_path="test.json"
        )

        assert event.metadata == {}

    def test_metadata_complex_structure(self):
        """Test metadata with complex nested structure."""
        complex_metadata = {
            "inference_times": {
                "coreml": 0.05,
                "llm": 2.34
            },
            "frame_info": {
                "number": 150,
                "dimensions": [640, 480]
            },
            "processing_flags": ["motion_detected", "objects_filtered"]
        }

        event = Event(
            event_id="evt_test",
            timestamp=datetime(2025, 11, 8, 12, 0, 0, tzinfo=timezone.utc),
            camera_id="camera_1",
            llm_description="Test",
            image_path="test.jpg",
            json_log_path="test.json",
            metadata=complex_metadata
        )

        assert event.metadata == complex_metadata

        # Test JSON round-trip preserves complex metadata
        json_str = event.to_json()
        reconstructed = Event.from_json(json_str)
        assert reconstructed.metadata == complex_metadata


@pytest.fixture
def deduplicator_config():
    """Create SystemConfig for EventDeduplicator testing."""
    return SystemConfig(
        camera_rtsp_url="rtsp://test:123@192.168.1.100:554/stream",
        deduplication_window=30
    )


@pytest.fixture
def deduplicator(deduplicator_config):
    """Create EventDeduplicator instance for testing."""
    return EventDeduplicator(deduplicator_config)


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


@pytest.fixture
def multiple_objects_detection():
    """Create DetectionResult with multiple objects."""
    return DetectionResult(
        objects=[
            DetectedObject(
                label="person",
                confidence=0.8,
                bbox=BoundingBox(x=100, y=50, width=200, height=300)
            ),
            DetectedObject(
                label="car",
                confidence=0.95,
                bbox=BoundingBox(x=50, y=100, width=300, height=150)
            )
        ],
        inference_time=0.05,
        frame_shape=(480, 640, 3)
    )


@pytest.fixture
def empty_detection():
    """Create DetectionResult with no objects."""
    return DetectionResult(
        objects=[],
        inference_time=0.05,
        frame_shape=(480, 640, 3)
    )


class TestEventDeduplicator:
    """Test cases for EventDeduplicator functionality."""

    def test_init_with_config(self, deduplicator_config):
        """Test EventDeduplicator initialization."""
        deduplicator = EventDeduplicator(deduplicator_config)

        assert deduplicator.deduplication_window == 30
        assert deduplicator._cache == {}
        assert hasattr(deduplicator, 'logger')

    def test_should_create_event_empty_detections(self, deduplicator, empty_detection):
        """Test should_create_event returns False for empty detections."""
        result = deduplicator.should_create_event(empty_detection)

        assert result is False
        assert deduplicator._cache == {}  # Cache should remain empty

    def test_should_create_event_first_detection(self, deduplicator, person_detection):
        """Test should_create_event returns True for first detection."""
        result = deduplicator.should_create_event(person_detection)

        assert result is True
        assert "person" in deduplicator._cache
        assert isinstance(deduplicator._cache["person"], float)

    def test_should_create_event_duplicate_within_window(self, deduplicator, person_detection):
        """Test should_create_event suppresses duplicate within window."""
        # First detection - should create event
        result1 = deduplicator.should_create_event(person_detection)
        assert result1 is True

        # Second detection immediately after - should be suppressed
        result2 = deduplicator.should_create_event(person_detection)
        assert result2 is False

    @patch('core.events.time.time')
    def test_should_create_event_window_expiry(self, mock_time, deduplicator, person_detection):
        """Test should_create_event allows event after window expiry."""
        # Set initial time
        mock_time.return_value = 1000.0

        # First detection
        result1 = deduplicator.should_create_event(person_detection)
        assert result1 is True

        # Advance time beyond window (31 seconds later)
        mock_time.return_value = 1031.0

        # Second detection - should create event (window expired)
        result2 = deduplicator.should_create_event(person_detection)
        assert result2 is True

    @patch('core.events.time.time')
    def test_should_create_event_multiple_objects_uses_highest_confidence(
        self, mock_time, deduplicator, multiple_objects_detection
    ):
        """Test that highest confidence object is used as primary key."""
        mock_time.return_value = 1000.0

        # Detection has person (0.8) and car (0.95) - car should be primary
        result = deduplicator.should_create_event(multiple_objects_detection)
        assert result is True
        assert "car" in deduplicator._cache  # Highest confidence object
        assert "person" not in deduplicator._cache

    @patch('core.events.time.time')
    def test_should_create_event_different_objects_allowed(self, mock_time, deduplicator):
        """Test that different objects are not deduplicated."""
        mock_time.return_value = 1000.0

        # First detection - person
        person_detection = DetectionResult(
            objects=[DetectedObject(label="person", confidence=0.9, bbox=BoundingBox(x=0, y=0, width=10, height=10))],
            inference_time=0.05,
            frame_shape=(480, 640, 3)
        )
        result1 = deduplicator.should_create_event(person_detection)
        assert result1 is True

        # Second detection - car (different object)
        car_detection = DetectionResult(
            objects=[DetectedObject(label="car", confidence=0.9, bbox=BoundingBox(x=0, y=0, width=10, height=10))],
            inference_time=0.05,
            frame_shape=(480, 640, 3)
        )
        result2 = deduplicator.should_create_event(car_detection)
        assert result2 is True  # Should allow different object

        assert "person" in deduplicator._cache
        assert "car" in deduplicator._cache

    @patch('core.events.time.time')
    def test_cache_cleanup_removes_expired_entries(self, mock_time, deduplicator, person_detection):
        """Test that cache cleanup removes old entries."""
        # Initial detection
        mock_time.return_value = 1000.0
        deduplicator.should_create_event(person_detection)

        # Advance time beyond cleanup threshold (2x window = 60 seconds)
        mock_time.return_value = 1061.0

        # New detection should trigger cleanup
        car_detection = DetectionResult(
            objects=[DetectedObject(label="car", confidence=0.9, bbox=BoundingBox(x=0, y=0, width=10, height=10))],
            inference_time=0.05,
            frame_shape=(480, 640, 3)
        )
        deduplicator.should_create_event(car_detection)

        # Person entry should be cleaned up (older than 60 seconds)
        assert "person" not in deduplicator._cache
        assert "car" in deduplicator._cache

    def test_deduplication_window_configuration(self):
        """Test that deduplication window is read from config."""
        # Short window
        config_short = SystemConfig(
            camera_rtsp_url="rtsp://test:123@192.168.1.100:554/stream",
            deduplication_window=5
        )
        deduplicator_short = EventDeduplicator(config_short)
        assert deduplicator_short.deduplication_window == 5

        # Long window
        config_long = SystemConfig(
            camera_rtsp_url="rtsp://test:123@192.168.1.100:554/stream",
            deduplication_window=300
        )
        deduplicator_long = EventDeduplicator(config_long)
        assert deduplicator_long.deduplication_window == 300
