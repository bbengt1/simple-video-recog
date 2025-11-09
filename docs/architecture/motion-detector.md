# Motion Detector

**Responsibility:** Analyzes frames to detect motion using background subtraction algorithm. Only frames with significant motion trigger downstream processing.

**Key Interfaces:**
- `detect_motion(frame: np.ndarray) -> tuple[bool, float, np.ndarray]`: Returns (has_motion, confidence_score, motion_mask)
- `reset_background() -> None`: Reset background model (called when camera moves)

**Dependencies:**
- OpenCV (cv2.createBackgroundSubtractorMOG2)
- SystemConfig (for motion_threshold parameter)

**Technology Stack:**
- Python 3.10+, OpenCV 4.8.1+ (MOG2 background subtraction)
- Module path: `core/motion_detector.py`
- Class: `MotionDetector`

**Implementation Notes:**
- Uses MOG2 algorithm with history=500 frames, varThreshold=16
- Confidence calculated as percentage of changed pixels above threshold
- Motion detected if confidence >= motion_threshold from config
- First 100 frames used to build initial background model (no motion detection)

---
