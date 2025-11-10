"""Unit tests for signal handling functionality."""

import signal
import threading
import time
import pytest
from unittest.mock import patch, MagicMock

from core.signals import SignalHandler


class TestSignalHandler:
    """Test cases for SignalHandler class."""

    def test_initialization(self):
        """Test SignalHandler initialization creates proper event objects."""
        handler = SignalHandler()

        assert isinstance(handler.shutdown_event, threading.Event)
        assert isinstance(handler.reload_event, threading.Event)
        assert not handler._shutdown_requested
        assert not handler._reload_requested

    def test_register_handlers(self):
        """Test signal handler registration."""
        handler = SignalHandler()

        with patch('signal.signal') as mock_signal:
            handler.register_handlers()

            # Verify signal.signal was called for each signal
            assert mock_signal.call_count == 3

            # Check that the correct signals were registered
            calls = mock_signal.call_args_list
            signal_mappings = {}
            for call in calls:
                sig_num, handler_func = call[0]
                signal_mappings[sig_num] = handler_func

            assert signal.SIGINT in signal_mappings
            assert signal.SIGTERM in signal_mappings
            assert signal.SIGHUP in signal_mappings

    def test_shutdown_signal_handling(self):
        """Test SIGINT signal handling triggers shutdown."""
        handler = SignalHandler()

        # Simulate SIGINT signal
        handler._handle_shutdown_signal(signal.SIGINT, None)

        assert handler._shutdown_requested
        assert handler.shutdown_event.is_set()
        assert handler.is_shutdown_requested()

    def test_sigterm_signal_handling(self):
        """Test SIGTERM signal handling triggers shutdown."""
        handler = SignalHandler()

        # Simulate SIGTERM signal
        handler._handle_shutdown_signal(signal.SIGTERM, None)

        assert handler._shutdown_requested
        assert handler.shutdown_event.is_set()
        assert handler.is_shutdown_requested()

    def test_duplicate_shutdown_signals(self):
        """Test that duplicate shutdown signals are handled gracefully."""
        handler = SignalHandler()

        # First signal
        handler._handle_shutdown_signal(signal.SIGINT, None)
        assert handler._shutdown_requested

        # Second signal should not cause issues
        handler._handle_shutdown_signal(signal.SIGINT, None)

        # Should still be in shutdown state
        assert handler._shutdown_requested
        assert handler.shutdown_event.is_set()

    def test_reload_signal_handling(self):
        """Test SIGHUP signal handling triggers reload."""
        handler = SignalHandler()

        # Simulate SIGHUP signal
        handler._handle_reload_signal(signal.SIGHUP, None)

        assert handler._reload_requested
        assert handler.reload_event.is_set()
        assert handler.is_reload_requested()

    def test_duplicate_reload_signals(self):
        """Test that duplicate reload signals are handled gracefully."""
        handler = SignalHandler()

        # First signal
        handler._handle_reload_signal(signal.SIGHUP, None)
        assert handler._reload_requested

        # Second signal should not cause issues
        handler._handle_reload_signal(signal.SIGHUP, None)

        # Should still be in reload state
        assert handler._reload_requested
        assert handler.reload_event.is_set()

    def test_clear_reload_flag(self):
        """Test clearing reload flag after processing."""
        handler = SignalHandler()

        # Set reload flag
        handler._handle_reload_signal(signal.SIGHUP, None)
        assert handler._reload_requested
        assert handler.reload_event.is_set()

        # Clear the flag
        handler.clear_reload_flag()
        assert not handler._reload_requested
        assert not handler.reload_event.is_set()

    def test_wait_for_shutdown_timeout(self):
        """Test waiting for shutdown with timeout."""
        handler = SignalHandler()

        # Test timeout without signal
        result = handler.wait_for_shutdown(timeout=0.01)
        assert not result

        # Test immediate return when shutdown is set
        handler.shutdown_event.set()
        result = handler.wait_for_shutdown(timeout=0.01)
        assert result

    def test_wait_for_shutdown_no_timeout(self):
        """Test waiting for shutdown without timeout."""
        handler = SignalHandler()

        # Start a thread that will set the event
        def set_event_after_delay():
            time.sleep(0.05)
            handler.shutdown_event.set()

        thread = threading.Thread(target=set_event_after_delay, daemon=True)
        thread.start()

        # Wait should return True when event is set
        start_time = time.time()
        result = handler.wait_for_shutdown()
        elapsed = time.time() - start_time

        assert result
        assert elapsed >= 0.05  # Should have waited for the event

    @patch('core.signals.logger')
    def test_logging_on_signal_registration(self, mock_logger):
        """Test that signal registration is logged."""
        handler = SignalHandler()

        with patch('signal.signal'):
            handler.register_handlers()

        mock_logger.info.assert_called_with("Signal handlers registered: SIGINT, SIGTERM, SIGHUP")

    @patch('core.signals.logger')
    def test_logging_on_shutdown_signal(self, mock_logger):
        """Test that shutdown signals are logged."""
        handler = SignalHandler()

        handler._handle_shutdown_signal(signal.SIGINT, None)

        mock_logger.info.assert_called_with("Received SIGINT, initiating graceful shutdown...")

    @patch('core.signals.logger')
    def test_logging_on_sigterm_signal(self, mock_logger):
        """Test that SIGTERM signals are logged."""
        handler = SignalHandler()

        handler._handle_shutdown_signal(signal.SIGTERM, None)

        mock_logger.info.assert_called_with("Received SIGTERM, initiating graceful shutdown...")

    @patch('core.signals.logger')
    def test_logging_on_reload_signal(self, mock_logger):
        """Test that reload signals are logged."""
        handler = SignalHandler()

        handler._handle_reload_signal(signal.SIGHUP, None)

        mock_logger.info.assert_called_with("Received SIGHUP, reloading configuration...")

    @patch('core.signals.logger')
    def test_logging_on_duplicate_signals(self, mock_logger):
        """Test logging for duplicate signals."""
        handler = SignalHandler()

        # First shutdown signal
        handler._handle_shutdown_signal(signal.SIGINT, None)

        # Second shutdown signal
        handler._handle_shutdown_signal(signal.SIGINT, None)

        # Should have logged the duplicate warning
        mock_logger.warning.assert_called_with("SIGINT received - shutdown already in progress")

        # Reset for reload test
        handler.clear_reload_flag()

        # First reload signal
        handler._handle_reload_signal(signal.SIGHUP, None)

        # Second reload signal
        handler._handle_reload_signal(signal.SIGHUP, None)

        # Should have logged the duplicate warning
        mock_logger.warning.assert_called_with("SIGHUP received - reload already in progress")


