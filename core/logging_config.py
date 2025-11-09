"""Logging configuration for the video recognition system.

This module provides centralized logging configuration with console output,
configurable verbosity levels, and structured logging support for future
JSON output capabilities.
"""

import logging
import time
from typing import Dict, Any

from .config import SystemConfig


class ConsoleFormatter(logging.Formatter):
    """Custom console formatter with ISO 8601 timestamps and module names.

    Formats log messages as: "[TIMESTAMP] [LEVEL] [MODULE] Message"
    Uses ISO 8601 timestamps with timezone information.
    """

    def __init__(self):
        """Initialize formatter with cached module name mapping."""
        super().__init__()
        self._module_cache: Dict[str, str] = {}

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with custom timestamp and module formatting.

        Args:
            record: The log record to format.

        Returns:
            Formatted log message string.
        """
        # Create timestamp in ISO 8601 format with timezone (optimized)
        # Use time module for better performance than datetime
        timestamp = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(record.created))
        # Add microseconds and timezone offset
        microseconds = int((record.created % 1) * 1000000)
        tz_offset = time.strftime('%z', time.localtime(record.created))
        timestamp = f"{timestamp}.{microseconds:06d}{tz_offset}"

        # Extract module name from logger name (cached for performance)
        if record.name not in self._module_cache:
            self._module_cache[record.name] = (
                record.name.split('.')[-1] if '.' in record.name else record.name
            )
        module_name = self._module_cache[record.name]

        # Format the message
        formatted_message = super().format(record)

        # Apply custom format: [TIMESTAMP] [LEVEL] [MODULE] Message
        return f"[{timestamp}] [{record.levelname}] [{module_name}] {formatted_message}"


def setup_logging(config: SystemConfig) -> None:
    """Configure Python logging with console output and structured support.

    Sets up logging with configurable verbosity levels, custom console formatting,
    and structured logging metadata for future JSON output capabilities.

    Args:
        config: SystemConfig instance containing log_level and other settings.

    Raises:
        ValueError: If log_level is not a valid logging level.
    """
    # Map string log levels to logging constants
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }

    if config.log_level not in log_level_map:
        raise ValueError(
            f"Invalid log_level '{config.log_level}'. "
            f"Must be one of: {', '.join(log_level_map.keys())}"
        )

    # Get the numeric log level
    log_level = log_level_map[config.log_level]

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    # Create and set custom formatter
    formatter = ConsoleFormatter()
    console_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Log the initial setup
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {config.log_level}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with structured logging support.

    This function provides a centralized way to get loggers with
    built-in structured logging metadata support for future JSON output.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)


def log_structured(logger: logging.Logger, level: int, message: str, **kwargs: Any) -> None:
    """Log a message with structured metadata.

    This function supports structured logging with extra fields that can be
    used for future JSON output while maintaining backward compatibility
    with console formatting.

    Args:
        logger: Logger instance to use.
        level: Logging level (e.g., logging.INFO).
        message: Log message.
        **kwargs: Additional structured metadata fields.
    """
    # For now, include structured data in the message for console output
    # Future JSON handler will extract these fields properly
    if kwargs:
        structured_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        message = f"{message} [{structured_info}]"

    logger.log(level, message, extra={"structured_data": kwargs})