"""Unit tests for plaintext event logger."""

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from core.config import SystemConfig
from core.events import Event
from core.models import BoundingBox, DetectedObject
from core.plaintext_logger import PlaintextEventLogger


class TestPlaintextEventLogger:
    """Test cases for PlaintextEventLogger class."""

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

    @pytest.fixture
    def sample_event(self) -> Event:
        """Create a sample event for testing."""
        return Event(
            event_id="evt_1731200000000_a1b2",
            timestamp=datetime(2025, 11, 10, 12, 0, 0, tzinfo=timezone.utc),
            camera_id="test_camera",
            llm_description="Person in blue shirt carrying brown package approaching front door",
            image_path="data/events/2025-11-10/evt_1731200000000_a1b2.jpg",
            json_log_path="data/events/2025-11-10/events.json",
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

    def test_init(self, config: SystemConfig) -> None:
        """Test logger initialization."""
        logger = PlaintextEventLogger(config)
        assert logger.config == config
        assert logger.logger is not None

    def test_log_event_creates_directory_structure(self, logger: PlaintextEventLogger, sample_event: Event) -> None:
        """Test that logging creates proper directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('pathlib.Path.mkdir') as mock_mkdir:
                with patch.object(logger, '_atomic_append', return_value=True) as mock_append:
                    # Change to temp directory for test
                    original_cwd = os.getcwd()
                    os.chdir(temp_dir)

                    try:
                        result = logger.log_event(sample_event)

                        assert result is True
                        # Verify directory creation was called
                        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
                        # Verify atomic append was called
                        mock_append.assert_called_once()

                    finally:
                        os.chdir(original_cwd)

    def test_log_event_calls_atomic_append(self, logger: PlaintextEventLogger, sample_event: Event) -> None:
        """Test that log_event calls atomic append with correct parameters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('pathlib.Path.mkdir'):
                with patch.object(logger, '_atomic_append', return_value=True) as mock_append:
                    original_cwd = os.getcwd()
                    os.chdir(temp_dir)

                    try:
                        result = logger.log_event(sample_event)

                        assert result is True
                        # Verify atomic append was called with correct file path and content
                        call_args = mock_append.call_args
                        target_file = call_args[0][0]
                        content = call_args[0][1]

                        assert str(target_file).endswith("data/events/2025-11-10/events.log")
                        assert content.endswith("\n")
                        assert "[2025-11-10" in content  # Check timestamp format
                        assert "Person detected" in content  # Check event title
                        assert "person (92%)" in content  # Check object formatting
                        assert "package (87%)" in content  # Check object formatting

                    finally:
                        os.chdir(original_cwd)

    def test_log_event_handles_atomic_append_failure(self, logger: PlaintextEventLogger, sample_event: Event) -> None:
        """Test that log_event handles atomic append failures gracefully."""
        with patch('pathlib.Path.mkdir'):
            with patch.object(logger, '_atomic_append', return_value=False):
                result = logger.log_event(sample_event)

                assert result is False

    def test_log_event_logs_performance_warning(self, logger: PlaintextEventLogger, sample_event: Event) -> None:
        """Test that slow operations trigger performance warnings."""
        with patch('pathlib.Path.mkdir'):
            with patch.object(logger, '_atomic_append', return_value=True):
                with patch('time.time', side_effect=[0.0, 0.01]):  # 10ms delay
                    with patch.object(logger.logger, 'warning') as mock_warning:
                        logger.log_event(sample_event)

                        # Verify performance warning was logged
                        mock_warning.assert_called_once()
                        call_args = mock_warning.call_args
                        assert "exceeded performance target" in call_args[0][0]
                        assert call_args[1]["extra"]["performance_ms"] == 10.0

    def test_format_event_complete_structure(self, logger: PlaintextEventLogger, sample_event: Event) -> None:
        """Test that _format_event produces correct structure."""
        formatted = logger._format_event(sample_event)

        lines = formatted.split('\n')

        # Should have 5 lines (header + objects + description + image + empty)
        assert len(lines) == 5

        # Check timestamp format (should be in local timezone)
        assert lines[0].startswith('[')
        assert '2025-11-10' in lines[0]
        assert 'EVENT:' in lines[0]
        assert 'Person detected' in lines[0]
        assert 'confidence: 92%' in lines[0]  # Highest confidence object

        # Check objects line
        assert lines[1].startswith('  - Objects: ')
        assert 'person (92%)' in lines[1]
        assert 'package (87%)' in lines[1]

        # Check description line
        assert lines[2].startswith('  - Description: ')
        assert 'Person in blue shirt' in lines[2]

        # Check image line
        assert lines[3].startswith('  - Image: ')
        assert 'evt_1731200000000_a1b2.jpg' in lines[3]

    def test_format_event_no_motion_confidence(self, logger: PlaintextEventLogger) -> None:
        """Test formatting when motion_confidence is None."""
        event = Event(
            event_id="evt_test",
            timestamp=datetime(2025, 11, 10, 12, 0, 0, tzinfo=timezone.utc),
            camera_id="test_camera",
            llm_description="Test description",
            image_path="data/events/2025-11-10/test.jpg",
            json_log_path="data/events/2025-11-10/events.json",
            motion_confidence=None,
            detected_objects=[
                DetectedObject(
                    label="car",
                    confidence=0.95,
                    bbox=BoundingBox(x=0, y=0, width=100, height=100)
                )
            ]
        )

        formatted = logger._format_event(event)
        first_line = formatted.split('\n')[0]

        # Should include confidence from detected object
        assert 'confidence: 95%' in first_line
        assert 'Car detected' in first_line

    def test_format_event_no_objects(self, logger: PlaintextEventLogger) -> None:
        """Test formatting when no objects are detected."""
        event = Event(
            event_id="evt_test",
            timestamp=datetime(2025, 11, 10, 12, 0, 0, tzinfo=timezone.utc),
            camera_id="test_camera",
            llm_description="Motion detected",
            image_path="data/events/2025-11-10/test.jpg",
            json_log_path="data/events/2025-11-10/events.json",
            motion_confidence=0.5,
            detected_objects=[]
        )

        formatted = logger._format_event(event)
        lines = formatted.split('\n')

        # Should have 4 lines (header + description + image + empty)
        assert len(lines) == 4

        # First line should have motion confidence
        assert 'Motion detected (confidence: 50%)' in lines[0]

        # Should not have objects line
        objects_lines = [line for line in lines if 'Objects:' in line]
        assert len(objects_lines) == 0

    def test_get_event_title_with_objects(self, logger: PlaintextEventLogger) -> None:
        """Test event title generation with detected objects."""
        event = Event(
            event_id="evt_test",
            timestamp=datetime(2025, 11, 10, 12, 0, 0, tzinfo=timezone.utc),
            camera_id="test_camera",
            llm_description="Test",
            image_path="test.jpg",
            json_log_path="test.json",
            detected_objects=[
                DetectedObject(label="person", confidence=0.8, bbox=BoundingBox(x=0, y=0, width=10, height=10)),
                DetectedObject(label="car", confidence=0.95, bbox=BoundingBox(x=0, y=0, width=10, height=10))
            ]
        )

        title = logger._get_event_title(event)
        assert title == "Car detected (confidence: 95%)"  # Should pick highest confidence

    def test_get_event_title_no_objects(self, logger: PlaintextEventLogger) -> None:
        """Test event title generation without detected objects."""
        event = Event(
            event_id="evt_test",
            timestamp=datetime(2025, 11, 10, 12, 0, 0, tzinfo=timezone.utc),
            camera_id="test_camera",
            llm_description="Test",
            image_path="test.jpg",
            json_log_path="test.json",
            detected_objects=[]
        )

        title = logger._get_event_title(event)
        assert title == "Motion detected"

    def test_format_detected_objects(self, logger: PlaintextEventLogger) -> None:
        """Test formatting of detected objects list."""
        objects = [
            DetectedObject(label="person", confidence=0.92, bbox=BoundingBox(x=0, y=0, width=10, height=10)),
            DetectedObject(label="dog", confidence=0.78, bbox=BoundingBox(x=0, y=0, width=10, height=10)),
            DetectedObject(label="car", confidence=0.85, bbox=BoundingBox(x=0, y=0, width=10, height=10))
        ]

        formatted = logger._format_detected_objects(objects)
        assert formatted == "person (92%), dog (78%), car (85%)"

    def test_atomic_append_creates_file_with_correct_permissions(self) -> None:
        """Test that atomic append creates files with correct permissions."""
        config = SystemConfig(
            camera_rtsp_url="rtsp://test:12345@192.168.1.100:554/stream1",
            camera_id="test_camera"
        )
        logger = PlaintextEventLogger(config)

        with tempfile.TemporaryDirectory() as temp_dir:
            target_file = Path(temp_dir) / "test.log"
            content = "[2025-11-10 12:00:00] EVENT: Test event\n"

            result = logger._atomic_append(target_file, content)

            assert result is True
            assert target_file.exists()

            # Check file permissions (0644)
            stat_result = target_file.stat()
            permissions = stat_result.st_mode & 0o777
            assert permissions == 0o644

    def test_atomic_append_preserves_existing_content(self) -> None:
        """Test that atomic append preserves existing file content."""
        config = SystemConfig(
            camera_rtsp_url="rtsp://test:12345@192.168.1.100:554/stream1",
            camera_id="test_camera"
        )
        logger = PlaintextEventLogger(config)

        with tempfile.TemporaryDirectory() as temp_dir:
            target_file = Path(temp_dir) / "test.log"

            # Create file with existing content
            existing_content = "[2025-11-10 11:00:00] EVENT: First event\n\n"
            target_file.write_text(existing_content)

            # Append new content
            new_content = "[2025-11-10 12:00:00] EVENT: Second event\n\n"
            result = logger._atomic_append(target_file, new_content)

            assert result is True
            final_content = target_file.read_text()
            assert final_content == existing_content + new_content

    def test_atomic_append_handles_file_operation_errors(self) -> None:
        """Test that atomic append handles file operation errors."""
        config = SystemConfig(
            camera_rtsp_url="rtsp://test:12345@192.168.1.100:554/stream1",
            camera_id="test_camera"
        )
        logger = PlaintextEventLogger(config)

        # Test with invalid path that should cause errors
        invalid_path = Path("/nonexistent/deep/path/test.log")
        content = "[2025-11-10 12:00:00] EVENT: Test event\n\n"

        result = logger._atomic_append(invalid_path, content)

        # Should return False on error
        assert result is False

    def test_log_event_error_logging(self, logger: PlaintextEventLogger, sample_event: Event) -> None:
        """Test that errors are properly logged."""
        with patch('pathlib.Path.mkdir', side_effect=Exception("Test error")):
            with patch.object(logger.logger, 'error') as mock_error:
                result = logger.log_event(sample_event)

                assert result is False
                mock_error.assert_called_once()

                # Verify error log contains event ID and error details
                call_args = mock_error.call_args
                error_message = call_args[0][0]
                assert sample_event.event_id in error_message
                assert "Test error" in error_message