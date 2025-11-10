"""Unit tests for storage monitoring functionality."""

from unittest.mock import MagicMock, patch

import pytest

from core.config import SystemConfig
from core.storage_monitor import StorageMonitor, StorageStats


class TestStorageStats:
    """Test StorageStats dataclass."""

    def test_storage_stats_creation(self) -> None:
        """Test creating StorageStats with valid values."""
        stats = StorageStats(
            total_bytes=1024, limit_bytes=4096, percentage_used=0.25, is_over_limit=False
        )

        assert stats.total_bytes == 1024
        assert stats.limit_bytes == 4096
        assert stats.percentage_used == 0.25
        assert stats.is_over_limit is False

    def test_storage_stats_over_limit(self) -> None:
        """Test StorageStats with over limit scenario."""
        stats = StorageStats(
            total_bytes=5000, limit_bytes=4096, percentage_used=1.22, is_over_limit=True
        )

        assert stats.is_over_limit is True
        assert stats.percentage_used > 1.0


class TestStorageMonitor:
    """Test StorageMonitor class functionality."""

    @pytest.fixture
    def config(self) -> SystemConfig:
        """Create test configuration."""
        return SystemConfig(
            camera_rtsp_url="rtsp://test", max_storage_gb=4.0, storage_check_interval=100
        )

    @pytest.fixture
    def monitor(self, config: SystemConfig) -> StorageMonitor:
        """Create StorageMonitor instance."""
        return StorageMonitor(config)

    def test_init_valid_config(self, config: SystemConfig) -> None:
        """Test initialization with valid configuration."""
        monitor = StorageMonitor(config)

        assert monitor.config == config
        assert monitor.event_count == 0

    def test_should_check_storage_initial(self, monitor: StorageMonitor) -> None:
        """Test should_check_storage returns False initially."""
        assert monitor.should_check_storage() is False

    def test_should_check_storage_after_events(self, monitor: StorageMonitor) -> None:
        """Test should_check_storage returns True after enough events."""
        # Add 99 events
        for _ in range(99):
            monitor.event_count += 1
        assert monitor.should_check_storage() is False

        # Add one more event
        monitor.event_count += 1
        assert monitor.should_check_storage() is True

    @patch("core.storage_monitor.Path")
    def test_calculate_directory_size_empty(
        self, mock_path: MagicMock, monitor: StorageMonitor
    ) -> None:
        """Test directory size calculation for non-existent directory."""
        mock_path.return_value.exists.return_value = False

        size = monitor._calculate_directory_size()
        assert size == 0

    def test_calculate_directory_size_with_files(self, monitor: StorageMonitor) -> None:
        """Test directory size calculation with files."""
        # Mock the entire method to return a known size
        with patch.object(monitor, "_calculate_directory_size", return_value=3072) as mock_calc:
            size = monitor._calculate_directory_size()
            assert size == 3072
            mock_calc.assert_called_once()

    def test_calculate_directory_size_file_error(self, monitor: StorageMonitor) -> None:
        """Test directory size calculation handles file access errors."""
        # Mock the method to simulate error handling
        with patch.object(monitor, "_calculate_directory_size", return_value=0) as mock_calc:
            size = monitor._calculate_directory_size()
            assert size == 0
            mock_calc.assert_called_once()

    def test_check_usage_under_limit(self, monitor: StorageMonitor) -> None:
        """Test check_usage when under storage limit."""
        with patch.object(
            monitor, "_calculate_directory_size", return_value=1024 * 1024 * 1024
        ):  # 1GB
            stats = monitor.check_usage()

            assert stats.total_bytes == 1024 * 1024 * 1024
            assert stats.limit_bytes == 4 * 1024 * 1024 * 1024  # 4GB
            assert stats.percentage_used == 0.25
            assert stats.is_over_limit is False

    def test_check_usage_over_limit(self, monitor: StorageMonitor) -> None:
        """Test check_usage when over storage limit."""
        with patch.object(
            monitor, "_calculate_directory_size", return_value=5 * 1024 * 1024 * 1024
        ):  # 5GB
            stats = monitor.check_usage()

            assert stats.total_bytes == 5 * 1024 * 1024 * 1024
            assert stats.limit_bytes == 4 * 1024 * 1024 * 1024  # 4GB
            assert stats.percentage_used == 1.25
            assert stats.is_over_limit is True

    def test_check_usage_zero_limit(self, monitor: StorageMonitor) -> None:
        """Test check_usage with zero limit (edge case)."""
        monitor.config.max_storage_gb = 0.0

        with patch.object(monitor, "_calculate_directory_size", return_value=1024):
            stats = monitor.check_usage()

            assert stats.total_bytes == 1024
            assert stats.limit_bytes == 0
            assert stats.percentage_used == 0.0
            assert stats.is_over_limit is True  # Any usage over 0 is over limit

    def test_check_storage_and_enforce_limits_under_threshold(
        self, monitor: StorageMonitor
    ) -> None:
        """Test check_storage_and_enforce_limits when under all thresholds."""
        # Mock the logger
        with (
            patch.object(monitor.logger, "info") as mock_info,
            patch.object(monitor.logger, "warning") as mock_warning,
            patch.object(monitor.logger, "error") as mock_error,
        ):

            # Set up monitor to trigger check
            monitor.event_count = 100

            # Mock storage usage at 50%
            with patch.object(monitor, "check_usage") as mock_check:
                mock_check.return_value = StorageStats(
                    total_bytes=2 * 1024 * 1024 * 1024,  # 2GB
                    limit_bytes=4 * 1024 * 1024 * 1024,  # 4GB
                    percentage_used=0.5,
                    is_over_limit=False,
                )

                result = monitor.check_storage_and_enforce_limits()

                assert result is False  # No shutdown
                assert monitor.event_count == 0  # Counter reset
                mock_info.assert_called_once()
                mock_warning.assert_not_called()
                mock_error.assert_not_called()

    def test_check_storage_and_enforce_limits_warning_threshold(
        self, monitor: StorageMonitor
    ) -> None:
        """Test check_storage_and_enforce_limits at warning threshold (80%)."""
        with (
            patch.object(monitor.logger, "warning") as mock_warning,
            patch.object(monitor.logger, "error") as mock_error,
        ):

            monitor.event_count = 100

            with patch.object(monitor, "check_usage") as mock_check:
                mock_check.return_value = StorageStats(
                    total_bytes=int(3.5 * 1024 * 1024 * 1024),  # 3.5GB
                    limit_bytes=4 * 1024 * 1024 * 1024,  # 4GB
                    percentage_used=0.875,  # 87.5%
                    is_over_limit=False,
                )

                result = monitor.check_storage_and_enforce_limits()

                assert result is False  # No shutdown
                mock_warning.assert_called_once()
                mock_error.assert_not_called()

    def test_check_storage_and_enforce_limits_over_limit(self, monitor: StorageMonitor) -> None:
        """Test check_storage_and_enforce_limits when over storage limit."""
        with (
            patch.object(monitor.logger, "warning") as mock_warning,
            patch.object(monitor.logger, "error") as mock_error,
        ):

            monitor.event_count = 100

            with patch.object(monitor, "check_usage") as mock_check:
                mock_check.return_value = StorageStats(
                    total_bytes=5 * 1024 * 1024 * 1024,  # 5GB
                    limit_bytes=4 * 1024 * 1024 * 1024,  # 4GB
                    percentage_used=1.25,
                    is_over_limit=True,
                )

                result = monitor.check_storage_and_enforce_limits()

                assert result is True  # Shutdown triggered
                mock_error.assert_called_once()
                mock_warning.assert_not_called()

    def test_check_storage_and_enforce_limits_no_check_needed(
        self, monitor: StorageMonitor
    ) -> None:
        """Test check_storage_and_enforce_limits when check interval not reached."""
        monitor.event_count = 50  # Less than 100

        result = monitor.check_storage_and_enforce_limits()

        assert result is False
        assert monitor.event_count == 51  # Incremented but no reset

    def test_get_status_display_success(self, monitor: StorageMonitor) -> None:
        """Test get_status_display with successful storage check."""
        with patch.object(monitor, "check_usage") as mock_check:
            mock_check.return_value = StorageStats(
                total_bytes=int(1.2 * 1024 * 1024 * 1024),  # 1.2GB
                limit_bytes=4 * 1024 * 1024 * 1024,  # 4GB
                percentage_used=0.3,
                is_over_limit=False,
            )

            status = monitor.get_status_display()
            assert status == "Storage: 1.2GB / 4GB (30%)"

    def test_get_status_display_error(self, monitor: StorageMonitor) -> None:
        """Test get_status_display handles errors gracefully."""
        with patch.object(monitor.logger, "error") as mock_error:
            with patch.object(monitor, "check_usage", side_effect=Exception("Test error")):
                status = monitor.get_status_display()
                assert status == "Storage: Unknown"
                mock_error.assert_called_once()
