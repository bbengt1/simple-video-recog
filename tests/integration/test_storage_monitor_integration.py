"""Integration tests for storage monitoring functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.config import SystemConfig
from core.storage_monitor import StorageMonitor


class TestStorageMonitorIntegration:
    """Integration tests for StorageMonitor with real file system operations."""

    @pytest.fixture
    def config(self) -> SystemConfig:
        """Create test configuration with small limits for testing."""
        return SystemConfig(
            camera_rtsp_url="rtsp://test",
            max_storage_gb=0.01,  # 10MB limit for better display testing
            storage_check_interval=5,  # Check every 5 events
        )

    @pytest.fixture
    def monitor(self, config: SystemConfig) -> StorageMonitor:
        """Create StorageMonitor instance."""
        return StorageMonitor(config)

    def create_test_files(self, base_dir: Path, total_size_bytes: int) -> None:
        """Create test files to simulate storage usage."""
        # Create data/events directory structure
        events_dir = base_dir / "data" / "events"
        events_dir.mkdir(parents=True, exist_ok=True)

        # Create files to reach desired total size
        file_size = 1024  # 1KB per file
        num_files = total_size_bytes // file_size

        for i in range(num_files):
            file_path = events_dir / f"test_file_{i}.dat"
            with open(file_path, "wb") as f:
                f.write(b"x" * file_size)

        # Create any remaining bytes
        remaining = total_size_bytes % file_size
        if remaining > 0:
            file_path = events_dir / "remaining.dat"
            with open(file_path, "wb") as f:
                f.write(b"x" * remaining)

    def test_storage_growth_to_warning_threshold(self, monitor: StorageMonitor) -> None:
        """Test that warning is triggered when approaching storage limit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Set up monitor to check every event for this test
                monitor.config.storage_check_interval = 1

                # Create files to reach 80% of limit (800KB out of 1MB)
                limit_bytes = int(monitor.config.max_storage_gb * 1024 * 1024 * 1024)
                warning_threshold_bytes = int(limit_bytes * 0.8)

                self.create_test_files(Path(temp_dir), warning_threshold_bytes)

                # Trigger storage check
                result = monitor.check_storage_and_enforce_limits()

                # Should not shutdown, but should have logged warning
                assert result is False

                # Verify storage stats
                stats = monitor.check_usage()
                assert stats.total_bytes >= warning_threshold_bytes
                assert stats.percentage_used >= 0.79  # Allow for rounding differences
                assert stats.is_over_limit is False

            finally:
                os.chdir(original_cwd)

    def test_storage_growth_to_critical_threshold(self, monitor: StorageMonitor) -> None:
        """Test that shutdown is triggered when exceeding storage limit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Set up monitor to check every event
                monitor.config.storage_check_interval = 1

                # Create files to exceed limit (1.2MB out of 1MB limit)
                limit_bytes = int(monitor.config.max_storage_gb * 1024 * 1024 * 1024)
                over_limit_bytes = int(limit_bytes * 1.2)

                self.create_test_files(Path(temp_dir), over_limit_bytes)

                # Trigger storage check
                result = monitor.check_storage_and_enforce_limits()

                # Should trigger shutdown
                assert result is True

                # Verify storage stats
                stats = monitor.check_usage()
                assert stats.total_bytes > limit_bytes
                assert stats.percentage_used > 1.0
                assert stats.is_over_limit is True

            finally:
                os.chdir(original_cwd)

    def test_periodic_checking_behavior(self, monitor: StorageMonitor) -> None:
        """Test that storage checks happen at configured intervals."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create some files to ensure there's storage to check
                self.create_test_files(Path(temp_dir), 100 * 1024)  # 100KB

                # Monitor should check every 5 events
                assert monitor.config.storage_check_interval == 5

                # First 4 calls should not trigger check
                for i in range(4):
                    result = monitor.check_storage_and_enforce_limits()
                    assert result is False
                    assert monitor.event_count == i + 1

                # 5th call should trigger check and reset counter
                result = monitor.check_storage_and_enforce_limits()
                assert result is False  # Under limit
                assert monitor.event_count == 0  # Counter reset

            finally:
                os.chdir(original_cwd)

    def test_status_display_with_real_files(self, monitor: StorageMonitor) -> None:
        """Test status display formatting with real files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Create 512KB of test files
                self.create_test_files(Path(temp_dir), 512 * 1024)

                # Get status display
                status = monitor.get_status_display()

                # Should show storage usage in GB
                assert "Storage:" in status
                assert "GB" in status
                assert "/" in status
                assert "(" in status and ")" in status

                # Verify the actual values
                stats = monitor.check_usage()
                expected_used_gb = stats.total_bytes / (1024 * 1024 * 1024)
                expected_limit_gb = monitor.config.max_storage_gb

                assert f"{expected_used_gb:.1f}GB" in status
                assert f"{expected_limit_gb:.0f}GB" in status

            finally:
                os.chdir(original_cwd)

    def test_empty_directory_handling(self, monitor: StorageMonitor) -> None:
        """Test behavior when data/events directory doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # Directory doesn't exist yet
                events_dir = Path("data/events")
                assert not events_dir.exists()

                # Should handle gracefully
                stats = monitor.check_usage()
                assert stats.total_bytes == 0
                assert stats.limit_bytes == int(monitor.config.max_storage_gb * 1024 * 1024 * 1024)
                assert stats.percentage_used == 0.0
                assert stats.is_over_limit is False

                # Status display should work
                status = monitor.get_status_display()
                assert "Storage:" in status

            finally:
                os.chdir(original_cwd)

    def test_pipeline_storage_shutdown_integration(self) -> None:
        """Test that pipeline properly integrates storage monitoring."""
        from unittest.mock import MagicMock
        from core.pipeline import ProcessingPipeline
        from core.signals import SignalHandler

        config = SystemConfig(
            camera_rtsp_url="rtsp://test",
            max_storage_gb=1.0,
            storage_check_interval=1,
        )

        # Create mocks
        rtsp_client = MagicMock()
        motion_detector = MagicMock()
        frame_sampler = MagicMock()
        coreml_detector = MagicMock()
        event_deduplicator = MagicMock()
        event_manager = MagicMock()
        ollama_client = MagicMock()
        image_annotator = MagicMock()
        database_manager = MagicMock()
        signal_handler = SignalHandler()
        storage_monitor = StorageMonitor(config)

        # Create pipeline
        pipeline = ProcessingPipeline(
            rtsp_client=rtsp_client,
            motion_detector=motion_detector,
            frame_sampler=frame_sampler,
            coreml_detector=coreml_detector,
            event_deduplicator=event_deduplicator,
            event_manager=event_manager,
            ollama_client=ollama_client,
            image_annotator=image_annotator,
            database_manager=database_manager,
            signal_handler=signal_handler,
            storage_monitor=storage_monitor,
            config=config,
        )

        # Verify that storage monitor is properly integrated
        assert pipeline.storage_monitor is storage_monitor
        assert pipeline.storage_monitor.config == config

        # Test that storage monitor methods are accessible
        stats = pipeline.storage_monitor.check_usage()
        assert hasattr(stats, 'total_bytes')
        assert hasattr(stats, 'limit_bytes')
        assert hasattr(stats, 'percentage_used')
        assert hasattr(stats, 'is_over_limit')

    def test_main_application_storage_exit_codes(self) -> None:
        """Test that main application uses correct exit codes for storage scenarios."""
        # This test verifies that the exit code constants are properly defined
        from main import EXIT_SUCCESS, EXIT_ERROR, EXIT_CONFIG_INVALID, EXIT_STORAGE_FULL

        assert EXIT_SUCCESS == 0
        assert EXIT_ERROR == 1
        assert EXIT_CONFIG_INVALID == 2
        assert EXIT_STORAGE_FULL == 3

    def test_health_check_storage_validation_at_startup(self) -> None:
        """Test that health checks validate storage at startup."""
        from core.health_check import HealthChecker

        config = SystemConfig(
            camera_rtsp_url="rtsp://test",
            max_storage_gb=0.01,  # 10MB limit
        )

        health_checker = HealthChecker(config)

        # Mock the StorageMonitor import inside the method
        with patch("core.storage_monitor.StorageMonitor") as mock_storage_monitor:
            storage_monitor_instance = MagicMock()
            mock_storage_monitor.return_value = storage_monitor_instance

            # Mock over-limit stats
            stats = MagicMock()
            stats.total_bytes = 15 * 1024 * 1024  # 15MB
            stats.is_over_limit = True
            storage_monitor_instance.check_usage.return_value = stats

            # Run health check
            result = health_checker.check_all(display_output=False)

            # Should fail health check
            assert result.all_passed is False
            assert len(result.failed_checks) > 0
            assert any("Storage limit exceeded" in check for check in result.failed_checks)

    def test_storage_monitor_graceful_shutdown_sequence(self) -> None:
        """Test that storage monitor triggers proper shutdown sequence."""
        from unittest.mock import patch

        config = SystemConfig(
            camera_rtsp_url="rtsp://test",
            max_storage_gb=1.0,
            storage_check_interval=1,
        )

        monitor = StorageMonitor(config)

        # Mock over-limit condition
        with patch.object(monitor, "check_usage") as mock_check:
            mock_check.return_value = MagicMock(
                total_bytes=2 * 1024 * 1024 * 1024,  # 2GB
                limit_bytes=1 * 1024 * 1024 * 1024,  # 1GB limit
                percentage_used=2.0,
                is_over_limit=True,
            )

            with patch.object(monitor.logger, "error") as mock_error:
                # Trigger storage check
                monitor.event_count = 1  # Force check
                result = monitor.check_storage_and_enforce_limits()

                # Should trigger shutdown
                assert result is True

                # Should log critical error
                mock_error.assert_called_once()
                error_call = mock_error.call_args[0][0]
                assert "Storage limit exceeded" in error_call
