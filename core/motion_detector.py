"""Motion detection module using OpenCV background subtraction.

This module implements motion detection using the MOG2 (Mixture of Gaussians)
background subtraction algorithm, which handles lighting changes and shadows
effectively.
"""

import logging

import cv2
import numpy as np

from core.config import SystemConfig

logger = logging.getLogger(__name__)


class MotionDetector:
    """Detects motion in video frames using background subtraction.

    This class uses OpenCV's BackgroundSubtractorMOG2 algorithm to detect
    motion in video frames. The algorithm learns a background model over the
    first 100 frames and then identifies pixels that differ significantly
    from the background as motion.

    Attributes:
        config: System configuration containing motion detection parameters
        bg_subtractor: OpenCV MOG2 background subtractor instance
        motion_threshold: Threshold for motion detection (0.0-1.0)
        frame_count: Number of frames processed (for learning phase)
        learning_frames: Number of frames to use for learning background (100)
    """

    def __init__(self, config: SystemConfig) -> None:
        """Initialize motion detector with configuration.

        Args:
            config: SystemConfig instance with motion detection parameters
        """
        self.config = config
        self.motion_threshold = config.motion_threshold
        self.frame_count = 0
        self.learning_frames = 100

        # Initialize MOG2 background subtractor
        # history=500: Number of last frames affecting background model
        # varThreshold=16: Threshold on squared Mahalanobis distance
        # detectShadows=True: Detect and filter shadow movement
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=16, detectShadows=True
        )

        logger.info(
            f"MotionDetector initialized with threshold: {self.motion_threshold}",
            extra={"motion_threshold": self.motion_threshold},
        )

    def detect_motion(
        self, frame: np.ndarray
    ) -> tuple[bool, float, np.ndarray]:
        """Detect motion in video frame using background subtraction.

        During the first 100 frames, the background model is being learned,
        so this method will always return (False, 0.0, empty_mask).

        Args:
            frame: OpenCV frame in BGR format (numpy array)

        Returns:
            Tuple of:
            - has_motion (bool): True if motion exceeds threshold
            - confidence (float): Percentage of frame with motion (0.0-1.0)
            - motion_mask (np.ndarray): Binary mask of detected motion
        """
        self.frame_count += 1

        # Apply background subtraction to generate foreground mask
        fg_mask = self.bg_subtractor.apply(frame)

        # During learning phase (first 100 frames), return no motion
        if self.frame_count <= self.learning_frames:
            empty_mask = np.zeros_like(fg_mask)
            return False, 0.0, empty_mask

        # Count non-zero pixels (detected motion pixels)
        motion_pixels = np.count_nonzero(fg_mask)

        # Calculate confidence as percentage of frame with motion
        total_pixels = fg_mask.shape[0] * fg_mask.shape[1]
        confidence = motion_pixels / total_pixels

        # Determine if motion threshold exceeded
        has_motion = confidence >= self.motion_threshold

        return has_motion, confidence, fg_mask

    def reset_background(self) -> None:
        """Reset background model and restart learning phase.

        This method creates a new BackgroundSubtractorMOG2 instance,
        which discards the learned background model and resets the
        frame counter to restart the 100-frame learning phase.

        Use this when the camera moves or when a major scene change occurs.
        """
        # Create new background subtractor instance
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=16, detectShadows=True
        )

        # Reset frame counter to restart learning phase
        self.frame_count = 0

        logger.info("Background model reset")
