# Error Handling Standards

## Python Error Handling

**Custom exception hierarchy:**
```python
# core/exceptions.py
class VideoRecognitionError(Exception):
    """Base exception for all application errors."""
    pass

class DatabaseError(VideoRecognitionError):
    """Database operation failed."""
    pass

class RTSPConnectionError(VideoRecognitionError):
    """RTSP camera connection failed."""
    pass

class CoreMLInferenceError(VideoRecognitionError):
    """CoreML inference failed."""
    pass

class OllamaServiceError(VideoRecognitionError):
    """Ollama LLM service unavailable or failed."""
    pass
```

**Error handling pattern:**
```python
def process_frame(self, frame: np.ndarray) -> Optional[Event]:
    """Process frame through pipeline.

    Returns None on recoverable errors, raises on critical failures.
    """
    try:
        # Attempt operation
        objects = self.object_detector.detect_objects(frame)
    except CoreMLInferenceError as e:
        logger.error(
            f"CoreML inference failed: {e}",
            exc_info=True,
            extra={"frame_shape": frame.shape}
        )
        # Recoverable: skip this frame, continue processing
        return None
    except Exception as e:
        logger.critical(
            f"Unexpected error in frame processing: {e}",
            exc_info=True
        )
        # Non-recoverable: re-raise
        raise
```

## JavaScript Error Handling

**API error handling pattern:**
```javascript
// services/apiClient.js
export async function fetchEvents(filters = {}) {
  try {
    const params = new URLSearchParams(filters)
    const response = await fetch(`/api/v1/events?${params}`)

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new APIError(
        error.error?.message || `HTTP ${response.status}`,
        response.status,
        error
      )
    }

    return await response.json()
  } catch (error) {
    if (error instanceof APIError) {
      throw error
    }
    // Network error or JSON parse error
    throw new APIError('Network request failed', 0, { cause: error })
  }
}

// Custom error class
class APIError extends Error {
  constructor(message, status, details) {
    super(message)
    this.name = 'APIError'
    this.status = status
    this.details = details
  }
}
```

---
