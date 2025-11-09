# Processing Pipeline

**Responsibility:** Orchestrates the complete frame processing workflow from RTSP capture through motion detection, object detection, LLM inference, and persistence.

**Key Interfaces:**
- `run() -> None`: Start processing loop (blocks until shutdown)
- `shutdown() -> None`: Trigger graceful shutdown
- `pause() -> None`: Temporarily pause processing
- `resume() -> None`: Resume after pause

**Dependencies:**
- All components above (RTSP, Motion, CoreML, Ollama, EventManager, etc.)
- SystemConfig

**Technology Stack:**
- Python 3.10+
- Module path: `core/processing_pipeline.py`
- Class: `ProcessingPipeline`

**Implementation Notes:**
- Sequential processing (no async/threads for MVP)
- Processing stages:
  1. Capture frame from RTSP
  2. Detect motion
  3. If motion: Run CoreML object detection
  4. Filter objects by blacklist and confidence
  5. If objects detected: Call Ollama LLM
  6. Create Event via EventManager
  7-9. Persist to database, JSON, plaintext
  10. Check storage every 100 events
- Error handling: Log error, skip frame, continue processing
- Shutdown on SIGINT/SIGTERM (graceful)
- Startup health check validates all dependencies

---
