"""Unit tests for main application storage monitoring integration."""

from unittest.mock import MagicMock, patch

import pytest

from core.config import SystemConfig
from core.storage_monitor import StorageMonitor, StorageStats


class TestMainStorageIntegration:
    """Test storage monitoring integration with main application."""

    @pytest.fixture
    def config(self) -> SystemConfig:
        """Create test configuration."""
        return SystemConfig(
            camera_rtsp_url="rtsp://test",
            camera_id="test_camera",
            max_storage_gb=4.0,
            storage_check_interval=100,
            log_level="INFO"
        )

    @pytest.fixture
    def storage_monitor(self, config: SystemConfig) -> StorageMonitor:
        """Create StorageMonitor instance."""
        return StorageMonitor(config)

    def test_storage_monitor_initialization_in_main(self, config: SystemConfig) -> None:
        """Test that StorageMonitor is properly initialized in main application."""
        monitor = StorageMonitor(config)
        assert monitor.config == config
        assert monitor.event_count == 0

    def test_storage_stats_calculation_accuracy(self, storage_monitor: StorageMonitor) -> None:
        """Test that storage statistics are calculated correctly."""
        # Mock directory size calculation
        with patch.object(storage_monitor, "_calculate_directory_size", return_value=2 * 1024 * 1024 * 1024):  # 2GB
            stats = storage_monitor.check_usage()

            expected_limit = 4 * 1024 * 1024 * 1024  # 4GB
            assert stats.total_bytes == 2 * 1024 * 1024 * 1024
            assert stats.limit_bytes == expected_limit
            assert stats.percentage_used == 0.5
            assert stats.is_over_limit is False

    def test_storage_limit_exceeded_detection(self, storage_monitor: StorageMonitor) -> None:
        """Test detection of storage limit exceeded."""
        # Mock over-limit usage
        with patch.object(storage_monitor, "_calculate_directory_size", return_value=5 * 1024 * 1024 * 1024):  # 5GB
            stats = storage_monitor.check_usage()

            assert stats.is_over_limit is True
            assert stats.percentage_used > 1.0

    def test_storage_check_interval_logic(self, storage_monitor: StorageMonitor) -> None:
        """Test that storage checks happen at correct intervals."""
        # Initially should not check
        assert storage_monitor.should_check_storage() is False

        # Add events up to threshold
        for i in range(99):
            storage_monitor.event_count += 1
        assert storage_monitor.should_check_storage() is False

        # Hit the threshold
        storage_monitor.event_count += 1
        assert storage_monitor.should_check_storage() is True

    def test_storage_monitor_shutdown_trigger(self, storage_monitor: StorageMonitor) -> None:
        """Test that storage monitor correctly triggers shutdown when limit exceeded."""
        storage_monitor.event_count = 100  # Trigger check

        with patch.object(storage_monitor, "check_usage") as mock_check:
            # Mock over-limit condition
            mock_check.return_value = StorageStats(
                total_bytes=5 * 1024 * 1024 * 1024,  # 5GB
                limit_bytes=4 * 1024 * 1024 * 1024,  # 4GB
                percentage_used=1.25,
                is_over_limit=True,
            )

            with patch.object(storage_monitor.logger, "error") as mock_error:
                result = storage_monitor.check_storage_and_enforce_limits()

                assert result is True  # Should trigger shutdown
                assert storage_monitor.event_count == 0  # Counter reset
                mock_error.assert_called_once()

    def test_storage_monitor_no_shutdown_under_limit(self, storage_monitor: StorageMonitor) -> None:
        """Test that storage monitor does not trigger shutdown when under limit."""
        storage_monitor.event_count = 100  # Trigger check

        with patch.object(storage_monitor, "check_usage") as mock_check:
            # Mock under-limit condition
            mock_check.return_value = StorageStats(
                total_bytes=2 * 1024 * 1024 * 1024,  # 2GB
                limit_bytes=4 * 1024 * 1024 * 1024,  # 4GB
                percentage_used=0.5,
                is_over_limit=False,
            )

            with patch.object(storage_monitor.logger, "info") as mock_info:
                result = storage_monitor.check_storage_and_enforce_limits()

                assert result is False  # Should not trigger shutdown
                assert storage_monitor.event_count == 0  # Counter reset
                mock_info.assert_called_once()

    def test_storage_monitor_warning_at_high_usage(self, storage_monitor: StorageMonitor) -> None:
        """Test that storage monitor logs warning at high usage levels."""
        storage_monitor.event_count = 100  # Trigger check

        with patch.object(storage_monitor, "check_usage") as mock_check:
            # Mock high usage (87.5% - above 80% warning threshold)
            mock_check.return_value = StorageStats(
                total_bytes=int(3.5 * 1024 * 1024 * 1024),  # 3.5GB
                limit_bytes=4 * 1024 * 1024 * 1024,  # 4GB
                percentage_used=0.875,
                is_over_limit=False,
            )

            with patch.object(storage_monitor.logger, "warning") as mock_warning:
                result = storage_monitor.check_storage_and_enforce_limits()

                assert result is False  # Should not trigger shutdown
                mock_warning.assert_called_once()

    def test_storage_monitor_counter_increment(self, storage_monitor: StorageMonitor) -> None:
        """Test that event counter increments properly."""
        initial_count = storage_monitor.event_count
        storage_monitor.check_storage_and_enforce_limits()

        assert storage_monitor.event_count == initial_count + 1

    def test_storage_monitor_counter_reset_on_check(self, storage_monitor: StorageMonitor) -> None:
        """Test that event counter resets after storage check."""
        storage_monitor.event_count = 100  # Above threshold

        with patch.object(storage_monitor, "check_usage") as mock_check:
            mock_check.return_value = StorageStats(
                total_bytes=1024,
                limit_bytes=4096,
                percentage_used=0.25,
                is_over_limit=False,
            )

            storage_monitor.check_storage_and_enforce_limits()

            assert storage_monitor.event_count == 0  # Should be reset

    def test_storage_monitor_status_display_formatting(self, storage_monitor: StorageMonitor) -> None:
        """Test that storage status display is formatted correctly."""
        with patch.object(storage_monitor, "check_usage") as mock_check:
            mock_check.return_value = StorageStats(
                total_bytes=int(1.234 * 1024 * 1024 * 1024),  # 1.234GB
                limit_bytes=4 * 1024 * 1024 * 1024,  # 4GB
                percentage_used=0.3085,
                is_over_limit=False,
            )

            status = storage_monitor.get_status_display()
            assert "1.2GB" in status
            assert "4GB" in status
            assert "31%" in status or "30%" in status  # Rounding may vary