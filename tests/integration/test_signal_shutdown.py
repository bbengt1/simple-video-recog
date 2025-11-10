"""Integration tests for graceful shutdown functionality."""

import os
import signal
import subprocess
import sys
import tempfile
import time
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.config import load_config
from core.signals import SignalHandler


class TestSignalShutdownIntegration:
    """Integration tests for signal handling and graceful shutdown."""

    def test_sigint_shutdown_during_processing(self):
        """Test that SIGINT signal triggers graceful shutdown during processing."""
        # Create a minimal config for testing
        config_content = """
camera_rtsp_url: "rtsp://test:test@127.0.0.1:554/test"
camera_id: "test_camera"
motion_threshold: 0.5
frame_sample_rate: 5
coreml_model_path: "models/test.mlmodel"
blacklist_objects: ["test"]
min_object_confidence: 0.5
ollama_base_url: "http://localhost:11434"
ollama_model: "test"
llm_timeout: 10
db_path: ":memory:"
max_storage_gb: 1.0
min_retention_days: 7
log_level: "INFO"
metrics_interval: 60
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            # Load config to validate it
            config = load_config(config_path)

            # Test signal handler initialization
            signal_handler = SignalHandler()
            signal_handler.register_handlers()

            # Simulate SIGINT
            signal_handler._handle_shutdown_signal(signal.SIGINT, None)

            # Verify shutdown was triggered
            assert signal_handler.is_shutdown_requested()

            # Test idempotent behavior (second signal should not cause issues)
            signal_handler._handle_shutdown_signal(signal.SIGINT, None)
            assert signal_handler.is_shutdown_requested()

        finally:
            os.unlink(config_path)

    def test_shutdown_timeout_mechanism(self):
        """Test shutdown timeout mechanism prevents hanging."""
        signal_handler = SignalHandler()

        # Test that wait_for_shutdown returns False when timeout expires
        result = signal_handler.wait_for_shutdown(timeout=0.01)
        assert not result

        # Test that wait_for_shutdown returns True when shutdown is set
        signal_handler.shutdown_event.set()
        result = signal_handler.wait_for_shutdown(timeout=0.01)
        assert result

    def test_signal_handler_thread_safety(self):
        """Test that signal handler is thread-safe under concurrent access."""
        import threading

        signal_handler = SignalHandler()
        results = []

        def worker_thread(thread_id):
            """Worker thread that accesses signal handler."""
            try:
                # Test setting shutdown from multiple threads
                if thread_id % 2 == 0:
                    signal_handler._handle_shutdown_signal(signal.SIGINT, None)
                else:
                    signal_handler._handle_reload_signal(signal.SIGHUP, None)

                # Test reading state from multiple threads
                shutdown_state = signal_handler.is_shutdown_requested()
                reload_state = signal_handler.is_reload_requested()

                results.append((thread_id, shutdown_state, reload_state))
            except Exception as e:
                results.append((thread_id, f"error: {e}", None))

        # Start multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all threads completed without errors
        assert len(results) == 10
        for result in results:
            thread_id, shutdown_state, reload_state = result
            assert not str(shutdown_state).startswith("error")

    def test_session_summary_calculation(self):
        """Test session summary calculation and formatting."""
        import time

        # Simulate session timing
        session_start = time.time()
        time.sleep(0.01)  # Brief delay
        session_end = time.time()
        total_runtime = session_end - session_start

        # Format runtime display
        hours, remainder = divmod(int(total_runtime), 3600)
        minutes, seconds = divmod(remainder, 60)
        runtime_display = f"{hours}h {minutes}m {seconds}s"

        # Verify formatting
        assert "h" in runtime_display
        assert "m" in runtime_display
        assert "s" in runtime_display

        # Test with longer runtime
        long_runtime = 3661  # 1h 1m 1s
        hours, remainder = divmod(int(long_runtime), 3600)
        minutes, seconds = divmod(remainder, 60)
        long_display = f"{hours}h {minutes}m {seconds}s"

        assert long_display == "1h 1m 1s"

    @pytest.mark.skip(reason="Requires actual processing pipeline to test shutdown sequence")
    def test_full_shutdown_sequence_integration(self):
        """Integration test for full shutdown sequence with real components.

        This test would require:
        - Actual RTSP client connection
        - Database operations
        - Metrics collection
        - Log file operations

        Currently skipped as it requires full system setup.
        """
        # TODO: Implement when full integration environment is available
        pass

    def test_signal_handler_with_config_override(self):
        """Test signal handler works with config file overrides."""
        config_content = """
camera_rtsp_url: "rtsp://test:test@127.0.0.1:554/test"
camera_id: "test_camera"
motion_threshold: 0.3
frame_sample_rate: 10
coreml_model_path: "models/test.mlmodel"
blacklist_objects: ["test"]
min_object_confidence: 0.5
ollama_base_url: "http://localhost:11434"
ollama_model: "test"
llm_timeout: 10
db_path: ":memory:"
max_storage_gb: 2.0
min_retention_days: 14
log_level: "DEBUG"
metrics_interval: 30
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            # Load config with overrides
            config = load_config(config_path)

            # Verify config was loaded correctly
            assert config.motion_threshold == 0.3
            assert config.frame_sample_rate == 10
            assert config.max_storage_gb == 2.0
            assert config.log_level == "DEBUG"

            # Test signal handler still works
            signal_handler = SignalHandler()
            signal_handler.register_handlers()

            signal_handler._handle_shutdown_signal(signal.SIGINT, None)
            assert signal_handler.is_shutdown_requested()

        finally:
            os.unlink(config_path)