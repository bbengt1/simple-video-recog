"""Integration tests for Event JSON serialization and end-to-end functionality."""

import json
import tempfile
from datetime import datetime, timezone

import pytest

from core.config import SystemConfig
from core.events import Event
from core.models import BoundingBox, DetectedObject


@pytest.fixture
def real_detection_result():
    """Create a realistic DetectionResult from actual object detection."""
    return {
        "objects": [
            DetectedObject(
                label="person",
                confidence=0.92,
                bbox=BoundingBox(x=120, y=50, width=180, height=320)
            ),
            DetectedObject(
                label="car",
                confidence=0.87,
                bbox=BoundingBox(x=300, y=100, width=200, height=150)
            )
        ],
        "inference_time": 0.05,
        "frame_shape": (480, 640, 3)
    }


@pytest.fixture
def real_ollama_description():
    """Simulate a realistic LLM-generated description."""
    return "A person in blue clothing is walking near a parked red sedan in the driveway during daytime."


@pytest.fixture
def system_config():
    """Create system configuration for testing."""
    return SystemConfig(
        camera_rtsp_url="rtsp://test:stream@localhost:8554/test",
        camera_id="front_door",
        ollama_base_url="http://localhost:11434",
        ollama_model="llava:7b",
        llm_timeout=10
    )


