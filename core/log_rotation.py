"""Log rotation and cleanup strategy for managing disk space.

This module provides the LogRotator class for implementing FIFO (First In, First Out)
log rotation to prevent unlimited disk space consumption by deleting old event data.
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

from .config import SystemConfig
from .logging_config import get_logger
from .storage_monitor import StorageMonitor


class LogRotator:
    """Manages log rotation and cleanup to prevent disk space exhaustion.

    This class implements a FIFO rotation strategy that deletes the oldest
    date-based directories when storage usage exceeds configured thresholds.
    """

    def __init__(self, config: SystemConfig, storage_monitor: StorageMonitor) -> None:
        """Initialize the log rotator.

        Args:
            config: System configuration containing retention settings.
            storage_monitor: Storage monitor for checking current usage.
        """
        self.config = config
        self.storage_monitor = storage_monitor
        self.logger = get_logger(__name__)

    def rotate_logs(self, force: bool = False) -> int:
        """Rotate logs by deleting old date directories if needed.

        Implements FIFO rotation: deletes oldest date directories first until
        storage usage drops below the target threshold.

        Args:
            force: If True, perform rotation regardless of storage usage.

        Returns:
            Total bytes freed by rotation, or 0 if no rotation performed.
        """
        # Check if rotation is needed
        if not force and not self._should_rotate():
            return 0

        # Get current storage stats
        stats = self.storage_monitor.check_usage()

        # Identify directories eligible for deletion
        directories_to_delete = self._get_directories_to_delete()

        if not directories_to_delete:
            self.logger.info("No directories available for rotation")
            return 0

        # Calculate target usage (80% of limit)
        target_bytes = int(self.config.max_storage_gb * 1024 * 1024 * 1024 * 0.8)

        total_freed = 0
        deleted_count = 0

        self.logger.warning(
            "Starting log rotation",
            extra={
                "current_usage_gb": stats.total_bytes / (1024**3),
                "limit_gb": self.config.max_storage_gb,
                "target_gb": target_bytes / (1024**3),
                "directories_available": len(directories_to_delete),
                "forced": force,
            },
        )

        # Delete directories until target is reached or no more directories
        for dir_path, dir_date in directories_to_delete:
            # For forced rotation, always delete at least one directory
            # For automatic rotation, only delete if we still need to free space
            current_usage = stats.total_bytes - total_freed
            if not force and current_usage <= target_bytes:
                break

            bytes_freed = self._delete_directory(dir_path, dir_date)
            if bytes_freed > 0:
                total_freed += bytes_freed
                deleted_count += 1

                # After forced deletion of first directory, check if we've reached target
                if force and deleted_count >= 1 and current_usage - bytes_freed <= target_bytes:
                    break

                self.logger.warning(
                    "Deleted old log directory",
                    extra={
                        "directory": dir_path.name,
                        "date": dir_date.isoformat(),
                        "freed_mb": bytes_freed / (1024 * 1024),
                    },
                )

        if total_freed > 0:
            self.logger.warning(
                "Log rotation completed",
                extra={
                    "directories_deleted": deleted_count,
                    "total_freed_mb": total_freed / (1024 * 1024),
                    "new_usage_gb": (stats.total_bytes - total_freed) / (1024**3),
                },
            )

        return total_freed

    def _should_rotate(self) -> bool:
        """Check if log rotation should be performed based on storage usage.

        Returns:
            True if storage usage exceeds 90% of limit.
        """
        stats = self.storage_monitor.check_usage()
        threshold_bytes = int(self.config.max_storage_gb * 1024 * 1024 * 1024 * 0.9)
        return stats.total_bytes > threshold_bytes

    def _get_directories_to_delete(self) -> List[Tuple[Path, datetime]]:
        """Get list of directories eligible for deletion, sorted by age (oldest first).

        Returns:
            List of (directory_path, date) tuples, sorted oldest first.
        """
        events_dir = Path("data/events")

        if not events_dir.exists():
            return []

        directories = []

        # Get current date for protection
        today = datetime.now().date()

        # Minimum retention date
        min_retention_date = today - timedelta(days=self.config.min_retention_days)

        try:
            for item in events_dir.iterdir():
                if not item.is_dir():
                    continue

                # Parse directory name as date
                dir_date = self._parse_directory_date(item.name)
                if dir_date is None:
                    continue

                # Skip current day and minimum retention period
                if dir_date.date() >= min_retention_date:
                    continue

                directories.append((item, dir_date))

        except (OSError, IOError) as e:
            self.logger.error(
                "Failed to scan events directory",
                extra={"directory": str(events_dir), "error": str(e)},
            )
            return []

        # Sort by date (oldest first)
        directories.sort(key=lambda x: x[1])

        return directories

    def _parse_directory_date(self, dirname: str) -> Optional[datetime]:
        """Parse directory name as YYYY-MM-DD date.

        Args:
            dirname: Directory name to parse.

        Returns:
            Parsed date or None if invalid format.
        """
        try:
            # Validate format: YYYY-MM-DD
            if len(dirname) != 10 or dirname[4] != "-" or dirname[7] != "-":
                return None

            return datetime.strptime(dirname, "%Y-%m-%d").replace(tzinfo=None)
        except ValueError:
            return None

    def _delete_directory(self, dir_path: Path, dir_date: datetime) -> int:
        """Delete a directory and return the bytes freed.

        Args:
            dir_path: Path to the directory to delete.
            dir_date: Date associated with the directory.

        Returns:
            Bytes freed by deletion, or 0 if deletion failed.
        """
        try:
            # Calculate size before deletion
            size_before = self._calculate_directory_size(dir_path)

            # Delete the directory
            shutil.rmtree(dir_path)

            self.logger.debug(
                "Successfully deleted directory",
                extra={
                    "directory": str(dir_path),
                    "date": dir_date.isoformat(),
                    "size_mb": size_before / (1024 * 1024),
                },
            )

            return size_before

        except (OSError, IOError, shutil.Error) as e:
            self.logger.error(
                "Failed to delete directory",
                extra={"directory": str(dir_path), "date": dir_date.isoformat(), "error": str(e)},
            )
            return 0

    def _calculate_directory_size(self, dir_path: Path) -> int:
        """Calculate total size of a directory recursively.

        Args:
            dir_path: Directory to calculate size for.

        Returns:
            Total size in bytes.
        """
        total_size = 0

        try:
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, IOError):
                        # Skip files we can't access
                        pass
        except (OSError, IOError):
            # Directory might have been deleted or become inaccessible
            pass

        return total_size