class TestHotReload:
    """Test cases for hot-reload functionality."""

    @patch('main.load_config')
    @patch('main.logger')
    def test_perform_hot_reload_success(self, mock_logger, mock_load_config):
        """Test successful hot-reload with configuration changes."""
        from main import perform_hot_reload
        from core.config import SystemConfig

        # Create mock configs
        old_config = SystemConfig(
            camera_rtsp_url="rtsp://old:old@old:554/old",
            camera_id="test",
            motion_threshold=0.5,
            frame_sample_rate=5,
            coreml_model_path="models/old.mlmodel",
            blacklist_objects=["old"],
            min_object_confidence=0.5,
            ollama_base_url="http://localhost:11434",
            ollama_model="old_model",
            llm_timeout=10,
            db_path=":memory:",
            max_storage_gb=1.0,
            min_retention_days=7,
            log_level="INFO",
            metrics_interval=60
        )

        new_config = SystemConfig(
            camera_rtsp_url="rtsp://new:new@new:554/new",
            camera_id="test",
            motion_threshold=0.3,
            frame_sample_rate=10,
            coreml_model_path="models/new.mlmodel",
            blacklist_objects=["new"],
            min_object_confidence=0.7,
            ollama_base_url="http://localhost:11434",
            ollama_model="new_model",
            llm_timeout=10,
            db_path=":memory:",
            max_storage_gb=1.0,
            min_retention_days=7,
            log_level="INFO",
            metrics_interval=60
        )

        mock_load_config.return_value = new_config

        # Create mock components
        mock_rtsp = MagicMock()
        mock_coreml = MagicMock()
        mock_ollama = MagicMock()
        mock_pipeline = MagicMock()

        # Test hot reload
        result = perform_hot_reload(old_config, mock_rtsp, mock_coreml, mock_ollama, mock_pipeline)

        assert result is True
        mock_load_config.assert_called_once()
        mock_rtsp.disconnect.assert_called_once()
        mock_rtsp.connect.assert_called_once()
        mock_coreml.load_model.assert_called_once_with("models/new.mlmodel")

    @patch('main.load_config')
    @patch('main.logger')
    def test_perform_hot_reload_config_load_failure(self, mock_logger, mock_load_config):
        """Test hot-reload failure when config loading fails."""
        from main import perform_hot_reload

        mock_load_config.side_effect = Exception("Config load failed")

        # Create minimal mock objects
        mock_config = MagicMock()
        mock_rtsp = MagicMock()
        mock_coreml = MagicMock()
        mock_ollama = MagicMock()
        mock_pipeline = MagicMock()

        result = perform_hot_reload(mock_config, mock_rtsp, mock_coreml, mock_ollama, mock_pipeline)

        assert result is False
        mock_logger.error.assert_called()

    @patch('main.load_config')
    @patch('main.logger')
    def test_perform_hot_reload_rtsp_reconnect_failure(self, mock_logger, mock_load_config):
        """Test hot-reload failure when RTSP reconnection fails."""
        from main import perform_hot_reload
        from core.config import SystemConfig

        # Create configs with different RTSP URLs
        old_config = SystemConfig(
            camera_rtsp_url="rtsp://old:old@old:554/old",
            camera_id="test",
            motion_threshold=0.5,
            frame_sample_rate=5,
            coreml_model_path="models/old.mlmodel",
            blacklist_objects=["old"],
            min_object_confidence=0.5,
            ollama_base_url="http://localhost:11434",
            ollama_model="old_model",
            llm_timeout=10,
            db_path=":memory:",
            max_storage_gb=1.0,
            min_retention_days=7,
            log_level="INFO",
            metrics_interval=60
        )

        new_config = SystemConfig(
            camera_rtsp_url="rtsp://new:new@new:554/new",  # Different URL
            camera_id="test",
            motion_threshold=0.5,
            frame_sample_rate=5,
            coreml_model_path="models/old.mlmodel",
            blacklist_objects=["old"],
            min_object_confidence=0.5,
            ollama_base_url="http://localhost:11434",
            ollama_model="old_model",
            llm_timeout=10,
            db_path=":memory:",
            max_storage_gb=1.0,
            min_retention_days=7,
            log_level="INFO",
            metrics_interval=60
        )

        mock_load_config.return_value = new_config

        # Create mock components
        mock_rtsp = MagicMock()
        mock_rtsp.connect.side_effect = Exception("RTSP connect failed")
        mock_coreml = MagicMock()
        mock_ollama = MagicMock()
        mock_pipeline = MagicMock()

        result = perform_hot_reload(old_config, mock_rtsp, mock_coreml, mock_ollama, mock_pipeline)

        assert result is False
        mock_logger.error.assert_called_with("Failed to reconnect RTSP camera: RTSP connect failed")

    @patch('main.load_config')
    @patch('main.logger')
    def test_perform_hot_reload_coreml_reload_failure(self, mock_logger, mock_load_config):
        """Test hot-reload failure when CoreML model reload fails."""
        from main import perform_hot_reload
        from core.config import SystemConfig

        # Create configs with different model paths
        old_config = SystemConfig(
            camera_rtsp_url="rtsp://old:old@old:554/old",
            camera_id="test",
            motion_threshold=0.5,
            frame_sample_rate=5,
            coreml_model_path="models/old.mlmodel",
            blacklist_objects=["old"],
            min_object_confidence=0.5,
            ollama_base_url="http://localhost:11434",
            ollama_model="old_model",
            llm_timeout=10,
            db_path=":memory:",
            max_storage_gb=1.0,
            min_retention_days=7,
            log_level="INFO",
            metrics_interval=60
        )

        new_config = SystemConfig(
            camera_rtsp_url="rtsp://old:old@old:554/old",
            camera_id="test",
            motion_threshold=0.5,
            frame_sample_rate=5,
            coreml_model_path="models/new.mlmodel",  # Different path
            blacklist_objects=["old"],
            min_object_confidence=0.5,
            ollama_base_url="http://localhost:11434",
            ollama_model="old_model",
            llm_timeout=10,
            db_path=":memory:",
            max_storage_gb=1.0,
            min_retention_days=7,
            log_level="INFO",
            metrics_interval=60
        )

        mock_load_config.return_value = new_config

        # Create mock components
        mock_rtsp = MagicMock()
        mock_coreml = MagicMock()
        mock_coreml.load_model.side_effect = Exception("Model load failed")
        mock_ollama = MagicMock()
        mock_pipeline = MagicMock()

        result = perform_hot_reload(old_config, mock_rtsp, mock_coreml, mock_ollama, mock_pipeline)

        assert result is False
        mock_logger.error.assert_called_with("Failed to reload CoreML model: Model load failed")