class TestEventJsonIntegration:
    """Integration tests for Event JSON functionality."""

    def test_create_event_from_detection_result(self, real_detection_result, real_ollama_description, system_config):
        """Test creating Event from real DetectionResult and LLM description."""
        # Simulate creating an event from pipeline results
        event = Event(
            event_id=Event.generate_event_id(),
            timestamp=datetime(2025, 11, 9, 14, 30, 0, tzinfo=timezone.utc),
            camera_id=system_config.camera_id,
            motion_confidence=0.85,
            detected_objects=real_detection_result["objects"],
            llm_description=real_ollama_description,
            image_path="data/events/2025-11-09/evt_test.jpg",
            json_log_path="data/events/2025-11-09/events.json",
            metadata={
                "coreml_inference_time": real_detection_result["inference_time"],
                "llm_inference_time": 2.1,
                "frame_number": 245,
                "motion_threshold_used": 0.15,
                "frame_shape": real_detection_result["frame_shape"]
            }
        )

        # Verify event structure
        assert event.camera_id == "front_door"
        assert len(event.detected_objects) == 2
        assert event.llm_description == real_ollama_description
        assert event.metadata["coreml_inference_time"] == 0.05
        assert event.metadata["frame_number"] == 245

    def test_event_json_schema_compliance(self, real_detection_result, real_ollama_description):
        """Test that Event JSON matches FR10 specification requirements."""
        event = Event(
            event_id="evt_1699540200000_test",
            timestamp=datetime(2025, 11, 9, 14, 30, 0, tzinfo=timezone.utc),
            camera_id="camera_1",
            motion_confidence=0.8,
            detected_objects=real_detection_result["objects"],
            llm_description=real_ollama_description,
            image_path="data/events/2025-11-09/evt_1699540200000_test.jpg",
            json_log_path="data/events/2025-11-09/events.json",
            metadata={
                "coreml_inference_time": 0.05,
                "llm_inference_time": 2.1,
                "frame_number": 245,
                "motion_threshold_used": 0.15
            }
        )

        json_str = event.to_json()
        parsed = json.loads(json_str)

        # FR10 Required fields
        required_fields = [
            "event_id", "timestamp", "camera_id", "detected_objects",
            "llm_description", "image_path", "metadata"
        ]

        for field in required_fields:
            assert field in parsed, f"Missing required field: {field}"

        # Timestamp should be ISO format
        assert "T" in parsed["timestamp"], "Timestamp should be ISO format"
        assert parsed["timestamp"].endswith("Z"), "Timestamp should end with Z for UTC"

        # Detected objects should have required fields
        for obj in parsed["detected_objects"]:
            assert "label" in obj, "Detected object missing label"
            assert "confidence" in obj, "Detected object missing confidence"
            assert "bbox" in obj, "Detected object missing bbox"
            assert isinstance(obj["confidence"], (int, float)), "Confidence should be numeric"

        # Metadata should contain inference timing
        assert "coreml_inference_time" in parsed["metadata"]
        assert "llm_inference_time" in parsed["metadata"]
        assert isinstance(parsed["metadata"]["coreml_inference_time"], (int, float))
        assert isinstance(parsed["metadata"]["llm_inference_time"], (int, float))

    def test_event_json_round_trip_with_file_storage(self, real_detection_result, real_ollama_description):
        """Test complete JSON round-trip including file storage simulation."""
        # Create event
        original_event = Event(
            event_id=Event.generate_event_id(),
            timestamp=datetime(2025, 11, 9, 15, 0, 0, tzinfo=timezone.utc),
            camera_id="backyard",
            motion_confidence=0.75,
            detected_objects=real_detection_result["objects"],
            llm_description=real_ollama_description,
            image_path="data/events/2025-11-09/test_event.jpg",
            json_log_path="data/events/2025-11-09/events.json",
            metadata={
                "coreml_inference_time": 0.04,
                "llm_inference_time": 1.8,
                "frame_number": 300,
                "motion_threshold_used": 0.12,
                "processing_pipeline_version": "2.7"
            }
        )

        # Serialize to JSON
        json_str = original_event.to_json()

        # Simulate writing to file (what would happen in production)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(json_str)
            temp_file = f.name

        # Simulate reading from file (what would happen when loading from database)
        with open(temp_file, 'r') as f:
            loaded_json_str = f.read()

        # Deserialize back to Event
        reconstructed_event = Event.from_json(loaded_json_str)

        # Verify complete fidelity
        assert reconstructed_event.event_id == original_event.event_id
        assert reconstructed_event.timestamp == original_event.timestamp
        assert reconstructed_event.camera_id == original_event.camera_id
        assert reconstructed_event.motion_confidence == original_event.motion_confidence
        assert reconstructed_event.llm_description == original_event.llm_description
        assert reconstructed_event.image_path == original_event.image_path
        assert reconstructed_event.metadata == original_event.metadata

        # Verify detected objects
        assert len(reconstructed_event.detected_objects) == len(original_event.detected_objects)
        for orig, recon in zip(original_event.detected_objects, reconstructed_event.detected_objects):
            assert recon.label == orig.label
            assert recon.confidence == orig.confidence
            assert recon.bbox.x == orig.bbox.x
            assert recon.bbox.y == orig.bbox.y
            assert recon.bbox.width == orig.bbox.width
            assert recon.bbox.height == orig.bbox.height

    def test_event_json_with_complex_metadata(self):
        """Test Event JSON with complex metadata structures."""
        complex_event = Event(
            event_id="evt_complex_test",
            timestamp=datetime(2025, 11, 9, 16, 0, 0, tzinfo=timezone.utc),
            camera_id="complex_camera",
            motion_confidence=0.8,
            llm_description="Complex scene description",
            image_path="data/events/2025-11-09/complex.jpg",
            json_log_path="data/events/2025-11-09/events.json",
            metadata={
                "performance": {
                    "coreml_fps": 18.5,
                    "total_processing_time": 2.8,
                    "memory_peak_mb": 245
                },
                "detection_stats": {
                    "total_objects": 3,
                    "high_confidence_objects": 2,
                    "filtered_objects": 1
                },
                "pipeline_info": {
                    "version": "2.7.0",
                    "modules_used": ["motion", "coreml", "ollama"],
                    "config_hash": "abc123def456"
                },
                "environmental_factors": {
                    "lighting_conditions": "daylight",
                    "weather": "clear",
                    "time_of_day": "afternoon"
                }
            }
        )

        # Test serialization
        json_str = complex_event.to_json()
        parsed = json.loads(json_str)

        # Verify complex metadata preserved
        assert parsed["metadata"]["performance"]["coreml_fps"] == 18.5
        assert parsed["metadata"]["detection_stats"]["total_objects"] == 3
        assert parsed["metadata"]["pipeline_info"]["version"] == "2.7.0"
        assert parsed["metadata"]["environmental_factors"]["lighting_conditions"] == "daylight"

        # Test round-trip
        reconstructed = Event.from_json(json_str)
        assert reconstructed.metadata == complex_event.metadata

    def test_event_json_error_handling(self):
        """Test JSON operations with error conditions."""
        # Test with invalid confidence value (should fail during Event creation)
        with pytest.raises(ValueError):
            Event(
                event_id="evt_test",
                timestamp=datetime(2025, 11, 9, 15, 0, 0, tzinfo=timezone.utc),
                camera_id="camera_1",
                motion_confidence=1.5,  # Invalid: should be <= 1.0
                llm_description="Test",
                image_path="test.jpg",
                json_log_path="data/events/2025-11-09/events.json"
            )

        # Test from_json with corrupted JSON
        corrupted_json = '{"event_id": "test", "timestamp": "2025-11-09T15:00:00Z"'  # Missing closing brace
        with pytest.raises(ValueError):
            Event.from_json(corrupted_json)

    def test_event_json_unicode_support(self):
        """Test JSON serialization with Unicode characters."""
        unicode_description = "Person detected with café au lait ☕ and naïve résumé 📄"

        event = Event(
            event_id="evt_unicode_test",
            timestamp=datetime(2025, 11, 9, 17, 0, 0, tzinfo=timezone.utc),
            camera_id="unicode_camera",
            motion_confidence=0.9,
            llm_description=unicode_description,
            image_path="data/events/2025-11-09/unicode.jpg",
            json_log_path="data/events/2025-11-09/events.json",
            metadata={"test": "unicode_support_✓"}
        )

        # Test serialization preserves Unicode
        json_str = event.to_json()
        assert "café" in json_str
        assert "☕" in json_str
        assert "✓" in json_str

        # Test round-trip preserves Unicode
        reconstructed = Event.from_json(json_str)
        assert reconstructed.llm_description == unicode_description
        assert reconstructed.metadata["test"] == "unicode_support_✓"
