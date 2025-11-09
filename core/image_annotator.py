"""Image annotation module for adding bounding boxes and labels to frames.

This module provides functionality to annotate video frames with detected object
information, including bounding boxes, labels, and confidence scores.
"""

from typing import List

import cv2
import numpy as np

from core.models import DetectedObject


class ImageAnnotator:
    """Annotates frames with bounding boxes and labels for detected objects.

    This class provides methods to draw bounding boxes, labels, and confidence
    scores on video frames for visualization and debugging purposes.
    """

    def annotate(
        self,
        frame: np.ndarray,
        detections: List[DetectedObject]
    ) -> np.ndarray:
        """Annotate frame with bounding boxes and labels for detected objects.

        Draws bounding boxes with color-coded confidence levels and labels
        for each detected object. The original frame is not modified.

        Args:
            frame: OpenCV frame (numpy array) in BGR format
            detections: List of detected objects with bounding boxes

        Returns:
            Annotated frame as numpy array with same dimensions as input

        Raises:
            ValueError: If frame is None or has invalid shape
        """
        # Validate input frame
        if frame is None:
            raise ValueError("Frame cannot be None")
        if len(frame.shape) != 3 or frame.shape[2] != 3:
            raise ValueError(f"Invalid frame shape: {frame.shape}. Expected (H, W, 3)")

        # Create a copy to avoid modifying the original frame
        annotated_frame = frame.copy()

        # If no detections, return unmodified copy
        if not detections:
            return annotated_frame

        # Get frame dimensions for boundary clipping
        frame_height, frame_width = frame.shape[:2]

        # Track used label positions to handle overlapping labels
        used_label_positions = []

        # Annotate each detected object
        for detection in detections:
            # Get color based on confidence threshold
            color = self._get_color_by_confidence(detection.confidence)

            # Clip bounding box to frame boundaries
            x1 = max(0, detection.bbox.x)
            y1 = max(0, detection.bbox.y)
            x2 = min(frame_width, detection.bbox.x + detection.bbox.width)
            y2 = min(frame_height, detection.bbox.y + detection.bbox.height)

            # Draw bounding box rectangle (2-pixel thickness)
            cv2.rectangle(
                annotated_frame,
                (x1, y1),
                (x2, y2),
                color,
                thickness=2
            )

            # Format label text with confidence percentage
            label_text = f"{detection.label} ({int(detection.confidence * 100)}%)"

            # Calculate text size for background rectangle
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 1
            (text_width, text_height), baseline = cv2.getTextSize(
                label_text,
                font,
                font_scale,
                thickness
            )

            # Calculate label position (above bounding box)
            label_x = x1
            label_y = y1 - 10  # 10 pixels above bbox

            # Handle overlapping labels by offsetting vertically
            label_y = self._adjust_label_position(
                label_x,
                label_y,
                text_width,
                text_height,
                used_label_positions
            )

            # Ensure label stays within frame boundaries
            if label_y - text_height < 0:
                label_y = y1 + text_height + 10  # Move below bbox if too high

            # Clip label to frame boundaries
            label_x = max(0, min(label_x, frame_width - text_width))
            label_y = max(text_height, min(label_y, frame_height))

            # Draw semi-transparent black background for text
            # Create overlay for transparency
            overlay = annotated_frame.copy()
            cv2.rectangle(
                overlay,
                (label_x, label_y - text_height - baseline),
                (label_x + text_width, label_y + baseline),
                (0, 0, 0),  # Black background
                cv2.FILLED
            )
            # Blend overlay with original (0.6 alpha for semi-transparency)
            cv2.addWeighted(overlay, 0.6, annotated_frame, 0.4, 0, annotated_frame)

            # Draw label text
            cv2.putText(
                annotated_frame,
                label_text,
                (label_x, label_y),
                font,
                font_scale,
                color,
                thickness,
                cv2.LINE_AA
            )

            # Track this label position
            used_label_positions.append((label_x, label_y, text_width, text_height))

        return annotated_frame

    def _get_color_by_confidence(self, confidence: float) -> tuple:
        """Get BGR color based on confidence threshold.

        Args:
            confidence: Detection confidence score (0.0-1.0)

        Returns:
            Tuple of (B, G, R) color values
        """
        if confidence > 0.8:
            return (0, 255, 0)  # Green for high confidence
        elif confidence >= 0.5:
            return (0, 255, 255)  # Yellow for medium confidence
        else:
            return (0, 0, 255)  # Red for low confidence

    def _adjust_label_position(
        self,
        label_x: int,
        label_y: int,
        text_width: int,
        text_height: int,
        used_positions: List[tuple]
    ) -> int:
        """Adjust label position to avoid overlapping with existing labels.

        Args:
            label_x: X coordinate of label
            label_y: Y coordinate of label
            text_width: Width of label text
            text_height: Height of label text
            used_positions: List of (x, y, width, height) tuples for existing labels

        Returns:
            Adjusted Y coordinate for label
        """
        # Check for overlaps and offset vertically if needed
        offset = 0
        max_iterations = 10  # Prevent infinite loop

        for _ in range(max_iterations):
            overlaps = False
            adjusted_y = label_y + offset

            for used_x, used_y, used_width, used_height in used_positions:
                # Check if rectangles overlap
                if (label_x < used_x + used_width and
                    label_x + text_width > used_x and
                    adjusted_y - text_height < used_y and
                    adjusted_y > used_y - used_height):
                    overlaps = True
                    break

            if not overlaps:
                return adjusted_y

            # Offset by text height + padding
            offset -= (text_height + 5)

        return label_y + offset
