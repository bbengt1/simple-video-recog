"""Signal handling module for graceful shutdown and hot-reload functionality."""

import signal
import threading
import time
from typing import Optional

from core.logging_config import get_logger

logger = get_logger(__name__)


class SignalHandler:
    """Handles system signals for graceful shutdown and configuration reload.

    Provides thread-safe signal handling using threading.Event objects to communicate
    with the main processing loop without race conditions.
    """

    def __init__(self):
        """Initialize signal handler with thread-safe event objects."""
        self.shutdown_event = threading.Event()
        self.reload_event = threading.Event()
        self._shutdown_requested = False
        self._reload_requested = False

    def register_handlers(self) -> None:
        """Register signal handlers for SIGINT, SIGTERM, and SIGHUP.

        SIGINT/SIGTERM: Trigger graceful shutdown
        SIGHUP: Trigger configuration reload without restart
        """
        signal.signal(signal.SIGINT, self._handle_shutdown_signal)
        signal.signal(signal.SIGTERM, self._handle_shutdown_signal)
        signal.signal(signal.SIGHUP, self._handle_reload_signal)

        logger.info("Signal handlers registered: SIGINT, SIGTERM, SIGHUP")

    def _handle_shutdown_signal(self, signum: int, frame) -> None:
        """Handle shutdown signals (SIGINT, SIGTERM)."""
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"

        if self._shutdown_requested:
            logger.warning(f"{signal_name} received - shutdown already in progress")
            return

        self._shutdown_requested = True
        logger.info(f"Received {signal_name}, initiating graceful shutdown...")
        self.shutdown_event.set()

    def _handle_reload_signal(self, signum: int, frame) -> None:
        """Handle configuration reload signal (SIGHUP)."""
        if self._reload_requested:
            logger.warning("SIGHUP received - reload already in progress")
            return

        self._reload_requested = True
        logger.info("Received SIGHUP, reloading configuration...")
        self.reload_event.set()

        # Reset reload flag after a short delay to allow processing
        def reset_reload_flag():
            time.sleep(0.1)  # Brief delay to allow reload processing
            self._reload_requested = False

        threading.Thread(target=reset_reload_flag, daemon=True).start()

    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested."""
        return self.shutdown_event.is_set()

    def is_reload_requested(self) -> bool:
        """Check if configuration reload has been requested."""
        return self.reload_event.is_set()

    def clear_reload_flag(self) -> None:
        """Clear the reload event flag after processing."""
        self.reload_event.clear()
        self._reload_requested = False

    def wait_for_shutdown(self, timeout: Optional[float] = None) -> bool:
        """Wait for shutdown signal with optional timeout.

        Args:
            timeout: Maximum time to wait in seconds, None for indefinite wait

        Returns:
            True if shutdown was requested, False if timeout expired
        """
        return self.shutdown_event.wait(timeout)