"""Integration tests for JSON event logger."""

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from core.config import SystemConfig
from core.events import Event
from core.json_logger import JSONEventLogger
from core.models import BoundingBox, DetectedObject


class TestJSONEventLoggerIntegration:
    """Integration tests for JSON event logger across multiple days."""

    @pytest.fixture
    def config(self) -> SystemConfig:
        """Create test configuration."""
        return SystemConfig(
            camera_rtsp_url="rtsp://test:12345@192.168.1.100:554/stream1", camera_id="test_camera"
        )

    @pytest.fixture
    def logger(self, config: SystemConfig) -> JSONEventLogger:
        """Create JSON event logger instance."""
        return JSONEventLogger(config)

    def create_test_event(self, event_id: str, timestamp: datetime) -> Event:
        """Create a test event with specified ID and timestamp."""
        return Event(
            event_id=event_id,
            timestamp=timestamp,
            camera_id="test_camera",
            llm_description=f"Test event {event_id}",
            image_path=f"data/events/{timestamp.date()}/{event_id}.jpg",
            json_log_path=f"data/events/{timestamp.date()}/events.json",
            detected_objects=[
                DetectedObject(
                    label="person",
                    confidence=0.85,
                    bbox=BoundingBox(x=100, y=200, width=150, height=300),
                )
            ],
        )

    def test_log_100_events_across_3_days(self, logger: JSONEventLogger) -> None:
        """Test logging 100 events across 3 consecutive days."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create events across 3 days
                base_date = datetime(2025, 11, 10, 12, 0, 0, tzinfo=timezone.utc)
                events_logged = 0

                for day_offset in range(3):  # 3 days
                    current_date = base_date + timedelta(days=day_offset)
                    events_per_day = 34 if day_offset < 2 else 32  # Total 100 events

                    for event_num in range(events_per_day):
                        event_id = "02d"
                        timestamp = current_date + timedelta(minutes=event_num)

                        event = self.create_test_event(event_id, timestamp)
                        result = logger.log_event(event)

                        assert result is True, f"Failed to log event {event_id}"
                        events_logged += 1

                assert events_logged == 100, f"Expected 100 events, logged {events_logged}"

                # Verify file structure
                events_dir = Path("data/events")
                assert events_dir.exists(), "Events directory should exist"

                # Check each day's directory and file
                for day_offset in range(3):
                    date_str = (base_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
                    date_dir = events_dir / date_str
                    json_file = date_dir / "events.json"

                    assert date_dir.exists(), f"Date directory {date_str} should exist"
                    assert json_file.exists(), f"JSON file for {date_str} should exist"

                    # Verify file is not empty
                    content = json_file.read_text()
                    assert len(content.strip()) > 0, f"JSON file for {date_str} should not be empty"

                    # Count JSON lines (should equal events per day)
                    lines = content.strip().split("\n")
                    expected_events = 34 if day_offset < 2 else 32
                    assert (
                        len(lines) == expected_events
                    ), f"Expected {expected_events} events in {date_str}, got {len(lines)}"

            finally:
                os.chdir(original_cwd)

    def test_json_file_format_validation(self, logger: JSONEventLogger) -> None:
        """Test that all logged events produce valid JSON Lines format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Log multiple events
                base_timestamp = datetime(2025, 11, 10, 12, 0, 0, tzinfo=timezone.utc)
                events_to_log = 10

                for i in range(events_to_log):
                    event_id = "02d"
                    timestamp = base_timestamp + timedelta(minutes=i)
                    event = self.create_test_event(event_id, timestamp)

                    result = logger.log_event(event)
                    assert result is True

                # Read and validate the JSON file
                json_file = Path("data/events/2025-11-10/events.json")
                assert json_file.exists()

                content = json_file.read_text()
                lines = content.strip().split("\n")

                assert len(lines) == events_to_log

                # Validate each line is valid JSON
                for i, line in enumerate(lines):
                    assert len(line.strip()) > 0, f"Line {i} should not be empty"

                    try:
                        parsed = json.loads(line)
                        assert isinstance(parsed, dict), f"Line {i} should parse to a dictionary"

                        # Verify required fields
                        required_fields = [
                            "event_id",
                            "timestamp",
                            "camera_id",
                            "llm_description",
                            "detected_objects",
                        ]
                        for field in required_fields:
                            assert field in parsed, f"Line {i} missing required field: {field}"

                        # Verify event_id matches expected pattern
                        expected_id = "02d"
                        assert parsed["event_id"] == expected_id, f"Line {i} event_id mismatch"

                    except json.JSONDecodeError as e:
                        pytest.fail(f"Line {i} is not valid JSON: {e}")

            finally:
                os.chdir(original_cwd)

    def test_file_rotation_at_midnight(self, logger: JSONEventLogger) -> None:
        """Test that events are correctly separated into different files at midnight."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create events just before and after midnight
                day1_timestamp = datetime(2025, 11, 10, 23, 59, 0, tzinfo=timezone.utc)
                day2_timestamp = datetime(2025, 11, 11, 0, 1, 0, tzinfo=timezone.utc)

                # Log event on day 1
                event1 = self.create_test_event("evt_day1", day1_timestamp)
                result1 = logger.log_event(event1)
                assert result1 is True

                # Log event on day 2
                event2 = self.create_test_event("evt_day2", day2_timestamp)
                result2 = logger.log_event(event2)
                assert result2 is True

                # Verify separate files were created
                day1_file = Path("data/events/2025-11-10/events.json")
                day2_file = Path("data/events/2025-11-11/events.json")

                assert day1_file.exists(), "Day 1 file should exist"
                assert day2_file.exists(), "Day 2 file should exist"

                # Verify each file contains exactly one event
                day1_content = day1_file.read_text().strip()
                day2_content = day2_file.read_text().strip()

                day1_lines = day1_content.split("\n")
                day2_lines = day2_content.split("\n")

                assert len(day1_lines) == 1, "Day 1 file should contain exactly 1 event"
                assert len(day2_lines) == 1, "Day 2 file should contain exactly 1 event"

                # Verify correct events in correct files
                day1_json = json.loads(day1_lines[0])
                day2_json = json.loads(day2_lines[0])

                assert day1_json["event_id"] == "evt_day1"
                assert day2_json["event_id"] == "evt_day2"

            finally:
                os.chdir(original_cwd)

    def test_atomic_write_integrity(self, logger: JSONEventLogger) -> None:
        """Test that atomic writes maintain file integrity."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Log multiple events to same file
                base_timestamp = datetime(2025, 11, 10, 12, 0, 0, tzinfo=timezone.utc)
                events_to_log = 5

                for i in range(events_to_log):
                    event_id = "02d"
                    timestamp = base_timestamp + timedelta(minutes=i)
                    event = self.create_test_event(event_id, timestamp)

                    result = logger.log_event(event)
                    assert result is True

                # Verify final file contains all events
                json_file = Path("data/events/2025-11-10/events.json")
                assert json_file.exists()

                content = json_file.read_text()
                lines = content.strip().split("\n")

                assert (
                    len(lines) == events_to_log
                ), f"Expected {events_to_log} events, got {len(lines)}"

                # Verify all events are valid and in order
                for i, line in enumerate(lines):
                    parsed = json.loads(line)
                    expected_id = "02d"
                    assert parsed["event_id"] == expected_id, f"Event {i} ID mismatch"

                # Verify no temporary files remain
                temp_files = list(Path("data/events/2025-11-10").glob("*.tmp"))
                assert len(temp_files) == 0, f"Temporary files found: {temp_files}"

            finally:
                os.chdir(original_cwd)
