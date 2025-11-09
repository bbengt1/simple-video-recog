"""Frame sampling and processing pipeline module.

This module provides the FrameSampler class for configurable frame sampling
and the ProcessingPipeline class for orchestrating the complete video processing workflow.
"""

import logging
import signal
import sys
from typing import Dict, Optional

import numpy as np

from core.config import SystemConfig
from core.exceptions import VideoRecognitionError
from core.motion_detector import MotionDetector
from integrations.rtsp_client import RTSPCameraClient

logger = logging.getLogger(__name__)


class FrameSampler:
    """Configurable frame sampler for optimizing processing performance.

    This class implements sampling logic to process every Nth frame,
    reducing computational load while maintaining adequate coverage.
    Sampling is applied after motion detection to only sample motion-triggered frames.
    """

    def __init__(self, config: SystemConfig):
        """Initialize frame sampler with configuration.

        Args:
            config: SystemConfig instance containing frame_sample_rate parameter
        """
        self.frame_sample_rate = config.frame_sample_rate

    def should_process(self, frame_count: int) -> bool:
        """Determine if a frame should be processed based on sampling rate.

        Args:
            frame_count: Continuously incrementing counter of total frames captured

        Returns:
            True if frame should be processed, False otherwise
        """
        return (frame_count % self.frame_sample_rate) == 0


class ProcessingPipeline:
    """Orchestrates the complete video processing pipeline.

    Coordinates RTSP frame capture, motion detection, frame sampling,
    and future object detection stages. Maintains comprehensive metrics
    and handles graceful shutdown.
    """

    def __init__(
        self,
        rtsp_client: RTSPCameraClient,
        motion_detector: MotionDetector,
        frame_sampler: FrameSampler,
        config: SystemConfig,
    ):
        """Initialize processing pipeline with all components.

        Args:
            rtsp_client: RTSP camera client for frame capture
            motion_detector: Motion detection component
            frame_sampler: Frame sampling component
            config: System configuration
        """
        self.rtsp_client = rtsp_client
        self.motion_detector = motion_detector
        self.frame_sampler = frame_sampler
        self.config = config

        # Metrics tracking
        self.metrics = {
            "total_frames_captured": 0,
            "frames_with_motion": 0,
            "frames_sampled": 0,
            "frames_processed": 0,
        }

        # Shutdown handling
        self._shutdown_requested = False
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info("Shutdown signal received, initiating graceful shutdown...")
        self._shutdown_requested = True

    def get_metrics(self) -> Dict[str, int]:
        """Get current processing metrics.

        Returns:
            Dictionary containing all metric counters
        """
        return self.metrics.copy()

    def run(self) -> None:
        """Run the main processing pipeline loop.

        Continuously captures frames from RTSP, detects motion, applies sampling,
        and processes sampled frames. Runs until shutdown signal received.
        """
        logger.info("Starting video processing pipeline")

        try:
            while not self._shutdown_requested:
                # Get frame from RTSP client
                frame = self.rtsp_client.get_frame()
                if frame is None:
                    continue  # Skip if no frame available

                self.metrics["total_frames_captured"] += 1

                # Detect motion
                has_motion, confidence, motion_mask = self.motion_detector.detect_motion(frame)

                if has_motion:
                    self.metrics["frames_with_motion"] += 1

                    # Apply sampling to motion-triggered frames
                    if self.frame_sampler.should_process(self.metrics["frames_with_motion"]):
                        self.metrics["frames_sampled"] += 1

                        # TODO: Future object detection will go here
                        # For now, just increment processed counter
                        self.metrics["frames_processed"] += 1

                        logger.debug(
                            f"Processed frame {self.metrics['frames_with_motion']} "
                            f"(sampled {self.metrics['frames_sampled']}, "
                            f"motion confidence: {confidence:.3f})"
                        )

        except Exception as e:
            logger.error(f"Error in processing pipeline: {e}", exc_info=True)
            raise VideoRecognitionError(f"Processing pipeline error: {e}") from e

        finally:
            # Log final metrics
            logger.info("Processing pipeline shutdown - Final metrics:")
            logger.info(f"  Total frames captured: {self.metrics['total_frames_captured']}")
            logger.info(f"  Frames with motion: {self.metrics['frames_with_motion']}")
            logger.info(f"  Frames sampled: {self.metrics['frames_sampled']}")
            logger.info(f"  Frames processed: {self.metrics['frames_processed']}")

            # Calculate percentages
            if self.metrics["total_frames_captured"] > 0:
                motion_rate = (self.metrics["frames_with_motion"] / self.metrics["total_frames_captured"]) * 100
                logger.info(f"  Motion detection rate: {motion_rate:.1f}%")

            if self.metrics["frames_with_motion"] > 0:
                sample_rate = (self.metrics["frames_sampled"] / self.metrics["frames_with_motion"]) * 100
                logger.info(f"  Sampling effectiveness: {sample_rate:.1f}%")