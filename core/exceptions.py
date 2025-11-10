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


class DatabaseError(VideoRecognitionError):
    """Database operation failed.

    Raised when database operations fail due to connection issues,
    SQL errors, constraint violations, or other database-related problems.
    This includes SQLite-specific errors and general database access issues.

    Examples:
        - Database file corrupted or inaccessible
        - SQL syntax errors in queries
        - UNIQUE constraint violations
        - Disk full preventing writes
        - Database locked by another process
    """

    pass


class DatabaseWriteError(DatabaseError):
    """Database write operation failed.

    Raised when database write operations fail due to disk space,
    permissions, or other write-specific issues. This is a subclass
    of DatabaseError for more specific error handling.

    Examples:
        - Disk full preventing event insertion
        - Insufficient permissions to write to database file
        - Database file locked for writing
        - File system errors during commit
    """

    pass
