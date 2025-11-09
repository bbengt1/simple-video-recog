# Error Logging Standards

## Structured Logging with Context

```python
# core/processing_pipeline.py
import logging

logger = logging.getLogger(__name__)

def process_frame(self, frame: np.ndarray) -> Optional[Event]:
    """Process frame with comprehensive error logging."""
    frame_id = f"frame_{int(time.time() * 1000)}"

    try:
        # Stage 1: Motion detection
        has_motion, confidence = self.motion_detector.detect_motion(frame)

        if not has_motion:
            logger.debug(
                f"No motion detected",
                extra={"frame_id": frame_id, "confidence": confidence}
            )
            return None

        # Stage 2: Object detection
        logger.info(
            f"Motion detected, running object detection",
            extra={"frame_id": frame_id, "motion_confidence": confidence}
        )

        objects = self.object_detector.detect_objects(frame)

        # ... rest of processing

    except CoreMLInferenceError as e:
        # Recoverable error - log and skip frame
        logger.error(
            f"CoreML inference failed, skipping frame",
            exc_info=True,
            extra={
                "frame_id": frame_id,
                "frame_shape": frame.shape,
                "error_type": type(e).__name__
            }
        )
        return None

    except Exception as e:
        # Unexpected error - log with full context
        logger.critical(
            f"Unexpected error in frame processing",
            exc_info=True,
            extra={
                "frame_id": frame_id,
                "frame_shape": frame.shape,
                "pipeline_stage": "unknown",
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        )
        raise
```

## Log Levels

- **DEBUG**: Detailed diagnostic information (motion detection results, frame counts)
- **INFO**: Normal operational messages (event created, pipeline started)
- **WARNING**: Recoverable issues (RTSP reconnection, storage approaching limit)
- **ERROR**: Errors that skip current operation (CoreML inference failed, LLM timeout)
- **CRITICAL**: Fatal errors requiring shutdown (database corruption, config invalid)

---
