# Service Architecture (Traditional Server + Processing Engine)

## Dual-Process Architecture

The system runs two separate Python processes in Phase 2:

1. **Processing Engine** (`main.py`): Runs ProcessingPipeline, handles RTSP/CoreML/Ollama/persistence
2. **API Server** (`api/server.py`): Runs FastAPI server, provides REST/WebSocket APIs

**Communication:** Both processes share the SQLite database file (`data/events.db`). The processing engine has read/write access, while the API server has read-only access.

**Rationale:** Separating concerns allows the processing engine to run continuously without HTTP overhead, while the API server can be restarted independently for configuration changes.

---

## Processing Pipeline Organization

```python
# core/processing_pipeline.py
"""
ProcessingPipeline orchestrates frame processing from capture to persistence.
Sequential execution (no async) for MVP simplicity.
"""
import signal
import threading
from typing import Optional
import numpy as np

from integrations.rtsp_client import RTSPCameraClient
from core.motion_detector import MotionDetector
from platform.coreml_detector import CoreMLObjectDetector
from integrations.ollama_client import OllamaLLMProcessor
from core.event_manager import EventManager
from core.storage_monitor import StorageMonitor
from core.metrics import MetricsCollector
from core.config import SystemConfig


class ProcessingPipeline:
    """Main processing pipeline orchestrating all stages."""

    def __init__(self, config: SystemConfig):
        self.config = config
        self.shutdown_event = threading.Event()
        self.paused = threading.Event()

        # Initialize all components
        self.rtsp_client = RTSPCameraClient(config.camera_rtsp_url)
        self.motion_detector = MotionDetector(config.motion_threshold)
        self.object_detector = CoreMLObjectDetector(config.coreml_model_path)
        self.llm_processor = OllamaLLMProcessor(config.ollama_base_url, config.ollama_model)
        self.event_manager = EventManager(config)
        self.storage_monitor = StorageMonitor(config.max_storage_gb)
        self.metrics = MetricsCollector(config.metrics_interval)

        self.frame_count = 0
        self.event_count = 0

        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def run(self) -> None:
        """Main processing loop - blocks until shutdown."""
        self.logger.info("Starting processing pipeline")

        # Startup health check
        if not self._health_check():
            self.logger.error("Health check failed, exiting")
            return

        # Connect to RTSP stream
        if not self.rtsp_client.connect():
            self.logger.error("Failed to connect to RTSP camera")
            return

        # Main loop
        while not self.shutdown_event.is_set():
            if self.paused.is_set():
                time.sleep(0.1)
                continue

            try:
                self._process_frame()
            except Exception as e:
                self.logger.error(f"Frame processing error: {e}", exc_info=True)
                # Continue processing despite errors

        # Cleanup
        self._shutdown()

    def _process_frame(self) -> None:
        """Process single frame through all stages."""
        # Stage 1: Capture frame
        frame = self.rtsp_client.get_frame()
        if frame is None:
            self.logger.warning("Failed to capture frame, attempting reconnect")
            return

        self.frame_count += 1
        self.metrics.increment_counter('frames_processed')

        # Stage 2: Detect motion
        has_motion, confidence = self.motion_detector.detect_motion(frame)
        if not has_motion:
            return  # Skip frame if no motion

        self.metrics.increment_counter('motion_detected')

        # Stage 3: Object detection (CoreML)
        start_time = time.time()
        detected_objects = self.object_detector.detect_objects(frame)
        coreml_time = (time.time() - start_time) * 1000  # Convert to ms
        self.metrics.record_inference_time('coreml', coreml_time)

        if not detected_objects:
            return  # No objects detected

        # Stage 4: Filter objects by blacklist and confidence
        filtered_objects = self._filter_objects(detected_objects)
        if not filtered_objects:
            return

        # Stage 5: LLM semantic description
        start_time = time.time()
        description = self.llm_processor.generate_description(frame, filtered_objects)
        llm_time = (time.time() - start_time) * 1000
        self.metrics.record_inference_time('llm', llm_time)

        # Stage 6: Create event
        event = self.event_manager.create_event(
            frame=frame,
            objects=filtered_objects,
            description=description,
            motion_confidence=confidence
        )

        if event is None:
            self.metrics.increment_counter('events_suppressed')
            return  # Event suppressed by de-duplication

        self.event_count += 1
        self.metrics.increment_counter('events_created')

        # Stages 7-9: Persistence (handled by EventManager)
        # EventManager delegates to DatabaseManager, JSONLogger, PlaintextLogger

        # Stage 10: Check storage (every 100 events)
        if self.event_count % 100 == 0:
            storage_stats = self.storage_monitor.check_usage()
            if storage_stats.is_over_limit:
                self.logger.error("Storage limit exceeded, triggering shutdown")
                self.shutdown()

    def _filter_objects(self, objects):
        """Filter objects by blacklist and minimum confidence."""
        return [
            obj for obj in objects
            if obj.label not in self.config.blacklist_objects
            and obj.confidence >= self.config.min_object_confidence
        ]

    def _health_check(self) -> bool:
        """Validate all dependencies are available."""
        checks = {
            'CoreML Model': self.object_detector.is_model_loaded(),
            'Ollama Service': self.llm_processor.health_check(),
            'Database': self.event_manager.db_manager.test_connection()
        }

        for service, status in checks.items():
            if status:
                self.logger.info(f"✓ {service}: OK")
            else:
                self.logger.error(f"✗ {service}: FAILED")

        return all(checks.values())

    def _signal_handler(self, signum, frame):
        """Handle SIGINT/SIGTERM for graceful shutdown."""
        signal_name = signal.Signals(signum).name
        self.logger.info(f"Received {signal_name}, initiating shutdown")
        self.shutdown()

    def shutdown(self) -> None:
        """Trigger graceful shutdown."""
        self.shutdown_event.set()

    def _shutdown(self) -> None:
        """Cleanup resources before exit."""
        self.logger.info("Shutting down processing pipeline")

        self.rtsp_client.disconnect()
        self.event_manager.flush()
        self.metrics.flush()

        self.logger.info(f"Processed {self.frame_count} frames, created {self.event_count} events")
        self.logger.info("Shutdown complete")
```

