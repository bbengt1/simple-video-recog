"""Custom exceptions for the video recognition system."""


class VideoRecognitionError(Exception):
    """Base exception for all application errors.

    This serves as the parent class for all custom exceptions in the
    video recognition system, allowing for broad exception catching
    when needed.
    """

    pass


class RTSPConnectionError(VideoRecognitionError):
    """RTSP camera connection failed.

    Raised when the system cannot establish or maintain a connection
    to the RTSP camera stream. This includes authentication failures,
    network timeouts, invalid URLs, and other connection-related issues.

    Examples:
        - Invalid RTSP URL format
        - Authentication credentials rejected
        - Network timeout during connection attempt
        - Camera unreachable or offline
    """

    pass


class CoreMLLoadError(VideoRecognitionError):
    """CoreML model loading failed.

    Raised when the system cannot load or validate a CoreML model file.
    This includes file not found, corrupted models, incompatible formats,
    or models that cannot run on the available hardware.

    Examples:
        - Model file not found at specified path
        - Corrupted or invalid .mlmodel file
        - Model incompatible with Apple Neural Engine
        - Missing required model metadata
    """

    pass
