"""Frame sampling and processing pipeline module.

This module provides the FrameSampler class for configurable frame sampling
and the ProcessingPipeline class for orchestrating the complete video processing workflow.
"""

import signal
import sys
from datetime import datetime
from typing import Dict, Optional

import numpy as np

from apple_platform.coreml_detector import CoreMLDetector
from core.config import SystemConfig
from core.events import EventDeduplicator
from core.exceptions import VideoRecognitionError
from core.image_annotator import ImageAnnotator
from core.logging_config import get_logger
from core.motion_detector import MotionDetector
from integrations.ollama import OllamaClient
from integrations.rtsp_client import RTSPCameraClient

logger = get_logger(__name__)

# Processing pipeline stages for tracking and debugging
STAGE_MOTION = "motion_detection"
STAGE_SAMPLING = "frame_sampling"
STAGE_DETECTION = "object_detection"
STAGE_DEDUPLICATION = "event_deduplication"
STAGE_LLM = "llm_inference"
STAGE_EVENT = "event_creation"


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
        coreml_detector: CoreMLDetector,
        event_deduplicator: EventDeduplicator,
        ollama_client: OllamaClient,
        image_annotator: ImageAnnotator,
        config: SystemConfig,
    ):
        """Initialize processing pipeline with all components.

        Args:
            rtsp_client: RTSP camera client for frame capture
            motion_detector: Motion detection component
            frame_sampler: Frame sampling component
            coreml_detector: CoreML object detection component
            event_deduplicator: Event deduplication component
            ollama_client: LLM semantic description component
            image_annotator: Image annotation component
            config: System configuration
        """
        self.rtsp_client = rtsp_client
        self.motion_detector = motion_detector
        self.frame_sampler = frame_sampler
        self.coreml_detector = coreml_detector
        self.event_deduplicator = event_deduplicator
        self.ollama_client = ollama_client
        self.image_annotator = image_annotator
        self.config = config

        # Metrics tracking
        self.metrics = {
            "total_frames_captured": 0,
            "frames_with_motion": 0,
            "frames_sampled": 0,
            "frames_processed": 0,
            "objects_detected": 0,
            "events_created": 0,
            "events_suppressed": 0,
            "coreml_time_avg": 0.0,
            "llm_time_avg": 0.0,
        }
        # Internal counters for average calculations
        self._coreml_operations = 0
        self._llm_operations = 0

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
                    logger.info(f"Motion detected: frame={self.metrics['frames_with_motion']}, confidence={confidence:.3f}")

                    # Apply sampling to motion-triggered frames
                    if self.frame_sampler.should_process(self.metrics["frames_with_motion"]):
                        self.metrics["frames_sampled"] += 1

                        # Stage 3: Object detection (CoreML)
                        import time
                        detection_start = time.time()
                        try:
                            detected_objects = self.coreml_detector.detect_objects(frame)
                            detection_time = time.time() - detection_start

                            # Create DetectionResult
                            from core.models import DetectionResult
                            detections = DetectionResult(
                                objects=detected_objects,
                                inference_time=detection_time,
                                frame_shape=tuple(frame.shape)
                            )

                            self.metrics["objects_detected"] += len(detections.objects)
                            self.metrics["frames_processed"] += 1

                            # Update CoreML timing average
                            self._coreml_operations += 1
                            self.metrics["coreml_time_avg"] = (
                                (self.metrics["coreml_time_avg"] * (self._coreml_operations - 1)) +
                                detections.inference_time
                            ) / self._coreml_operations

                            logger.debug(
                                f"Object detection: objects={len(detections.objects)}, "
                                f"inference_time={detections.inference_time:.3f}s"
                            )
                        except Exception as e:
                            logger.warning(f"CoreML detection failed: {e}")
                            continue  # Skip frame if detection fails

                        # Skip if no objects detected
                        if not detections.objects:
                            logger.debug("No objects detected")
                            continue

                        # Stage 4: Event deduplication
                        if not self.event_deduplicator.should_create_event(detections):
                            self.metrics["events_suppressed"] += 1
                            logger.debug("Event suppressed by deduplication logic")
                            continue

                        # Stage 5: LLM semantic description
                        llm_start = time.time()
                        llm_time = 0.0
                        try:
                            description = self.ollama_client.generate_description(frame, detections)
                            llm_time = time.time() - llm_start

                            # Update LLM timing average
                            self._llm_operations += 1
                            self.metrics["llm_time_avg"] = (
                                (self.metrics["llm_time_avg"] * (self._llm_operations - 1)) +
                                llm_time
                            ) / self._llm_operations

                            logger.debug(f"LLM description generated: {description[:50]}...")
                        except Exception as e:
                            logger.warning(f"LLM inference failed: {e}, using fallback description")
                            description = f"Detected: {', '.join(obj.label for obj in detections.objects)}"

                        # Stage 6: Event creation and output
                        try:
                            # Generate event ID and create Event object
                            from core.events import Event
                            from datetime import timezone
                            event_id = Event.generate_event_id()
                            now = datetime.now(timezone.utc)
                            event = Event(
                                event_id=event_id,
                                timestamp=now,
                                camera_id=self.config.camera_id,
                                motion_confidence=confidence,
                                detected_objects=detections.objects,
                                llm_description=description,
                                image_path=f"data/events/{now.date()}/{event_id}.jpg",
                                json_log_path=f"data/events/{now.date()}/events.json",
                                metadata={
                                    "coreml_inference_time": detections.inference_time,
                                    "llm_inference_time": llm_time if 'llm_time' in locals() else 0.0,
                                    "frame_number": self.metrics["frames_with_motion"],
                                    "motion_threshold_used": self.config.motion_threshold,
                                }
                            )

                            # Annotate and save image
                            annotated_frame = self.image_annotator.annotate(frame, detections.objects)
                            # TODO: Save annotated image to disk (implemented in Epic 3)

                            # Output Event JSON (console for now, file in Epic 3)
                            print(event.to_json())  # Console output as specified

                            self.metrics["events_created"] += 1
                            logger.info(f"Event created: {event_id}, objects={len(detections.objects)}")

                        except Exception as e:
                            logger.error(f"Event creation failed: {e}")
                            continue

        except Exception as e:
            logger.error(f"Error in processing pipeline: {e}", exc_info=True)
            raise VideoRecognitionError(f"Processing pipeline error: {e}") from e

        finally:
            # Log final metrics summary
            logger.info("Metrics summary: "
                       f"frames_captured={self.metrics['total_frames_captured']}, "
                       f"motion_detected={self.metrics['frames_with_motion']}, "
                       f"frames_sampled={self.metrics['frames_sampled']}, "
                       f"frames_processed={self.metrics['frames_processed']}, "
                       f"objects_detected={self.metrics['objects_detected']}, "
                       f"events_created={self.metrics['events_created']}, "
                       f"events_suppressed={self.metrics['events_suppressed']}, "
                       f"coreml_time_avg={self.metrics['coreml_time_avg']:.3f}s, "
                       f"llm_time_avg={self.metrics['llm_time_avg']:.3f}s")

            # Calculate and log percentages
            if self.metrics["total_frames_captured"] > 0:
                motion_rate = (self.metrics["frames_with_motion"] / self.metrics["total_frames_captured"]) * 100
                logger.info(f"Motion detection rate: {motion_rate:.1f}%")

            if self.metrics["frames_with_motion"] > 0:
                sample_rate = (self.metrics["frames_sampled"] / self.metrics["frames_with_motion"]) * 100
                logger.info(f"Sampling effectiveness: {sample_rate:.1f}%")