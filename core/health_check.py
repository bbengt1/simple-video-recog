"""Health check and status reporting for the video recognition system.

This module provides startup health validation and runtime status display
to ensure system components are properly initialized and functioning.
"""

import logging
from typing import Optional

from .config import SystemConfig
from .motion_detector import MotionDetector
from integrations.rtsp_client import RTSPCameraClient

logger = logging.getLogger(__name__)


class StatusReporter:
    """Reports runtime system status and metrics.

    Displays periodic status updates with human-readable formatting
    showing frames captured, motion detection rates, and system performance.
    """

    def __init__(self, config: SystemConfig):
        """Initialize status reporter.

        Args:
            config: System configuration instance
        """
        self.config = config

    def display_status(self, metrics: dict) -> None:
        """Display formatted runtime status.

        Args:
            metrics: Dictionary containing runtime metrics
        """
        interval = self.config.metrics_interval

        # Extract metrics with defaults
        frames_captured = metrics.get('frames_captured', 0)
        motion_detected = metrics.get('motion_detected', 0)
        frames_sampled = metrics.get('frames_sampled', 0)
        queue_size = metrics.get('queue_size', 0)
        queue_max = metrics.get('queue_max', 100)
        elapsed_time = metrics.get('elapsed_time', 1.0)  # Avoid division by zero
        frame_sample_rate = metrics.get('frame_sample_rate', 1)

        # Calculate derived metrics
        fps = frames_captured / elapsed_time if elapsed_time > 0 else 0
        hit_rate = (motion_detected / frames_captured * 100) if frames_captured > 0 else 0

        # Format status message
        status_message = (
            f"[INFO] Runtime Status ({interval}s interval)\n"
            f"  Frames Captured: {frames_captured:,} ({fps:.1f} fps)\n"
            f"  Motion Detected: {motion_detected:,} ({hit_rate:.1f}% hit rate)\n"
            f"  Frames Sampled: {frames_sampled:,} (sampling rate: 1/{frame_sample_rate})\n"
            f"  Queue Size: {queue_size}/{queue_max}"
        )

        logger.info(status_message)


class HealthChecker:
    """Performs startup health checks on system components.

    Validates configuration, RTSP connectivity, motion detector initialization,
    and frame queue status before allowing system startup.
    """

    def __init__(
        self,
        config: SystemConfig,
        rtsp_client: RTSPCameraClient,
        motion_detector: MotionDetector
    ):
        """Initialize health checker with dependencies.

        Args:
            config: System configuration instance
            rtsp_client: RTSP camera client instance
            motion_detector: Motion detector instance
        """
        self.config = config
        self.rtsp_client = rtsp_client
        self.motion_detector = motion_detector

    def _check_config(self) -> tuple[bool, str]:
        """Check if configuration is valid.

        Returns:
            Tuple of (success, message)
        """
        # Basic config validation - config is already validated by Pydantic
        # during construction, so we just confirm it exists
        try:
            # Verify required fields are present
            if not self.config.camera_rtsp_url:
                return False, "✗ Configuration invalid: camera_rtsp_url is required"
            if not self.config.camera_id:
                return False, "✗ Configuration invalid: camera_id is required"

            return True, f"✓ Configuration loaded: {self.config.camera_id}"
        except Exception as e:
            return False, f"✗ Configuration check failed: {str(e)}"

    def _check_rtsp_connection(self) -> tuple[bool, str]:
        """Check RTSP camera connection status.

        Returns:
            Tuple of (success, message)
        """
        try:
            if self.rtsp_client.is_connected():
                camera_id = self.config.camera_id
                return True, f"✓ RTSP stream: Connected ({camera_id})"
            else:
                return False, f"✗ RTSP stream: Not connected ({self.config.camera_id})"
        except Exception as e:
            logger.error(f"RTSP connection check failed: {e}", exc_info=True)
            return False, f"✗ RTSP connection failed: {str(e)}"

    def _check_motion_detector(self) -> tuple[bool, str]:
        """Check motion detector initialization status.

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if motion detector has required attributes initialized
            if hasattr(self.motion_detector, 'bg_subtractor') and self.motion_detector.bg_subtractor is not None:
                return True, "✓ Motion detector: Initialized"
            else:
                return False, "✗ Motion detector: Not initialized"
        except Exception as e:
            logger.error(f"Motion detector check failed: {e}", exc_info=True)
            return False, f"✗ Motion detector check failed: {str(e)}"

    def _check_frame_queue(self) -> tuple[bool, str]:
        """Check frame queue status.

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if RTSP client has frame_queue attribute
            if hasattr(self.rtsp_client, 'frame_queue') and self.rtsp_client.frame_queue is not None:
                queue_size = self.rtsp_client.frame_queue.qsize()
                max_size = self.rtsp_client.frame_queue.maxsize
                return True, f"✓ Frame queue: Ready ({queue_size}/{max_size})"
            else:
                return False, "✗ Frame queue: Not initialized"
        except Exception as e:
            logger.error(f"Frame queue check failed: {e}", exc_info=True)
            return False, f"✗ Frame queue check failed: {str(e)}"

    def run_checks(self) -> bool:
        """Run all system health checks.

        Checks are performed in order:
        1. Configuration validation
        2. RTSP connection
        3. Motion detector initialization
        4. Frame queue status

        Returns:
            True if all checks pass, False if any check fails
        """
        logger.info("===== System Health Check =====")

        checks = [
            self._check_config,
            self._check_rtsp_connection,
            self._check_motion_detector,
            self._check_frame_queue,
        ]

        all_passed = True

        for check in checks:
            success, message = check()
            logger.info(message)
            if not success:
                all_passed = False

        if all_passed:
            logger.info("===== System Ready =====")
            return True
        else:
            logger.error("===== System NOT Ready =====")
            return False