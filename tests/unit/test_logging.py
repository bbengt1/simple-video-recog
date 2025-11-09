"""Unit tests for logging configuration and functionality.

Tests cover log level filtering, formatter output, structured logging,
and logger configuration.
"""

import logging
import pytest
from unittest.mock import patch, MagicMock

from core.config import SystemConfig
from core.logging_config import (
    setup_logging,
    ConsoleFormatter,
    get_logger,
    log_structured,
)


class TestConsoleFormatter:
    """Test the custom console formatter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = ConsoleFormatter()
        self.logger = logging.getLogger("test.module")
        self.record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

    def test_format_includes_timestamp(self):
        """Test that formatted output includes ISO 8601 timestamp."""
        formatted = self.formatter.format(self.record)
        assert "T" in formatted  # ISO 8601 format contains 'T'
        assert "-" in formatted  # Date separators
        assert ":" in formatted  # Time separators

    def test_format_includes_level(self):
        """Test that formatted output includes log level."""
        formatted = self.formatter.format(self.record)
        assert "[INFO]" in formatted

    def test_format_includes_module_name(self):
        """Test that formatted output includes module name."""
        formatted = self.formatter.format(self.record)
        assert "[module]" in formatted

    def test_format_includes_message(self):
        """Test that formatted output includes the log message."""
        formatted = self.formatter.format(self.record)
        assert "Test message" in formatted

    def test_module_name_extraction(self):
        """Test module name extraction from logger names."""
        # Test dotted name
        record = logging.LogRecord(
            name="core.pipeline.worker",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test",
            args=(),
            exc_info=None,
        )
        formatted = self.formatter.format(record)
        assert "[worker]" in formatted

        # Test single name
        record.name = "simple"
        formatted = self.formatter.format(record)
        assert "[simple]" in formatted

    def test_module_name_caching(self):
        """Test that module names are cached for performance."""
        # First call should cache
        record1 = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test1",
            args=(),
            exc_info=None,
        )
        formatted1 = self.formatter.format(record1)

        # Second call with same name should use cache
        record2 = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test2",
            args=(),
            exc_info=None,
        )
        formatted2 = self.formatter.format(record2)

        # Both should have same module name formatting
        assert "[module]" in formatted1
        assert "[module]" in formatted2


class TestSetupLogging:
    """Test logging setup functionality."""

    def test_setup_logging_valid_level(self):
        """Test that setup_logging works with valid log levels."""
        config = SystemConfig(
            camera_rtsp_url="rtsp://test:pass@192.168.1.100:554/stream",
            log_level="INFO"
        )

        with patch('logging.getLogger') as mock_get_logger:
            mock_root_logger = MagicMock()
            mock_get_logger.return_value = mock_root_logger

            setup_logging(config)

            # Verify root logger was configured
            mock_root_logger.setLevel.assert_called_with(logging.INFO)
            assert mock_root_logger.addHandler.called

    def test_setup_logging_invalid_level(self):
        """Test that setup_logging raises ValueError for invalid log levels."""
        config = SystemConfig(
            camera_rtsp_url="rtsp://test:pass@192.168.1.100:554/stream",
            log_level="INVALID"
        )

        with pytest.raises(ValueError, match="Invalid log_level"):
            setup_logging(config)

    @pytest.mark.parametrize("level_str,level_int", [
        ("DEBUG", logging.DEBUG),
        ("INFO", logging.INFO),
        ("WARNING", logging.WARNING),
        ("ERROR", logging.ERROR),
    ])
    def test_setup_logging_level_mapping(self, level_str, level_int):
        """Test that log level strings map to correct logging constants."""
        config = SystemConfig(
            camera_rtsp_url="rtsp://test:pass@192.168.1.100:554/stream",
            log_level=level_str
        )

        with patch('logging.getLogger') as mock_get_logger:
            mock_root_logger = MagicMock()
            mock_get_logger.return_value = mock_root_logger

            setup_logging(config)

            mock_root_logger.setLevel.assert_called_with(level_int)

    def test_setup_logging_removes_existing_handlers(self):
        """Test that setup_logging removes existing handlers."""
        config = SystemConfig(
            camera_rtsp_url="rtsp://test:pass@192.168.1.100:554/stream",
            log_level="INFO"
        )

        with patch('logging.getLogger') as mock_get_logger:
            mock_root_logger = MagicMock()
            mock_handler = MagicMock()
            mock_root_logger.handlers = [mock_handler]
            mock_get_logger.return_value = mock_root_logger

            setup_logging(config)

            mock_root_logger.removeHandler.assert_called_with(mock_handler)


class TestGetLogger:
    """Test logger retrieval functionality."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_get_logger_caching(self):
        """Test that get_logger returns the same instance for same name."""
        logger1 = get_logger("test.cached")
        logger2 = get_logger("test.cached")
        assert logger1 is logger2


class TestLogStructured:
    """Test structured logging functionality."""

    def test_log_structured_with_metadata(self):
        """Test logging with structured metadata."""
        logger = MagicMock()
        log_structured(logger, logging.INFO, "Test message", key="value", count=42)

        # Verify logger.log was called with structured data
        logger.log.assert_called_once()
        call_args = logger.log.call_args
        assert call_args[0][0] == logging.INFO  # level
        assert "Test message" in call_args[0][1]  # message
        assert "key=value" in call_args[0][1]  # structured data in message
        assert "count=42" in call_args[0][1]  # structured data in message

    def test_log_structured_without_metadata(self):
        """Test logging without structured metadata."""
        logger = MagicMock()
        log_structured(logger, logging.INFO, "Test message")

        logger.log.assert_called_once_with(logging.INFO, "Test message", extra={"structured_data": {}})

    def test_log_structured_extra_field(self):
        """Test that structured data is passed in extra field."""
        logger = MagicMock()
        log_structured(logger, logging.INFO, "Test", key="value")

        call_args = logger.log.call_args
        assert call_args[1]["extra"]["structured_data"] == {"key": "value"}


class TestLoggingIntegration:
    """Test logging integration with actual logging calls."""

    def setup_method(self):
        """Set up test with logging configured."""
        self.config = SystemConfig(
            camera_rtsp_url="rtsp://test:pass@192.168.1.100:554/stream",
            log_level="DEBUG"
        )
        setup_logging(self.config)

    def test_log_level_filtering(self, caplog):
        """Test that log levels are properly filtered."""
        logger = get_logger("test.filtering")

        with caplog.at_level(logging.DEBUG):
            # INFO level should be logged when level is DEBUG
            logger.info("Info message")
            assert "Info message" in caplog.text

            # DEBUG level should be logged when level is DEBUG
            logger.debug("Debug message")
            assert "Debug message" in caplog.text

    def test_structured_logging_output(self, caplog):
        """Test that structured logging produces correct output format."""
        logger = get_logger("test.structured")

        with caplog.at_level(logging.INFO):
            log_structured(logger, logging.INFO, "Structured test", component="pipeline", frame_id=123)

            # Verify structured data appears in log output
            assert "component=pipeline" in caplog.text
            assert "frame_id=123" in caplog.text
            assert "Structured test" in caplog.text