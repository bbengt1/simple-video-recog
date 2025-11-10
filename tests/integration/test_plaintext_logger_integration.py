"""Integration tests for plaintext event logger."""

import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from core.config import SystemConfig
from core.events import Event
from core.models import BoundingBox, DetectedObject
from core.plaintext_logger import PlaintextEventLogger


class TestPlaintextEventLoggerIntegration:
    """Integration tests for plaintext event logger across multiple days."""

    @pytest.fixture
    def config(self) -> SystemConfig:
        """Create test configuration."""
        return SystemConfig(
            camera_rtsp_url="rtsp://test:12345@192.168.1.100:554/stream1",
            camera_id="test_camera"
        )

    @pytest.fixture
    def logger(self, config: SystemConfig) -> PlaintextEventLogger:
        """Create plaintext event logger instance."""
        return PlaintextEventLogger(config)

    def create_test_event(self, event_id: str, timestamp: datetime, description: str | None = None) -> Event:
        """Create a test event with specified ID and timestamp."""
        if description is None:
            description = f"Test event {event_id}"

        return Event(
            event_id=event_id,
            timestamp=timestamp,
            camera_id="test_camera",
            llm_description=description,
            image_path=f"data/events/{timestamp.date()}/{event_id}.jpg",
            json_log_path=f"data/events/{timestamp.date()}/events.json",
            motion_confidence=0.85,
            detected_objects=[
                DetectedObject(
                    label="person",
                    confidence=0.92,
                    bbox=BoundingBox(x=100, y=200, width=150, height=300)
                ),
                DetectedObject(
                    label="package",
                    confidence=0.87,
                    bbox=BoundingBox(x=120, y=250, width=80, height=60)
                )
            ]
        )

    def test_log_50_events_across_multiple_days(self, logger: PlaintextEventLogger) -> None:
        """Test logging 50 events across multiple days."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create events across 3 days (roughly 17 events per day)
                base_date = datetime(2025, 11, 10, 12, 0, 0, tzinfo=timezone.utc)
                events_logged = 0

                for day_offset in range(3):  # 3 days
                    current_date = base_date + timedelta(days=day_offset)
                    events_per_day = 17 if day_offset < 2 else 16  # Total 50 events

                    for event_num in range(events_per_day):
                        event_id = "02d"
                        timestamp = current_date + timedelta(minutes=event_num * 2)  # Space out events

                        event = self.create_test_event(event_id, timestamp)
                        result = logger.log_event(event)

                        assert result is True, f"Failed to log event {event_id}"
                        events_logged += 1

                assert events_logged == 50, f"Expected 50 events, logged {events_logged}"

                # Verify file structure
                events_dir = Path("data/events")
                assert events_dir.exists(), "Events directory should exist"

                # Check each day's directory and file
                for day_offset in range(3):
                    date_str = (base_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
                    date_dir = events_dir / date_str
                    log_file = date_dir / "events.log"

                    assert date_dir.exists(), f"Date directory {date_str} should exist"
                    assert log_file.exists(), f"Log file for {date_str} should exist"

                    # Verify file is not empty
                    content = log_file.read_text()
                    assert len(content.strip()) > 0, f"Log file for {date_str} should not be empty"

            finally:
                os.chdir(original_cwd)

    def test_log_format_readability_and_correctness(self, logger: PlaintextEventLogger) -> None:
        """Test that log format is human-readable and contains correct information."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create a detailed test event
                timestamp = datetime(2025, 11, 10, 14, 32, 15, tzinfo=timezone.utc)
                event = self.create_test_event(
                    "evt_1731247935000_test",
                    timestamp,
                    "Person in blue shirt carrying brown package approaching front door"
                )

                result = logger.log_event(event)
                assert result is True

                # Read and validate the log file
                log_file = Path("data/events/2025-11-10/events.log")
                assert log_file.exists()

                content = log_file.read_text()
                lines = content.split('\n')

                # Should have 5 lines (header + objects + description + image + blank)
                assert len(lines) == 5, f"Expected 5 lines, got {len(lines)}"

                # Validate timestamp format (should be in local timezone)
                assert lines[0].startswith('['), "First line should start with timestamp"
                assert '2025-11-10' in lines[0], "Should contain date"
                assert 'EVENT:' in lines[0], "Should contain EVENT marker"
                assert 'Person detected' in lines[0], "Should contain event title"
                assert 'confidence: 92%' in lines[0], "Should contain highest object confidence"

                # Validate objects line
                assert lines[1].startswith('  - Objects: '), "Second line should be objects"
                assert 'person (92%)' in lines[1], "Should contain person with confidence"
                assert 'package (87%)' in lines[1], "Should contain package with confidence"
                assert ', ' in lines[1], "Should separate objects with comma"

                # Validate description line
                assert lines[2].startswith('  - Description: '), "Third line should be description"
                assert 'Person in blue shirt carrying brown package approaching front door' in lines[2]

                # Validate image line
                assert lines[3].startswith('  - Image: '), "Fourth line should be image path"
                assert 'evt_1731247935000_test.jpg' in lines[3], "Should contain image filename"

                # Validate blank separator line
                assert lines[4] == "", "Fifth line should be blank separator"

            finally:
                os.chdir(original_cwd)

    def test_file_rotation_at_midnight(self, logger: PlaintextEventLogger) -> None:
        """Test that events are correctly separated into different files at midnight."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create events just before and after midnight
                day1_timestamp = datetime(2025, 11, 10, 23, 59, 0, tzinfo=timezone.utc)
                day2_timestamp = datetime(2025, 11, 11, 0, 1, 0, tzinfo=timezone.utc)

                # Log event on day 1
                event1 = self.create_test_event("evt_day1", day1_timestamp, "Late night event")
                result1 = logger.log_event(event1)
                assert result1 is True

                # Log event on day 2
                event2 = self.create_test_event("evt_day2", day2_timestamp, "Early morning event")
                result2 = logger.log_event(event2)
                assert result2 is True

                # Verify separate files were created
                day1_file = Path("data/events/2025-11-10/events.log")
                day2_file = Path("data/events/2025-11-11/events.log")

                assert day1_file.exists(), "Day 1 file should exist"
                assert day2_file.exists(), "Day 2 file should exist"

                # Verify each file contains exactly one event block
                day1_content = day1_file.read_text()
                day2_content = day2_file.read_text()

                day1_lines = day1_content.split('\n')
                day2_lines = day2_content.split('\n')

                # Each event should have 5 lines (4 content + 1 blank separator)
                assert len(day1_lines) == 5, f"Day 1 file should contain 5 lines, got {len(day1_lines)}"
                assert len(day2_lines) == 5, f"Day 2 file should contain 5 lines, got {len(day2_lines)}"

                # Verify correct events in correct files
                assert 'Late night event' in day1_content
                assert 'Early morning event' in day2_content
                assert 'evt_day1' in day1_content
                assert 'evt_day2' in day2_content

            finally:
                os.chdir(original_cwd)

    def test_multiple_events_same_day_formatting(self, logger: PlaintextEventLogger) -> None:
        """Test that multiple events in the same day are properly formatted and separated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                base_timestamp = datetime(2025, 11, 10, 12, 0, 0, tzinfo=timezone.utc)

                # Log multiple events
                events_to_log = 3
                for i in range(events_to_log):
                    event_id = "02d"
                    timestamp = base_timestamp + timedelta(minutes=i * 10)
                    description = f"Event number {i + 1} description"

                    event = self.create_test_event(event_id, timestamp, description)
                    result = logger.log_event(event)
                    assert result is True

                # Read and validate the log file
                log_file = Path("data/events/2025-11-10/events.log")
                assert log_file.exists()

                content = log_file.read_text()
                lines = content.split('\n')

                # Should have 15 lines total (5 lines per event × 3 events)
                assert len(lines) == 15, f"Expected 15 lines for 3 events, got {len(lines)}"

                # Verify each event block
                for i in range(events_to_log):
                    block_start = i * 5
                    block_lines = lines[block_start:block_start + 5]

                    # Each block should have the right structure
                    assert len(block_lines) == 5, f"Event {i} block should have 5 lines"
                    assert block_lines[0].startswith('['), f"Event {i} first line should start with timestamp"
                    assert 'EVENT:' in block_lines[0], f"Event {i} should contain EVENT marker"
                    assert 'Objects:' in block_lines[1], f"Event {i} should have objects line"
                    assert f"Event number {i + 1} description" in block_lines[2], f"Event {i} should have correct description"
                    assert 'Image:' in block_lines[3], f"Event {i} should have image line"
                    assert block_lines[4] == "", f"Event {i} should end with blank line"

            finally:
                os.chdir(original_cwd)

    def test_atomic_write_integrity(self, logger: PlaintextEventLogger) -> None:
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
                log_file = Path("data/events/2025-11-10/events.log")
                assert log_file.exists()

                content = log_file.read_text()
                lines = content.split('\n')

                # Should have 25 lines (5 lines per event × 5 events)
                assert len(lines) == 25, f"Expected 25 lines for 5 events, got {len(lines)}"

                # Verify all events are present and properly formatted
                for i in range(events_to_log):
                    block_start = i * 5
                    block_lines = lines[block_start:block_start + 5]

                    assert len(block_lines) == 5, f"Event {i} should have 5 lines"
                    assert block_lines[0].startswith('['), f"Event {i} should start with timestamp"
                    assert 'EVENT:' in block_lines[0], f"Event {i} should have EVENT marker"
                    assert 'Objects:' in block_lines[1], f"Event {i} should have objects line"
                    assert 'Description:' in block_lines[2], f"Event {i} should have description"
                    assert 'Image:' in block_lines[3], f"Event {i} should have image path"
                    assert block_lines[4] == "", f"Event {i} should end with blank line"

                # Verify no temporary files remain
                temp_files = list(Path("data/events/2025-11-10").glob("*.tmp"))
                assert len(temp_files) == 0, f"Temporary files found: {temp_files}"

            finally:
                os.chdir(original_cwd)