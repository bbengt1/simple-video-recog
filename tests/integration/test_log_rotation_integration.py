"""Integration tests for log rotation functionality."""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from core.config import SystemConfig
from core.log_rotation import LogRotator
from core.storage_monitor import StorageMonitor


class TestLogRotationIntegration:
    """Integration tests for LogRotator with real file system operations."""

    @pytest.fixture
    def config(self) -> SystemConfig:
        """Create test configuration with small limits for testing."""
        return SystemConfig(
            camera_rtsp_url="rtsp://test",
            max_storage_gb=0.01,  # 10MB limit for easy testing
            min_retention_days=7,
            storage_check_interval=1  # Check every event
        )

    @pytest.fixture
    def storage_monitor(self, config: SystemConfig) -> StorageMonitor:
        """Create StorageMonitor instance."""
        return StorageMonitor(config)

    @pytest.fixture
    def rotator(self, config: SystemConfig, storage_monitor: StorageMonitor) -> LogRotator:
        """Create LogRotator instance."""
        return LogRotator(config, storage_monitor)

    def create_date_directory_with_files(self, base_dir: Path, date: datetime, size_mb: float) -> Path:
        """Create a date directory with test files of specified size."""
        date_str = date.strftime("%Y-%m-%d")
        date_dir = base_dir / "data" / "events" / date_str
        date_dir.mkdir(parents=True, exist_ok=True)

        # Create files to reach desired size
        file_size = 1024 * 1024  # 1MB per file
        num_files = int(size_mb * 1024 * 1024 // file_size)

        for i in range(num_files):
            file_path = date_dir / f"test_file_{i}.dat"
            with open(file_path, 'wb') as f:
                f.write(b'x' * file_size)

        # Create any remaining bytes
        remaining = int(size_mb * 1024 * 1024) % file_size
        if remaining > 0:
            file_path = date_dir / "remaining.dat"
            with open(file_path, 'wb') as f:
                f.write(b'x' * remaining)

        return date_dir

    def test_automatic_rotation_trigger(self, rotator: LogRotator, storage_monitor: StorageMonitor) -> None:
        """Test that automatic rotation triggers when storage exceeds 90%."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create date directories with old data
                base_date = datetime.now() - timedelta(days=20)

                # Create directories to exceed 90% of limit
                # 0.01 GB = 10.24 MB, 90% = 9.216 MB, so create ~9.5 MB total
                self.create_date_directory_with_files(Path(temp_dir), base_date - timedelta(days=5), 3.0)
                self.create_date_directory_with_files(Path(temp_dir), base_date - timedelta(days=10), 3.5)
                self.create_date_directory_with_files(Path(temp_dir), base_date - timedelta(days=15), 3.0)

                # Trigger rotation (should automatically detect >90% usage)
                bytes_freed = rotator.rotate_logs(force=False)

                # Should have freed some space
                assert bytes_freed > 0

                # Check that at least one old directory was deleted
                events_dir = Path("data/events")
                remaining_dirs = [d for d in events_dir.iterdir() if d.is_dir()]
                assert len(remaining_dirs) < 3  # At least one should be deleted

            finally:
                os.chdir(original_cwd)

    def test_force_rotation_bypasses_threshold(self, rotator: LogRotator) -> None:
        """Test that force=True bypasses storage threshold checks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create minimal directory structure
                events_dir = Path("data/events")
                events_dir.mkdir(parents=True)

                # Create one old directory with some content
                old_date = datetime.now() - timedelta(days=30)
                self.create_date_directory_with_files(Path(temp_dir), old_date, 1.0)

                # Force rotation even though storage is low
                bytes_freed = rotator.rotate_logs(force=True)

                # Should have deleted the directory
                assert bytes_freed > 0

                # Directory should be gone
                date_dir = events_dir / old_date.strftime("%Y-%m-%d")
                assert not date_dir.exists()

            finally:
                os.chdir(original_cwd)

    def test_current_day_protection(self, rotator: LogRotator) -> None:
        """Test that current day's directory is never deleted."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create today's directory
                today = datetime.now()
                self.create_date_directory_with_files(Path(temp_dir), today, 0.1)

                # Fill storage to trigger rotation
                for i in range(10):
                    old_date = today - timedelta(days=20 + i)
                    self.create_date_directory_with_files(Path(temp_dir), old_date, 1.0)

                # Force rotation
                rotator.rotate_logs(force=True)

                # Today's directory should still exist
                events_dir = Path("data/events")
                today_dir = events_dir / today.strftime("%Y-%m-%d")
                assert today_dir.exists()

            finally:
                os.chdir(original_cwd)

    def test_minimum_retention_protection(self, rotator: LogRotator) -> None:
        """Test that directories within minimum retention period are protected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create directories within retention period (7 days)
                today = datetime.now()
                for i in range(5):
                    date = today - timedelta(days=i + 1)  # 1-5 days ago
                    self.create_date_directory_with_files(Path(temp_dir), date, 0.1)

                # Create one old directory (beyond retention period)
                old_date = today - timedelta(days=10)
                self.create_date_directory_with_files(Path(temp_dir), old_date, 1.0)

                # Force rotation
                bytes_freed = rotator.rotate_logs(force=True)

                # Should have deleted the old directory only
                assert bytes_freed > 0

                events_dir = Path("data/events")
                remaining_dirs = [d for d in events_dir.iterdir() if d.is_dir()]

                # Should have 5 recent directories remaining
                assert len(remaining_dirs) == 5

                # Old directory should be gone
                old_dir = events_dir / old_date.strftime("%Y-%m-%d")
                assert not old_dir.exists()

            finally:
                os.chdir(original_cwd)

    def test_rotation_stops_at_target(self, rotator: LogRotator, storage_monitor: StorageMonitor) -> None:
        """Test that rotation stops when storage drops below 80% target."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create directories that will bring us to exactly 95% usage
                # Each directory is 1MB, limit is 10MB, so 9.5MB total = 95%
                base_date = datetime.now() - timedelta(days=20)

                for i in range(9):
                    date = base_date - timedelta(days=i * 2)
                    self.create_date_directory_with_files(Path(temp_dir), date, 1.0)

                # Add a small 6th directory (0.5MB) to make exactly 9.5MB
                date = base_date - timedelta(days=20)
                self.create_date_directory_with_files(Path(temp_dir), date, 0.5)

                # Check initial state
                initial_stats = storage_monitor.check_usage()
                assert initial_stats.percentage_used >= 0.9  # Should trigger rotation

                # Trigger rotation
                bytes_freed = rotator.rotate_logs(force=True)

                # Should have freed some space
                assert bytes_freed > 0

                # Check final state - should be below 80%
                final_stats = storage_monitor.check_usage()
                assert final_stats.percentage_used < 0.8

            finally:
                os.chdir(original_cwd)

    def test_empty_directory_handling(self, rotator: LogRotator) -> None:
        """Test behavior when events directory is empty or doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # No events directory exists
                result = rotator.rotate_logs(force=True)
                assert result == 0

                # Create empty events directory
                events_dir = Path("data/events")
                events_dir.mkdir(parents=True)

                result = rotator.rotate_logs(force=True)
                assert result == 0

            finally:
                os.chdir(original_cwd)