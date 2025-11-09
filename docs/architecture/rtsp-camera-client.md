# RTSP Camera Client

**Responsibility:** Establishes and maintains connection to RTSP camera stream, captures frames, and provides frame iterator for the processing pipeline.

**Key Interfaces:**
- `connect() -> bool`: Establish RTSP connection, returns True if successful
- `get_frame() -> np.ndarray | None`: Capture single frame, returns None if connection lost
- `disconnect() -> None`: Gracefully close RTSP connection
- `is_connected() -> bool`: Check connection status

**Dependencies:**
- OpenCV (cv2.VideoCapture for RTSP client)
- SystemConfig (for RTSP URL and camera settings)

**Technology Stack:**
- Python 3.10+, OpenCV 4.8.1+
- Module path: `integrations/rtsp_client.py`
- Class: `RTSPCameraClient`

**Implementation Notes:**
- Implements automatic reconnection with exponential backoff (1s, 2s, 4s, 8s max)
- Logs WARNING on connection failure, ERROR after 5 consecutive failures
- Frame capture timeout: 5 seconds (raises TimeoutError if exceeded)
- Validates frame is not empty/corrupted before returning

---
