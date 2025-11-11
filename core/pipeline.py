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
from core.event_manager import EventManager
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
        event_manager: EventManager,
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
            event_manager: Event creation and broadcasting manager
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
        self.event_manager = event_manager
        self.ollama_client = ollama_client
        self.image_annotator = image_annotator
        self.database_manager = database_manager
        self.signal_handler = signal_handler
        self.storage_monitor = storage_monitor
        self.config = config

        # Initialize metrics collector
        self.metrics_collector = MetricsCollector(config)

        # Check if CoreML is available to avoid repeated error logs
        self.coreml_available = (
            self.coreml_detector.is_loaded and
            self.coreml_detector.model_metadata and
            self.coreml_detector.model_metadata.get('coreml_available', True)
        )

        if not self.coreml_available:
            logger.info("CoreML framework unavailable - using motion-only detection mode")



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

        # Start RTSP frame capture in background thread
        self.rtsp_client.start_capture()
        logger.info("RTSP frame capture started")

        # Processing rate limiter to prevent 100% CPU usage
        # Use configurable max processing FPS to balance performance and CPU usage
        import time
        import psutil
        base_processing_interval = 1.0 / self.config.max_processing_fps
        processing_interval = base_processing_interval
        last_processing_time = time.time()
        cpu_check_interval = 10  # Check CPU every 10 frames
        frame_count = 0

        try:
            while not self.signal_handler.is_shutdown_requested():
                # Check if we should display periodic status
                if self.metrics_collector.should_log_metrics():
                    status_display = self.metrics_collector.get_status_display()
                    logger.info("Periodic status update:\n" + status_display)

                # Get latest frame from RTSP client queue
                frame = self.rtsp_client.get_latest_frame()
                if frame is None:
                    continue  # Skip if no frame available

                self.metrics_collector.increment_counter("frames_processed")
                frame_count += 1

                # Adaptive CPU-based rate limiting: Check CPU usage every 10 frames
                if frame_count % cpu_check_interval == 0:
                    cpu_percent = psutil.cpu_percent(interval=0.05)
                    if cpu_percent > 75:
                        # Critical CPU: Reduce processing rate significantly
                        processing_interval = max(1.0 / 5.0, base_processing_interval * 3.0)
                        logger.info(f"Critical CPU usage ({cpu_percent:.1f}%), reducing processing rate to {1.0/processing_interval:.1f} FPS")
                    elif cpu_percent > 60:
                        # High CPU: Reduce processing rate moderately
                        processing_interval = max(1.0 / 8.0, base_processing_interval * 2.0)
                        logger.debug(f"High CPU usage ({cpu_percent:.1f}%), reducing processing rate to {1.0/processing_interval:.1f} FPS")
                    elif cpu_percent > 45:
                        # Moderate CPU: Slight reduction
                        processing_interval = max(1.0 / 12.0, base_processing_interval * 1.5)
                        logger.debug(f"Moderate CPU usage ({cpu_percent:.1f}%), reducing processing rate to {1.0/processing_interval:.1f} FPS")
                    else:
                        # Normal CPU: Use base rate
                        processing_interval = base_processing_interval

                # Detect motion (with CPU-aware skipping for high load)
                motion_skip_rate = 1  # Check every frame by default
                if processing_interval > base_processing_interval * 2.0:  # If slowed down significantly (>50% reduction)
                    motion_skip_rate = 3  # Skip 2 out of 3 frames for motion detection
                elif processing_interval > base_processing_interval * 1.5:  # Moderate slowdown
                    motion_skip_rate = 2  # Skip every other frame for motion detection

                has_motion = False
                confidence = 0.0
                motion_mask = None

                if frame_count % motion_skip_rate == 0:
                    has_motion, confidence, motion_mask = self.motion_detector.detect_motion(frame)
                else:
                    # Skip motion detection for this frame to reduce CPU load
                    # Create minimal motion mask (no motion detected)
                    motion_mask = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)

                if has_motion:
                    # For now, we approximate motion detection with frame processing
                    # In a more complete implementation, we'd track motion separately
                    logger.info(f"Motion detected: confidence={confidence:.3f}")

                    # Apply sampling to motion-triggered frames
                    # For simplicity, we'll sample based on frame count
                    if self.frame_sampler.should_process(self.metrics_collector.frames_processed):
                        # Process this frame

                        # Stage 3: Object detection
                        import time
                        detection_start = time.time()
                        detections = None

                        if self.coreml_available:
                            # Use CoreML detection
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
                                logger.warning(f"CoreML detection failed unexpectedly: {e}")
                                # Fall back to motion-only detection
                                self.coreml_available = False  # Disable for future frames
                                logger.info("Disabled CoreML detection due to failure - switching to motion-only mode")

                        # Use motion-only detection (either CoreML unavailable or failed)
                        if not detections:
                            from core.models import DetectionResult, DetectedObject, BoundingBox
                            detection_time = time.time() - detection_start

                            # Create a generic "motion" object to represent detected motion
                            motion_object = DetectedObject(
                                label="motion",
                                confidence=confidence,  # Use motion confidence
                                bbox=BoundingBox(x=0, y=0, width=frame.shape[1], height=frame.shape[0])  # Full frame
                            )

                            detections = DetectionResult(
                                objects=[motion_object],
                                inference_time=detection_time,
                                frame_shape=tuple(frame.shape)
                            )

                            logger.debug(f"Created motion-only event: confidence={confidence:.3f}")

                        # Skip if no detections (shouldn't happen with fallback)
                        if not detections or not detections.objects:
                            logger.debug("No detections available")
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
                            # Generate event ID
                            from core.events import Event
                            from datetime import timezone
                            event_id = Event.generate_event_id()
                            now = datetime.now(timezone.utc)

                            # Annotate and save image
                            annotated_frame = self.image_annotator.annotate(frame, detections.objects)

                            # Create directories for persistence
                            image_path = f"data/events/{now.date()}/{event_id}.jpg"
                            json_log_path = f"data/events/{now.date()}/events.json"
                            image_dir = Path(image_path).parent
                            json_dir = Path(json_log_path).parent
                            image_dir.mkdir(parents=True, exist_ok=True)
                            json_dir.mkdir(parents=True, exist_ok=True)

                            # Save annotated image
                            try:
                                cv2.imwrite(str(image_path), annotated_frame)
                                logger.debug(f"Saved annotated image: {image_path}")
                            except Exception as e:
                                logger.warning(f"Failed to save annotated image {image_path}: {e}")

                            # Append event to JSON log file (for now, will be moved to EventManager later)
                            try:
                                # Create temporary event for JSON logging
                                temp_event = Event(
                                    event_id=event_id,
                                    timestamp=now,
                                    camera_id=self.config.camera_id,
                                    motion_confidence=confidence,
                                    detected_objects=detections.objects,
                                    llm_description=description,
                                    image_path=image_path,
                                    json_log_path=json_log_path,
                                    metadata={
                                        "coreml_inference_time": detections.inference_time,
                                        "llm_inference_time": llm_time if 'llm_time' in locals() else 0.0,
                                        "frame_number": self.metrics_collector.frames_processed,
                                        "motion_threshold_used": self.config.motion_threshold,
                                    }
                                )
                                with open(json_log_path, 'a', encoding='utf-8') as f:
                                    f.write(temp_event.model_dump_json() + '\n')
                                logger.debug(f"Appended event to JSON log: {json_log_path}")
                            except Exception as e:
                                logger.warning(f"Failed to append to JSON log {json_log_path}: {e}")

                            # Create event using EventManager (includes database persistence and WebSocket broadcasting)
                            event = self.event_manager.create_event(
                                event_id=event_id,
                                timestamp=now,
                                camera_id=self.config.camera_id,
                                motion_confidence=confidence,
                                detected_objects=detections.objects,
                                llm_description=description,
                                image_path=image_path,
                                json_log_path=json_log_path,
                                metadata={
                                    "coreml_inference_time": detections.inference_time,
                                    "llm_inference_time": llm_time if 'llm_time' in locals() else 0.0,
                                    "frame_number": self.metrics_collector.frames_processed,
                                    "motion_threshold_used": self.config.motion_threshold,
                                }
                            )

                            if event:
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
                            else:
                                logger.error(f"Event creation failed for {event_id}")

                        except Exception as e:
                            logger.error(f"Event creation failed: {e}")
                            continue

                # Rate limiting: Sleep to maintain target processing rate and reduce CPU usage
                current_time = time.time()
                elapsed = current_time - last_processing_time
                if elapsed < processing_interval:
                    sleep_time = processing_interval - elapsed
                    time.sleep(sleep_time)
                last_processing_time = time.time()

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
            self.rtsp_client.stop_capture()
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