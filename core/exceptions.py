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


class OllamaConnectionError(VideoRecognitionError):
    """Ollama service connection failed.

    Raised when the system cannot connect to the Ollama LLM service.
    This includes service not running, network connectivity issues,
    or invalid base URL configuration.

    Examples:
        - Ollama service not started (ollama serve not running)
        - Invalid base URL or port configuration
        - Network connectivity issues
        - Service temporarily unavailable
    """

    pass


class OllamaModelNotFoundError(VideoRecognitionError):
    """Ollama vision model not found.

    Raised when the specified vision model is not downloaded or available
    in the Ollama service. The model needs to be pulled first using
    'ollama pull <model_name>'.

    Examples:
        - Vision model not downloaded (need to run ollama pull)
        - Incorrect model name specified in configuration
        - Model was removed or corrupted
    """

    pass


class OllamaTimeoutError(VideoRecognitionError):
    """Ollama LLM inference timeout.

    Raised when LLM inference exceeds the configured timeout limit.
    This prevents the system from hanging on slow or unresponsive
    LLM requests while still allowing graceful degradation.

    Examples:
        - Large images causing slow processing
        - Model overload on the local system
        - Network latency issues (though local, still possible)
        - Complex prompts requiring extended processing time
    """

    pass
