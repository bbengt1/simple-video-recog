"""RTSP Camera Client for capturing video frames from IP cameras."""

# Standard library imports
import logging
import queue
import threading
import time

# Third-party imports
import cv2
import numpy as np

# Local application imports
from core.config import SystemConfig
from core.exceptions import RTSPConnectionError

logger = logging.getLogger(__name__)


class RTSPCameraClient:
    """RTSP camera client for establishing connection and capturing frames.

    This client handles RTSP stream connections, frame capture, and automatic
    reconnection with exponential backoff. Frame capture runs in a background
    thread to avoid blocking the main processing loop.

    Attributes:
        config: SystemConfig instance containing camera_rtsp_url and camera_id
        rtsp_url: RTSP stream URL with embedded credentials
        camera_id: Camera identifier for logging
        cap: OpenCV VideoCapture instance (None when disconnected)
        frame_queue: Thread-safe queue buffering captured frames (max 100)
        capture_thread: Background thread for continuous frame capture
        _stop_capture: Event flag to stop background thread
    """

    def __init__(self, config: SystemConfig):
        """Initialize RTSP camera client.

        Args:
            config: SystemConfig instance with camera_rtsp_url and camera_id fields
        """
        self.config = config
        self.rtsp_url = config.camera_rtsp_url
        self.camera_id = config.camera_id
        self.cap = None
        self.frame_queue = queue.Queue(maxsize=100)
        self.capture_thread = None
        self._stop_capture = threading.Event()

    def connect(self) -> bool:
        """Establish connection to RTSP camera stream.

        Creates an OpenCV VideoCapture instance with the configured RTSP URL
        and verifies the connection is successfully opened.

        Returns:
            True if connection successful, False otherwise

        Raises:
            RTSPConnectionError: If connection fails (invalid URL, network timeout,
                authentication failure, or camera unreachable)
        """
        try:
            self.cap = cv2.VideoCapture(self.rtsp_url)

            if not self.cap.isOpened():
                raise RTSPConnectionError(
                    f"Failed to connect to RTSP stream for camera '{self.camera_id}'. "
                    f"Verify camera URL, credentials, and network connectivity."
                )

            logger.info(
                f"Connected to RTSP stream: {self.camera_id}",
                extra={"camera_id": self.camera_id}
            )
            return True

        except Exception as e:
            if isinstance(e, RTSPConnectionError):
                raise
            raise RTSPConnectionError(
                f"RTSP connection error for camera '{self.camera_id}': {str(e)}"
            )

    def disconnect(self) -> None:
        """Gracefully close RTSP connection and release resources.

        Releases the OpenCV VideoCapture object and sets it to None.
        Safe to call even if not currently connected.
        """
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            logger.info(
                f"Disconnected from RTSP stream: {self.camera_id}",
                extra={"camera_id": self.camera_id}
            )

    def is_connected(self) -> bool:
        """Check if currently connected to RTSP stream.

        Returns:
            True if connected and stream is open, False otherwise
        """
        if self.cap is None:
            return False
        return self.cap.isOpened()

    def get_frame(self) -> np.ndarray | None:
        """Capture a single frame from the RTSP stream.

        Returns:
            Numpy array in BGR format if frame captured successfully,
            None if stream unavailable or frame invalid

        Note:
            Returns None (rather than raising exception) to allow graceful
            handling of temporary connection issues and reconnection logic.
        """
        if not self.is_connected():
            return None

        ret, frame = self.cap.read()

        if not ret or frame is None or frame.size == 0:
            return None

        return frame

    def start_capture(self) -> None:
        """Start background thread for continuous frame capture.

        Creates and starts a daemon thread running _capture_loop() which
        continuously captures frames and adds them to the frame queue.
        """
        if self.capture_thread is not None and self.capture_thread.is_alive():
            logger.warning(
                f"Capture thread already running for camera: {self.camera_id}",
                extra={"camera_id": self.camera_id}
            )
            return

        self._stop_capture.clear()
        self.capture_thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
            name=f"RTSPCapture-{self.camera_id}"
        )
        self.capture_thread.start()
        logger.info(
            f"Started capture thread for camera: {self.camera_id}",
            extra={"camera_id": self.camera_id}
        )

    def stop_capture(self) -> None:
        """Stop background frame capture thread.

        Signals the capture thread to stop and waits for it to exit.
        """
        if self.capture_thread is None or not self.capture_thread.is_alive():
            return

        self._stop_capture.set()
        self.capture_thread.join(timeout=5.0)
        logger.info(
            f"Stopped capture thread for camera: {self.camera_id}",
            extra={"camera_id": self.camera_id}
        )

    def get_latest_frame(self) -> np.ndarray | None:
        """Retrieve latest frame from the queue.

        Returns:
            Numpy array in BGR format if frame available,
            None if queue is empty
        """
        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return None

    def _capture_loop(self) -> None:
        """Background thread loop for continuous frame capture with reconnection.

        Continuously captures frames from RTSP stream and adds them to queue.
        Implements exponential backoff reconnection on connection loss.
        Exits when _stop_capture event is set or after 5 consecutive failures.
        """
        consecutive_failures = 0
        backoff_delays = [1, 2, 4, 8]  # Exponential backoff sequence in seconds

        while not self._stop_capture.is_set():
            frame = self.get_frame()

            if frame is not None:
                # Successfully captured frame, reset failure counter
                consecutive_failures = 0

                try:
                    # Try to add frame to queue without blocking
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    # Queue full, skip this frame (oldest frames remain)
                    logger.debug(
                        f"Frame queue full for camera: {self.camera_id}, dropping frame",
                        extra={"camera_id": self.camera_id}
                    )

                # Small sleep to control frame rate
                time.sleep(0.033)  # ~30 fps max

            else:
                # Frame capture failed, attempt reconnection
                consecutive_failures += 1

                if consecutive_failures == 1:
                    logger.warning(
                        f"RTSP connection lost for camera: {self.camera_id}",
                        extra={"camera_id": self.camera_id}
                    )

                if consecutive_failures > 5:
                    logger.error(
                        f"Failed to reconnect after 5 attempts for camera: {self.camera_id}. "
                        f"Exiting capture thread.",
                        extra={"camera_id": self.camera_id}
                    )
                    break

                # Calculate backoff delay (cap at 8 seconds)
                delay_index = min(consecutive_failures - 1, len(backoff_delays) - 1)
                delay = backoff_delays[delay_index]

                logger.warning(
                    f"Reconnection attempt {consecutive_failures} for camera: {self.camera_id}. "
                    f"Waiting {delay}s before retry...",
                    extra={"camera_id": self.camera_id, "attempt": consecutive_failures, "delay": delay}
                )

                time.sleep(delay)

                # Attempt reconnection
                try:
                    self.disconnect()
                    if self.connect():
                        logger.info(
                            f"RTSP connection restored for camera: {self.camera_id}",
                            extra={"camera_id": self.camera_id}
                        )
                        consecutive_failures = 0
                except RTSPConnectionError as e:
                    logger.warning(
                        f"Reconnection failed: {str(e)}",
                        extra={"camera_id": self.camera_id}
                    )
