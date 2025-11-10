"""Storage monitoring and size limits enforcement.

This module provides the StorageMonitor class for monitoring disk usage
and enforcing storage limits to prevent unlimited disk space consumption.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .config import SystemConfig
from .logging_config import get_logger

if TYPE_CHECKING:
    from .log_rotation import LogRotator


@dataclass
class StorageStats:
    """Storage statistics and limit information.

    Attributes:
        total_bytes: Total bytes used by data/events directory
        limit_bytes: Storage limit in bytes
        percentage_used: Percentage of limit used (0.0 to 1.0)
        is_over_limit: True if storage exceeds the limit
    """

    total_bytes: int
    limit_bytes: int
    percentage_used: float
    is_over_limit: bool


class StorageMonitor:
    """Monitors disk usage and enforces storage limits.

    This class provides storage monitoring capabilities including size calculation,
    limit enforcement, and periodic checking based on event counts.
    """

    def __init__(self, config: SystemConfig, log_rotator: Optional["LogRotator"] = None) -> None:
        """Initialize the storage monitor.

        Args:
            config: System configuration containing storage settings.
            log_rotator: Optional log rotator for automatic cleanup.
        """
        self.config = config
        self.log_rotator = log_rotator
        self.logger = get_logger(__name__)

        # Event counter for periodic checks
        self.event_count = 0

        # Validate configuration
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate storage configuration parameters."""
        if self.config.max_storage_gb <= 0:
            raise ValueError(f"max_storage_gb must be positive, got {self.config.max_storage_gb}")

        if self.config.storage_check_interval <= 0:
            raise ValueError(
                f"storage_check_interval must be positive, got {self.config.storage_check_interval}"
            )

    def check_usage(self) -> StorageStats:
        """Check current storage usage and return statistics.

        Calculates the total size of the data/events directory and compares
        against the configured limit.

        Returns:
            StorageStats object with current usage information.
        """
        # Calculate total bytes used
        total_bytes = self._calculate_directory_size()

        # Get limit in bytes
        limit_bytes = int(self.config.max_storage_gb * 1024 * 1024 * 1024)  # GB to bytes

        # Calculate percentage used
        percentage_used = total_bytes / limit_bytes if limit_bytes > 0 else 0.0

        # Check if over limit
        is_over_limit = total_bytes > limit_bytes

        return StorageStats(
            total_bytes=total_bytes,
            limit_bytes=limit_bytes,
            percentage_used=percentage_used,
            is_over_limit=is_over_limit,
        )

    def _calculate_directory_size(self) -> int:
        """Calculate total size of data/events directory recursively.

        Returns:
            Total size in bytes.
        """
        events_dir = Path("data/events")
        total_size = 0

        try:
            if events_dir.exists():
                for root, dirs, files in os.walk(events_dir):
                    for file in files:
                        file_path = Path(root) / file
                        try:
                            total_size += file_path.stat().st_size
                        except (OSError, IOError) as e:
                            self.logger.warning(
                                "Failed to get size for file",
                                extra={"file_path": str(file_path), "error": str(e)},
                            )
            else:
                self.logger.debug("Events directory does not exist yet")
        except (OSError, IOError) as e:
            self.logger.error(
                "Failed to calculate directory size",
                extra={"directory": str(events_dir), "error": str(e)},
            )

        return total_size

    def should_check_storage(self) -> bool:
        """Check if storage monitoring should be performed.

        Returns:
            True if enough events have occurred to trigger a check.
        """
        return self.event_count >= self.config.storage_check_interval

    def check_storage_and_enforce_limits(self) -> bool:
        """Check storage usage and enforce limits if necessary.

        This method should be called after each event is processed.
        It performs periodic storage checks and enforces limits.

        Returns:
            True if system should shutdown due to storage limits, False otherwise.
        """
        self.event_count += 1

        # Only check storage periodically
        if not self.should_check_storage():
            return False

        # Reset counter
        self.event_count = 0

        # Check storage usage
        stats = self.check_usage()

        # Log current status
        self._log_storage_status(stats)

        # Trigger log rotation if storage exceeds 90% and rotator is available
        if stats.percentage_used >= 0.9 and self.log_rotator is not None:
            bytes_freed = self.log_rotator.rotate_logs(force=False)
            if bytes_freed > 0:
                # Re-check storage after rotation
                stats = self.check_usage()

        # Check thresholds
        if stats.percentage_used >= 1.0:
            # Critical: Over limit
            self.logger.error(
                "Storage limit exceeded",
                extra={
                    "used_gb": stats.total_bytes / (1024**3),
                    "limit_gb": self.config.max_storage_gb,
                    "percentage": stats.percentage_used * 100,
                },
            )
            return True  # Trigger shutdown

        elif stats.percentage_used >= 0.8:
            # Warning: Approaching limit
            self.logger.warning(
                "Storage approaching limit",
                extra={
                    "used_gb": stats.total_bytes / (1024**3),
                    "limit_gb": self.config.max_storage_gb,
                    "percentage": stats.percentage_used * 100,
                },
            )

        return False

    def _log_storage_status(self, stats: StorageStats) -> None:
        """Log current storage status.

        Args:
            stats: Current storage statistics.
        """
        used_gb = stats.total_bytes / (1024**3)
        limit_gb = self.config.max_storage_gb

        self.logger.info(
            "Storage usage checked",
            extra={
                "used_gb": round(used_gb, 2),
                "limit_gb": limit_gb,
                "percentage": round(stats.percentage_used * 100, 1),
            },
        )

    def get_status_display(self) -> str:
        """Get formatted storage status for display.

        Returns:
            Formatted string like "Storage: 1.2GB / 4GB (30%)".
        """
        try:
            stats = self.check_usage()
            used_gb = stats.total_bytes / (1024**3)
            percentage = stats.percentage_used * 100

            return (
                f"Storage: {used_gb:.1f}GB / {self.config.max_storage_gb:.0f}GB ({percentage:.0f}%)"
            )
        except Exception as e:
            self.logger.error("Failed to get storage status display", extra={"error": str(e)})
            return "Storage: Unknown"
