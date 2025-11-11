"""RTSP Camera Client for capturing video frames from IP cameras."""

# Standard library imports
import os
import queue
import threading
import time
from typing import Optional

# Third-party imports
import cv2
import numpy as np

# Local application imports
from core.config import SystemConfig
from core.exceptions import RTSPConnectionError
from core.logging_config import get_logger

logger = get_logger(__name__)


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
        self.cap: Optional[cv2.VideoCapture] = None
        self.frame_queue = queue.Queue(maxsize=100)
        self.capture_thread = None
        self._stop_capture = threading.Event()

        # RTSP-specific settings from config
        self.buffer_size = getattr(config, 'rtsp_buffer_size', 1)
        self.max_reconnect_attempts = getattr(config, 'rtsp_reconnect_attempts', 10)
        self.max_reconnect_delay = getattr(config, 'rtsp_reconnect_delay_max', 8)
        self.connection_timeout = getattr(config, 'rtsp_connection_timeout', 10) * 1000  # Convert to ms
        self.read_timeout = getattr(config, 'rtsp_read_timeout', 5) * 1000  # Convert to ms

    def connect(self) -> bool:
        """Establish connection to RTSP camera stream.

        Creates an OpenCV VideoCapture instance with the configured RTSP URL
        and verifies the connection is successfully opened. Includes timeout
        and buffer configuration for better stability.

        Returns:
            True if connection successful, False otherwise

        Raises:
            RTSPConnectionError: If connection fails (invalid URL, network timeout,
                authentication failure, or camera unreachable)
        """
        try:
            # Set additional OpenCV properties for RTSP stability before opening
            os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = f'rtsp_transport;tcp|buffer_size;{self.buffer_size * 102400}|max_delay;5000000'

            self.cap = cv2.VideoCapture(self.rtsp_url)

            # Configure RTSP connection for better stability
            if self.cap.isOpened():
                # Set buffer size to reduce latency and improve stability
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)

                # Additional RTSP-specific settings
                self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, self.connection_timeout)
                self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, self.read_timeout)

                # Verify we can actually read a frame to ensure connection is working
                ret, test_frame = self.cap.read()
                if not ret or test_frame is None:
                    self.cap.release()
                    self.cap = None
                    raise RTSPConnectionError(
                        f"RTSP stream connected but cannot read frames for camera '{self.camera_id}'. "
                        f"Check camera configuration and stream settings."
                    )

            if not self.cap or not self.cap.isOpened():
                raise RTSPConnectionError(
                    f"Failed to connect to RTSP stream for camera '{self.camera_id}'. "
                    f"Verify camera URL, credentials, and network connectivity."
                )

            logger.info(f"RTSP connected: {self.camera_id}")
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
            logger.info(f"RTSP disconnected: {self.camera_id}")

    def is_connected(self) -> bool:
        """Check if currently connected to RTSP stream.

        Returns:
            True if connected and stream is open, False otherwise
        """
        if self.cap is None:
            return False
        return self.cap.isOpened()

    def test_connectivity(self) -> dict:
        """Test RTSP connectivity and return diagnostic information.

        Returns:
            Dictionary with connectivity test results and metadata
        """
        results = {
            'url': self.rtsp_url,
            'connected': False,
            'frame_size': None,
            'fps': None,
            'codec': None,
            'error': None
        }

        try:
            # Try to connect and read basic stream properties
            temp_cap = cv2.VideoCapture(self.rtsp_url)
            if temp_cap.isOpened():
                results['connected'] = True

                # Get frame size
                width = int(temp_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(temp_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                results['frame_size'] = f"{width}x{height}"

                # Get FPS
                fps = temp_cap.get(cv2.CAP_PROP_FPS)
                results['fps'] = fps if fps > 0 else None

                # Try to read a test frame
                ret, frame = temp_cap.read()
                if ret and frame is not None:
                    results['can_read_frames'] = True
                else:
                    results['can_read_frames'] = False
                    results['error'] = "Cannot read frames from stream"

            else:
                results['error'] = "Failed to open RTSP stream"

            temp_cap.release()

        except Exception as e:
            results['error'] = str(e)

        return results

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

        # At this point, is_connected() returned True, so self.cap is guaranteed to be not None
        assert self.cap is not None, "cap should not be None when is_connected() returns True"

        try:
            ret, frame = self.cap.read()

            if not ret or frame is None or frame.size == 0:
                return None

            # Additional validation: check frame dimensions and type
            if len(frame.shape) != 3 or frame.shape[2] != 3:
                logger.debug(f"Invalid frame format for camera '{self.camera_id}': shape={frame.shape}")
                return None

            # Check for reasonable frame size (not too small or corrupted)
            min_dimension = 100  # Minimum 100x100 pixels
            if frame.shape[0] < min_dimension or frame.shape[1] < min_dimension:
                logger.debug(f"Frame too small for camera '{self.camera_id}': {frame.shape}")
                return None

            return frame

        except Exception as e:
            logger.debug(f"Frame read error for camera '{self.camera_id}': {str(e)}")
            return None

    def start_capture(self) -> None:
        """Start background thread for continuous frame capture.

        Creates and starts a daemon thread running _capture_loop() which
        continuously captures frames and adds them to the frame queue.
        """
        if self.capture_thread is not None and self.capture_thread.is_alive():
            logger.warning(f"Capture thread already running: {self.camera_id}")
            return

        self._stop_capture.clear()
        self.capture_thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,
            name=f"RTSPCapture-{self.camera_id}"
        )
        self.capture_thread.start()
        logger.info(f"Started capture thread: {self.camera_id}")

    def stop_capture(self) -> None:
        """Stop background frame capture thread.

        Signals the capture thread to stop and waits for it to exit.
        """
        if self.capture_thread is None or not self.capture_thread.is_alive():
            return

        self._stop_capture.set()
        self.capture_thread.join(timeout=5.0)
        logger.info(f"Stopped capture thread: {self.camera_id}")

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
        Includes frame validation and better error handling.
        Exits when _stop_capture event is set or after 5 consecutive failures.
        """
        consecutive_failures = 0
        # Generate exponential backoff sequence up to max delay
        backoff_delays = []
        delay = 1
        while delay <= self.max_reconnect_delay:
            backoff_delays.append(delay)
            delay *= 2
        if not backoff_delays or backoff_delays[-1] < self.max_reconnect_delay:
            backoff_delays.append(self.max_reconnect_delay)
        successful_frames = 0

        while not self._stop_capture.is_set():
            frame = self.get_frame()

            if frame is not None:
                # Successfully captured frame, reset failure counter
                consecutive_failures = 0
                successful_frames += 1

                try:
                    # Try to add frame to queue without blocking
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    # Queue full, skip this frame (oldest frames remain)
                    logger.debug(f"Frame queue full, dropping frame: {self.camera_id}")

                # Small sleep to control frame rate and reduce CPU usage
                time.sleep(0.033)  # ~30 fps max

            else:
                # Frame capture failed, attempt reconnection
                consecutive_failures += 1

                if consecutive_failures == 1:
                    logger.warning(f"RTSP connection lost: {self.camera_id} (successful frames: {successful_frames})")
                    successful_frames = 0  # Reset counter for next connection

                if consecutive_failures > self.max_reconnect_attempts:
                    logger.error(f"Failed to reconnect after {self.max_reconnect_attempts} attempts, exiting: {self.camera_id}")
                    break

                # Calculate backoff delay (cap at 8 seconds)
                delay_index = min(consecutive_failures - 1, len(backoff_delays) - 1)
                delay = backoff_delays[delay_index]

                logger.debug(f"Reconnection attempt {consecutive_failures}, waiting {delay}s: {self.camera_id}")

                time.sleep(delay)

                # Attempt reconnection
                try:
                    self.disconnect()
                    if self.connect():
                        logger.info(f"RTSP connection restored: {self.camera_id}")
                        consecutive_failures = 0
                        successful_frames = 0
                except RTSPConnectionError as e:
                    logger.warning(f"Reconnection failed: {str(e)}")
