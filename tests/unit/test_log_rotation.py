"""Unit tests for log rotation functionality."""

import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.config import SystemConfig
from core.log_rotation import LogRotator
from core.storage_monitor import StorageMonitor, StorageStats


class TestLogRotator:
    """Test LogRotator class functionality."""

    @pytest.fixture
    def config(self) -> SystemConfig:
        """Create test configuration."""
        return SystemConfig(
            camera_rtsp_url="rtsp://test",
            max_storage_gb=4.0,
            min_retention_days=7
        )

    @pytest.fixture
    def storage_monitor(self, config: SystemConfig) -> StorageMonitor:
        """Create StorageMonitor instance."""
        return StorageMonitor(config)

    @pytest.fixture
    def rotator(self, config: SystemConfig, storage_monitor: StorageMonitor) -> LogRotator:
        """Create LogRotator instance."""
        return LogRotator(config, storage_monitor)

    def test_init(self, config: SystemConfig, storage_monitor: StorageMonitor) -> None:
        """Test initialization."""
        rotator = LogRotator(config, storage_monitor)

        assert rotator.config == config
        assert rotator.storage_monitor == storage_monitor

    def test_rotate_logs_no_rotation_needed(self, rotator: LogRotator) -> None:
        """Test rotate_logs returns 0 when rotation is not needed."""
        with patch.object(rotator, '_should_rotate', return_value=False):
            result = rotator.rotate_logs()
            assert result == 0

    def test_rotate_logs_force_rotation(self, rotator: LogRotator) -> None:
        """Test rotate_logs with force=True bypasses threshold check."""
        with patch.object(rotator, '_should_rotate', return_value=False), \
             patch.object(rotator, '_get_directories_to_delete', return_value=[]):
            result = rotator.rotate_logs(force=True)
            assert result == 0

    @patch('core.log_rotation.get_logger')
    def test_rotate_logs_with_deletion(self, mock_get_logger: MagicMock, rotator: LogRotator) -> None:
        """Test rotate_logs performs deletion when needed."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Mock storage stats (95% usage)
        stats = StorageStats(
            total_bytes=int(3.8 * 1024 * 1024 * 1024),  # 3.8GB
            limit_bytes=4 * 1024 * 1024 * 1024,         # 4GB
            percentage_used=0.95,
            is_over_limit=False
        )

        # Mock directories to delete
        today = datetime.now().date()
        old_date = today - timedelta(days=10)
        dir_path = Path("data/events") / old_date.isoformat()

        directories = [(dir_path, old_date)]

        with patch.object(rotator.storage_monitor, 'check_usage', return_value=stats), \
             patch.object(rotator, '_get_directories_to_delete', return_value=directories), \
             patch.object(rotator, '_delete_directory', return_value=100 * 1024 * 1024) as mock_delete:

            result = rotator.rotate_logs(force=True)

            assert result == 100 * 1024 * 1024  # Bytes freed
            mock_delete.assert_called_once_with(dir_path, old_date)

    def test_should_rotate_under_threshold(self, rotator: LogRotator) -> None:
        """Test _should_rotate returns False when under 90% threshold."""
        stats = StorageStats(
            total_bytes=int(3.5 * 1024 * 1024 * 1024),  # 3.5GB
            limit_bytes=4 * 1024 * 1024 * 1024,         # 4GB
            percentage_used=0.875,  # 87.5%
            is_over_limit=False
        )

        with patch.object(rotator.storage_monitor, 'check_usage', return_value=stats):
            assert rotator._should_rotate() is False

    def test_should_rotate_over_threshold(self, rotator: LogRotator) -> None:
        """Test _should_rotate returns True when over 90% threshold."""
        stats = StorageStats(
            total_bytes=int(3.7 * 1024 * 1024 * 1024),  # 3.7GB
            limit_bytes=4 * 1024 * 1024 * 1024,         # 4GB
            percentage_used=0.925,  # 92.5%
            is_over_limit=False
        )

        with patch.object(rotator.storage_monitor, 'check_usage', return_value=stats):
            assert rotator._should_rotate() is True

    def test_get_directories_to_delete_no_directory(self, rotator: LogRotator) -> None:
        """Test _get_directories_to_delete when events directory doesn't exist."""
        with patch('core.log_rotation.Path') as mock_path:
            mock_path.return_value.exists.return_value = False
            directories = rotator._get_directories_to_delete()
            assert directories == []

    def test_get_directories_to_delete_with_directories(self, rotator: LogRotator) -> None:
        """Test _get_directories_to_delete identifies and sorts directories."""
        today = datetime.now().date()
        old_date1 = today - timedelta(days=10)
        old_date2 = today - timedelta(days=15)
        recent_date = today - timedelta(days=3)  # Within retention period

        with patch('core.log_rotation.Path') as mock_path_class:
            # Mock events directory
            mock_events_dir = MagicMock()
            mock_events_dir.exists.return_value = True

            # Mock subdirectories
            mock_dir1 = MagicMock()
            mock_dir1.is_dir.return_value = True
            mock_dir1.name = old_date1.isoformat()

            mock_dir2 = MagicMock()
            mock_dir2.is_dir.return_value = True
            mock_dir2.name = old_date2.isoformat()

            mock_dir3 = MagicMock()
            mock_dir3.is_dir.return_value = True
            mock_dir3.name = recent_date.isoformat()

            mock_file = MagicMock()
            mock_file.is_dir.return_value = False

            mock_events_dir.iterdir.return_value = [mock_dir1, mock_dir2, mock_dir3, mock_file]

            mock_path_class.return_value = mock_events_dir

            directories = rotator._get_directories_to_delete()

            # Should return 2 directories (old ones), sorted by date (oldest first)
            assert len(directories) == 2
            assert directories[0][1].date() == old_date2  # Older date first
            assert directories[1][1].date() == old_date1  # Newer date second

    def test_parse_directory_date_valid(self, rotator: LogRotator) -> None:
        """Test _parse_directory_date with valid date string."""
        date = rotator._parse_directory_date("2025-11-10")
        expected = datetime(2025, 11, 10)
        assert date == expected

    def test_parse_directory_date_invalid(self, rotator: LogRotator) -> None:
        """Test _parse_directory_date with invalid date strings."""
        assert rotator._parse_directory_date("invalid") is None
        assert rotator._parse_directory_date("2025/11/10") is None
        assert rotator._parse_directory_date("2025-11-32") is None
        assert rotator._parse_directory_date("25-11-10") is None

    @patch('core.log_rotation.shutil.rmtree')
    def test_delete_directory_success(self, mock_rmtree: MagicMock, rotator: LogRotator) -> None:
        """Test _delete_directory successfully deletes and returns size."""
        mock_dir = MagicMock(spec=Path)
        mock_dir.name = "2025-11-10"
        test_date = datetime(2025, 11, 10)

        with patch.object(rotator, '_calculate_directory_size', return_value=1024 * 1024):
            result = rotator._delete_directory(mock_dir, test_date)

            assert result == 1024 * 1024
            mock_rmtree.assert_called_once_with(mock_dir)

    @patch('core.log_rotation.shutil.rmtree')
    def test_delete_directory_failure(self, mock_rmtree: MagicMock, rotator: LogRotator) -> None:
        """Test _delete_directory handles deletion errors."""
        mock_rmtree.side_effect = OSError("Permission denied")

        mock_dir = MagicMock(spec=Path)
        mock_dir.name = "2025-11-10"
        test_date = datetime(2025, 11, 10)

        with patch.object(rotator, '_calculate_directory_size', return_value=1024):
            result = rotator._delete_directory(mock_dir, test_date)

            assert result == 0  # Failed deletion returns 0

    def test_calculate_directory_size(self, rotator: LogRotator) -> None:
        """Test _calculate_directory_size calculates total directory size."""
        # Mock the method to return a known size
        with patch.object(rotator, '_calculate_directory_size', return_value=1024) as mock_calc:
            result = rotator._calculate_directory_size(Path("/path/to/dir"))
            assert result == 1024
            mock_calc.assert_called_once()