---

## FastAPI Server Structure

```python
# api/server.py
"""
FastAPI server providing REST API and WebSocket endpoints.
Runs in separate process from processing pipeline.
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List, Optional
from datetime import datetime

from core.database import DatabaseManager
from core.metrics import MetricsCollector
from core.config import load_config
from api.websocket import WebSocketManager

# Initialize app
app = FastAPI(
    title="Local Video Recognition System API",
    version="1.0.0",
    description="REST API for event querying and real-time streaming"
)

# CORS middleware for web dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize dependencies
config = load_config("config/config.yaml")
db_manager = DatabaseManager(config.db_path)
metrics_collector = MetricsCollector(config.metrics_interval)
ws_manager = WebSocketManager()

# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """System health status."""
    return {
        "status": "healthy",
        "services": {
            "database": "ok" if db_manager.test_connection() else "error",
            "ollama": "ok",  # TODO: Add Ollama health check
            "rtsp_camera": "ok"  # TODO: Add RTSP health check
        },
        "uptime_seconds": metrics_collector.get_uptime()
    }

# Metrics endpoint
@app.get("/api/v1/metrics")
async def get_metrics():
    """Current system metrics."""
    return metrics_collector.collect()

# Events list endpoint
@app.get("/api/v1/events")
async def list_events(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    camera_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """List events with filtering and pagination."""
    if start and end:
        events = db_manager.get_events_by_timerange(start, end, limit, offset)
    elif camera_id:
        events = db_manager.get_events_by_camera(camera_id, limit, offset)
    else:
        events = db_manager.get_recent_events(limit)

    total = db_manager.count_events()

    return {
        "events": [e.model_dump() for e in events],
        "total": total,
        "limit": limit,
        "offset": offset
    }

# Event detail endpoint
@app.get("/api/v1/events/{event_id}")
async def get_event(event_id: str):
    """Get event by ID."""
    event = db_manager.get_event_by_id(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event.model_dump()

# Event image endpoint
@app.get("/api/v1/events/{event_id}/image")
async def get_event_image(event_id: str):
    """Get annotated image for event."""
    event = db_manager.get_event_by_id(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    image_path = event.image_path
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(image_path, media_type="image/jpeg")

# Configuration endpoint
@app.get("/api/v1/config")
async def get_config():
    """Get sanitized system configuration."""
    return {
        "camera_id": config.camera_id,
        "motion_threshold": config.motion_threshold,
        "frame_sample_rate": config.frame_sample_rate,
        "blacklist_objects": config.blacklist_objects,
        "ollama_model": config.ollama_model,
        "max_storage_gb": config.max_storage_gb,
        "log_level": config.log_level
    }

# WebSocket endpoint
@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time event streaming via WebSocket."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, wait for disconnect
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
```

---
