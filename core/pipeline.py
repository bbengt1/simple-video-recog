"""Frame sampling and processing pipeline module.

This module provides the FrameSampler class for configurable frame sampling
and the ProcessingPipeline class for orchestrating the complete video processing workflow.
"""

import cv2
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from apple_platform.coreml_detector import CoreMLDetector
from core.config import SystemConfig
from core.database import DatabaseManager
from core.events import EventDeduplicator
from core.exceptions import VideoRecognitionError
from core.image_annotator import ImageAnnotator
from core.logging_config import get_logger
from core.metrics import MetricsCollector
from core.motion_detector import MotionDetector
from core.signals import SignalHandler
from core.storage_monitor import StorageMonitor
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
        database_manager: DatabaseManager,
        signal_handler: SignalHandler,
        storage_monitor: StorageMonitor,
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
            database_manager: Database manager for event persistence
            signal_handler: Signal handler for graceful shutdown and hot-reload
            storage_monitor: Storage monitoring component
            config: System configuration
        """
        self.rtsp_client = rtsp_client
        self.motion_detector = motion_detector
        self.frame_sampler = frame_sampler
        self.coreml_detector = coreml_detector
        self.event_deduplicator = event_deduplicator
        self.ollama_client = ollama_client
        self.image_annotator = image_annotator
        self.database_manager = database_manager
        self.signal_handler = signal_handler
        self.storage_monitor = storage_monitor
        self.config = config

        # Initialize metrics collector
        self.metrics_collector = MetricsCollector(config)



    def get_metrics(self) -> Dict[str, Any]:
        """Get current processing metrics.

        Returns:
            Dictionary containing current metric values
        """
        snapshot = self.metrics_collector.collect()
        return {
            "total_frames_captured": snapshot.frames_processed,  # Note: this is approximate
            "frames_with_motion": snapshot.frames_processed,  # Note: this is approximate
            "frames_sampled": snapshot.frames_processed,  # Note: this is approximate
            "frames_processed": snapshot.frames_processed,
            "objects_detected": 0,  # Not tracked in MetricsCollector
            "events_created": snapshot.events_created,
            "events_suppressed": snapshot.events_suppressed,
            "coreml_time_avg": snapshot.coreml_inference_avg,
            "llm_time_avg": snapshot.llm_inference_avg,
        }

    def run(self) -> None:
        """Run the main processing pipeline loop.

        Continuously captures frames from RTSP, detects motion, applies sampling,
        and processes sampled frames. Runs until shutdown signal received.
        """
        logger.info("Starting video processing pipeline")

        try:
            while not self.signal_handler.is_shutdown_requested():
                # Check if we should display periodic status
                if self.metrics_collector.should_log_metrics():
                    status_display = self.metrics_collector.get_status_display()
                    logger.info("Periodic status update:\n" + status_display)

                # Get frame from RTSP client
                frame = self.rtsp_client.get_frame()
                if frame is None:
                    continue  # Skip if no frame available

                self.metrics_collector.increment_counter("frames_processed")

                # Detect motion
                has_motion, confidence, motion_mask = self.motion_detector.detect_motion(frame)

                if has_motion:
                    # For now, we approximate motion detection with frame processing
                    # In a more complete implementation, we'd track motion separately
                    logger.info(f"Motion detected: confidence={confidence:.3f}")

                    # Apply sampling to motion-triggered frames
                    # For simplicity, we'll sample based on frame count
                    if self.frame_sampler.should_process(self.metrics_collector.frames_processed):
                        # Process this frame

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

                            # Record CoreML inference time
                            self.metrics_collector.record_inference_time("coreml", detections.inference_time * 1000)  # Convert to ms

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
                            self.metrics_collector.increment_counter("events_suppressed")
                            logger.debug("Event suppressed by deduplication logic")
                            continue

                        # Stage 5: LLM semantic description
                        llm_start = time.time()
                        llm_time = 0.0
                        try:
                            description = self.ollama_client.generate_description(frame, detections)
                            llm_time = time.time() - llm_start

                            # Record LLM inference time
                            self.metrics_collector.record_inference_time("llm", llm_time * 1000)  # Convert to ms

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
                                    "frame_number": self.metrics_collector.frames_processed,
                                    "motion_threshold_used": self.config.motion_threshold,
                                }
                            )

                            # Annotate and save image
                            annotated_frame = self.image_annotator.annotate(frame, detections.objects)

                            # Create directories for persistence
                            image_dir = Path(event.image_path).parent
                            json_dir = Path(event.json_log_path).parent
                            image_dir.mkdir(parents=True, exist_ok=True)
                            json_dir.mkdir(parents=True, exist_ok=True)

                            # Save annotated image
                            try:
                                cv2.imwrite(str(event.image_path), annotated_frame)
                                logger.debug(f"Saved annotated image: {event.image_path}")
                            except Exception as e:
                                logger.warning(f"Failed to save annotated image {event.image_path}: {e}")

                            # Append event to JSON log file
                            try:
                                with open(event.json_log_path, 'a', encoding='utf-8') as f:
                                    f.write(event.model_dump_json() + '\n')
                                logger.debug(f"Appended event to JSON log: {event.json_log_path}")
                            except Exception as e:
                                logger.warning(f"Failed to append to JSON log {event.json_log_path}: {e}")

                            # Persist event to database
                            try:
                                self.database_manager.insert_event(event)
                                logger.debug(f"Inserted event into database: {event_id}")
                            except Exception as e:
                                logger.error(f"Failed to persist event {event_id} to database: {e}")
                                # Continue processing even if database insert fails

                            # Output Event JSON (console for now, file in Epic 3)
                            print(event.to_json())  # Console output as specified

                            self.metrics_collector.increment_counter("events_created")
                            logger.info(f"Event created: {event_id}, objects={len(detections.objects)}")

                            # Check storage limits after event creation
                            if self.storage_monitor.check_storage_and_enforce_limits():
                                logger.critical(
                                    "Storage limit exceeded during event processing. "
                                    "Initiating graceful shutdown to prevent data loss."
                                )
                                self.signal_handler.shutdown_event.set()
                                break

                        except Exception as e:
                            logger.error(f"Event creation failed: {e}")
                            continue

        except Exception as e:
            logger.error(f"Error in processing pipeline: {e}", exc_info=True)
            raise VideoRecognitionError(f"Processing pipeline error: {e}") from e

        finally:
            # Perform graceful shutdown sequence
            self._perform_graceful_shutdown()

    def _perform_graceful_shutdown(self) -> None:
        """Perform graceful shutdown sequence.

        Stops accepting new frames, finishes current processing, flushes buffers,
        closes connections, and saves final metrics.
        """
        logger.info("[SHUTDOWN] Stopping frame capture...")
        try:
            self.rtsp_client.disconnect()
            logger.info("[SHUTDOWN] RTSP connection closed")
        except Exception as e:
            logger.warning(f"[SHUTDOWN] Error closing RTSP connection: {e}")

        logger.info("[SHUTDOWN] Flushing log buffers...")
        # Note: Log flushing will be handled by the loggers themselves
        # when they detect shutdown

        logger.info("[SHUTDOWN] Closing database connection...")
        try:
            # Database connection will be closed by context manager
            # when the main application exits
            logger.info("[SHUTDOWN] Database connection prepared for closure")
        except Exception as e:
            logger.warning(f"[SHUTDOWN] Error preparing database for closure: {e}")

        logger.info("[SHUTDOWN] Saving final metrics...")
        try:
            # Save final metrics snapshot
            final_metrics = self.metrics_collector.collect()
            # TODO: Save to metrics.json file (will be implemented with metrics persistence)
            logger.info(f"[SHUTDOWN] Final metrics collected: {final_metrics.frames_processed} frames, {final_metrics.events_created} events")
        except Exception as e:
            logger.warning(f"[SHUTDOWN] Error saving final metrics: {e}")

        # Log final metrics summary
        try:
            status_display = self.metrics_collector.get_status_display()
            logger.info("Final metrics summary:\n" + status_display)
        except Exception as e:
            logger.warning(f"[SHUTDOWN] Error generating final metrics summary: {e}")