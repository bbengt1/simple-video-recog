# Local Video Recognition System Fullstack Architecture Document

This document outlines the complete fullstack architecture for the Local Video Recognition System, including backend systems, frontend implementation, and their integration. It serves as the single source of truth for AI-driven development, ensuring consistency across the entire technology stack.

This unified approach combines what would traditionally be separate backend and frontend architecture documents, streamlining the development process for modern fullstack applications where these concerns are increasingly intertwined.

## Starter Template or Existing Project

**Status:** N/A - Greenfield project

This is a new project built from scratch with no existing codebase or starter template. All architectural decisions are made based on the specific requirements outlined in the PRD.

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-08 | 1.0 | Initial architecture draft | Winston (Architect) |

---

# High Level Architecture

## Technical Summary

The Local Video Recognition System is a privacy-first, macOS-native application that processes RTSP camera streams locally on Apple Silicon hardware. The system employs a sequential processing pipeline architecture where each frame captured from an RTSP camera undergoes motion detection, object recognition via CoreML (optimized for Apple Neural Engine), and semantic analysis through a local Ollama LLM instance. All processing occurs on-device with zero cloud dependencies, ensuring complete data privacy.

Phase 1 delivers a CLI-based application with a monolithic Python backend focused on the core processing pipeline and data persistence. Phase 2 introduces a modular architecture with a separate FastAPI web server that provides REST and WebSocket APIs, enabling a vanilla JavaScript web dashboard for real-time event monitoring and historical analysis. The frontend communicates with the backend via HTTP APIs while maintaining complete separation of concerns.

The system integrates with two external local services: Ollama (local LLM inference via HTTP API) and RTSP cameras (via OpenCV's RTSP client). All event data is persisted to SQLite with dual-format logging (JSON + plaintext) and stored locally with FIFO rotation to maintain a 4GB storage limit. The architecture is designed to run 24/7 on Mac Mini or Mac Studio hardware with automatic recovery from transient failures.

## Platform and Infrastructure Choice

**Platform:** macOS Native on Apple Silicon
**Key Services:** None - 100% local processing with no cloud services
**Deployment Host and Regions:** Local deployment on Mac Mini or Mac Studio (Apple Silicon M1/M2/M3)

**Rationale:** The platform choice is constrained by the requirement to use Apple's Neural Engine for CoreML inference. This hardware acceleration is only accessible on macOS with Apple Silicon (M1/M2/M3 chips). Cloud deployment is explicitly out of scope due to privacy requirements - all video processing must occur on local hardware with no data transmission to external services.

## Repository Structure

**Structure:** Monorepo with functional separation
**Monorepo Tool:** Not applicable (Python project, no workspace tooling needed)
**Package Organization:** Functional grouping by architectural layer

```
video-recognition/
├── core/           # Platform-independent business logic
├── platform/       # Apple Silicon-specific implementations
├── integrations/   # External service clients (Ollama, RTSP)
├── api/            # Phase 2: FastAPI web server
├── web/            # Phase 2: Vanilla JavaScript dashboard
├── tests/          # Test organization mirrors source structure
└── config/         # Configuration files and schemas
```

The monorepo structure provides clear separation of concerns while keeping all code in a single repository. This approach simplifies dependency management and ensures atomic commits across the entire stack. Functional grouping (rather than feature-based modules) aligns with the sequential processing pipeline architecture and makes dependencies explicit.

## High Level Architecture Diagram

```mermaid
graph TB
    subgraph "Phase 1: CLI MVP"
        Camera[RTSP Camera Stream]
        CLI[CLI Interface]
        Pipeline[Processing Pipeline]
        Motion[Motion Detector]
        CoreML[CoreML Object Detector]
        LLM[Ollama LLM Processor]
        EventMgr[Event Manager]
        DB[(SQLite Database)]
        JSONLog[JSON Logger]
        TxtLog[Plaintext Logger]
        Storage[Storage Monitor]

        Camera --> Pipeline
        CLI --> Pipeline
        Pipeline --> Motion
        Motion --> CoreML
        CoreML --> LLM
        LLM --> EventMgr
        EventMgr --> DB
        EventMgr --> JSONLog
        EventMgr --> TxtLog
        EventMgr --> Storage
    end

    subgraph "Phase 2: Web Dashboard"
        WebUI[Web Dashboard<br/>Vanilla JS]
        API[FastAPI Server]
        WS[WebSocket Server]

        WebUI -->|HTTP API| API
        WebUI -->|Real-time events| WS
        API --> DB
        WS --> EventMgr
    end

    subgraph "External Services (Local)"
        OllamaService[Ollama Service<br/>localhost:11434]
        RTSPCam[IP Camera<br/>RTSP Stream]
    end

    LLM -->|HTTP API| OllamaService
    Pipeline -->|RTSP Client| RTSPCam

    style Camera fill:#e1f5ff
    style OllamaService fill:#e1f5ff
    style RTSPCam fill:#e1f5ff
    style WebUI fill:#fff4e1
    style DB fill:#f0f0f0
```

## Architectural Patterns

- **Pipeline Pattern:** Sequential frame processing through motion detection → CoreML → LLM → persistence stages. Each stage has clear inputs/outputs and can be tested independently. _Rationale:_ Simplifies error handling and makes performance bottlenecks easy to identify. Sequential execution matches the natural flow of video frame processing.

- **Repository Pattern:** DatabaseManager abstracts all SQLite operations behind a clean interface (insert_event, get_events_by_timerange, etc.). _Rationale:_ Isolates database implementation details, enables easy mocking for tests, and provides a single point of control for data access.

- **Dependency Injection:** Components receive dependencies through constructor parameters rather than creating them internally. Example: ProcessingPipeline receives motion_detector, object_detector, llm_processor instances. _Rationale:_ Enables unit testing with mock objects and makes component dependencies explicit.

- **Event-Driven Architecture (Phase 2):** WebSocket server publishes new events to connected clients in real-time. _Rationale:_ Decouples event creation from event delivery, allowing multiple clients to receive updates without polling.

- **Observer Pattern (Frontend State Management):** Custom state management where UI components subscribe to state changes. _Rationale:_ Avoids framework overhead while providing reactive UI updates. Lightweight alternative to Redux/MobX for simple state.

- **Monolith → Modular Monolith Evolution:** Phase 1 is a single-process CLI application. Phase 2 separates into two processes (processing engine + API server) sharing the same database. _Rationale:_ Maintains simplicity for MVP while enabling web access in Phase 2. Avoids premature microservices complexity.

---

# Tech Stack

## Technology Stack Table

| Category | Technology | Version | Purpose | Rationale |
|----------|-----------|---------|---------|-----------|
| Core Language | Python | 3.10+ | Primary development language | Native ARM64 support, rich ML/CV ecosystem, CoreML bindings available |
| Computer Vision | OpenCV | 4.8.1+ | RTSP stream capture, motion detection, image processing | Industry standard, M1-optimized builds available, mature RTSP client |
| ML Framework | CoreML Tools | 7.0+ | Neural Engine interface for object detection | Only framework with Apple Neural Engine access for <100ms inference |
| LLM Integration | ollama-python | 0.1.0+ | Ollama HTTP API client | Official Python client for local LLM inference |
| API Framework | FastAPI | 0.104+ | Phase 2 REST API and WebSocket server | Async support, auto-generated OpenAPI docs, excellent performance |
| Frontend Language | JavaScript | ES6+ | Web dashboard implementation | Native browser support, no transpilation needed, simple deployment |
| State Management | Custom Observer Pattern | N/A | Reactive UI updates | Lightweight alternative to frameworks, no external dependencies |
| Database | SQLite | 3.42+ | Event storage and querying | File-based, zero-config, ACID compliant, sufficient for single-user |
| Cache | None | N/A | Not needed for MVP | Event data is write-heavy, reads are infrequent, no performance benefit |
| File Storage | Local Filesystem | N/A | Annotated images, JSON/plaintext logs | Simple, no additional infrastructure, aligns with privacy-first approach |
| Authentication | None (Phase 1-2) | N/A | Not implemented in MVP | Localhost-only access, future enhancement for remote access |
| Frontend Testing | None (Phase 1) | N/A | Vanilla JS with manual testing initially | Defer to Phase 3, focus on backend test coverage for MVP |
| Backend Testing | pytest | 7.4+ | Unit, integration, and performance tests | Python standard, fixture support, parametrization, ≥70% coverage target |
| E2E Testing | Playwright (Phase 3) | TBD | Full workflow validation | Deferred to Phase 3, manual testing sufficient for Phase 1-2 |
| Build Tool | None | N/A | No build step required | Python is interpreted, JavaScript uses native ES6 modules |
| Bundler | None | N/A | No bundling required | Vanilla JS served directly, no framework compilation needed |
| IaC Tool | None | N/A | Local deployment only | No cloud infrastructure, manual setup on Mac Mini/Studio |
| CI/CD | GitHub Actions | N/A | Automated testing on push/PR | Free for public repos, macOS runners available for testing |
| Monitoring | Custom Metrics Logger | N/A | Performance metrics to logs/metrics.json | Simple JSON Lines format, no external service needed |
| Logging | Python logging + custom | 3.10+ stdlib | Application logs, event logs, metrics | Built-in logging module + custom JSON/plaintext event loggers |
| CSS Framework | Custom CSS | N/A | Web dashboard styling | Simple layout, dark mode optimized, no framework overhead |

---

# Data Models

## Event

**Purpose:** Represents a single motion-triggered event captured from the camera, processed through the pipeline, and persisted to storage. This is the core entity in the system, containing all information about detected objects and semantic descriptions.

**Key Attributes:**
- `event_id` (str): Unique identifier, format: `evt_<timestamp>_<random>` (e.g., `evt_1699459335_a7b3c`)
- `timestamp` (datetime): When the event occurred (UTC with timezone awareness)
- `camera_id` (str): Identifier for the camera source (future multi-camera support)
- `motion_confidence` (float | None): Motion detection confidence score (0.0-1.0)
- `detected_objects` (list[DetectedObject]): All objects detected by CoreML
- `llm_description` (str): Semantic description generated by Ollama LLM
- `image_path` (str): Path to annotated image with bounding boxes (relative to project root)
- `json_log_path` (str): Path to JSON log file containing this event
- `created_at` (datetime): Database insertion timestamp (auto-generated)

### Pydantic Schema

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class Event(BaseModel):
    """Core event entity representing a motion-triggered detection."""

    event_id: str = Field(
        ...,
        description="Unique event identifier",
        example="evt_1699459335_a7b3c"
    )
    timestamp: datetime = Field(
        ...,
        description="Event occurrence time (UTC)",
        example="2025-11-08T14:32:15Z"
    )
    camera_id: str = Field(
        ...,
        description="Camera identifier",
        example="front_door"
    )
    motion_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Motion detection confidence score"
    )
    detected_objects: List['DetectedObject'] = Field(
        default_factory=list,
        description="Objects detected by CoreML"
    )
    llm_description: str = Field(
        ...,
        description="Semantic description from Ollama LLM",
        example="Person in blue shirt carrying brown package approaching front door"
    )
    image_path: str = Field(
        ...,
        description="Path to annotated image",
        example="data/events/2025-11-08/evt_1699459335_a7b3c.jpg"
    )
    json_log_path: str = Field(
        ...,
        description="Path to JSON log file",
        example="data/events/2025-11-08/events.json"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Database insertion timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "evt_1699459335_a7b3c",
                "timestamp": "2025-11-08T14:32:15Z",
                "camera_id": "front_door",
                "motion_confidence": 0.87,
                "detected_objects": [
                    {"label": "person", "confidence": 0.92, "bbox": {"x": 120, "y": 50, "width": 180, "height": 320}},
                    {"label": "package", "confidence": 0.87, "bbox": {"x": 150, "y": 280, "width": 80, "height": 60}}
                ],
                "llm_description": "Person in blue shirt carrying brown package approaching front door",
                "image_path": "data/events/2025-11-08/evt_1699459335_a7b3c.jpg",
                "json_log_path": "data/events/2025-11-08/events.json",
                "created_at": "2025-11-08T14:32:16Z"
            }
        }
```

### Relationships
- **Has many** DetectedObject instances (1:N relationship)
- **Belongs to** Camera (future Phase 3 multi-camera support)
- **References** image file and JSON log file on filesystem

---

## DetectedObject

**Purpose:** Represents a single object detected by CoreML within a frame, including its label, confidence score, and bounding box coordinates. Multiple DetectedObject instances are associated with each Event.

**Key Attributes:**
- `label` (str): Object class label from CoreML model (e.g., "person", "car", "dog")
- `confidence` (float): Detection confidence score (0.0-1.0)
- `bbox` (BoundingBox): Bounding box coordinates for the detected object

### Pydantic Schema

```python
class BoundingBox(BaseModel):
    """Bounding box coordinates for detected objects."""

    x: int = Field(..., description="Top-left X coordinate", ge=0)
    y: int = Field(..., description="Top-left Y coordinate", ge=0)
    width: int = Field(..., description="Box width in pixels", gt=0)
    height: int = Field(..., description="Box height in pixels", gt=0)

    class Config:
        json_schema_extra = {
            "example": {"x": 120, "y": 50, "width": 180, "height": 320}
        }


class DetectedObject(BaseModel):
    """Object detected by CoreML within a frame."""

    label: str = Field(
        ...,
        description="Object class label",
        example="person"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Detection confidence score",
        example=0.92
    )
    bbox: BoundingBox = Field(
        ...,
        description="Bounding box coordinates"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "label": "person",
                "confidence": 0.92,
                "bbox": {"x": 120, "y": 50, "width": 180, "height": 320}
            }
        }
```

### Relationships
- **Belongs to** Event (N:1 relationship)

---

## SystemConfig

**Purpose:** Configuration data loaded from YAML file, validated using Pydantic to ensure type safety and provide clear error messages for invalid configurations.

**Key Attributes:**
- `camera_rtsp_url` (str): RTSP stream URL
- `camera_id` (str): Camera identifier
- `motion_threshold` (float): Motion detection sensitivity
- `frame_sample_rate` (int): Frames to process per second
- `blacklist_objects` (list[str]): Object labels to filter out
- `ollama_base_url` (str): Ollama API endpoint
- `ollama_model` (str): LLM model name
- `db_path` (str): SQLite database file path
- `max_storage_gb` (float): Storage limit
- `log_level` (str): Logging verbosity

### Pydantic Schema

```python
from pydantic import BaseModel, Field, HttpUrl
from typing import List

class SystemConfig(BaseModel):
    """System configuration loaded from config/config.yaml."""

    # Camera Configuration
    camera_rtsp_url: str = Field(
        ...,
        description="RTSP stream URL",
        example="rtsp://admin:password@192.168.1.100:554/stream1"
    )
    camera_id: str = Field(
        default="camera_1",
        description="Camera identifier for multi-camera support"
    )

    # Motion Detection
    motion_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Motion detection sensitivity (0=very sensitive, 1=less sensitive)"
    )
    frame_sample_rate: int = Field(
        default=5,
        ge=1,
        le=30,
        description="Frames per second to process during motion"
    )

    # Object Detection
    coreml_model_path: str = Field(
        default="models/yolov8n.mlmodel",
        description="Path to CoreML model file"
    )
    blacklist_objects: List[str] = Field(
        default_factory=lambda: ["bird", "cat"],
        description="Object labels to ignore"
    )
    min_object_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence to include detected object"
    )

    # LLM Configuration
    ollama_base_url: HttpUrl = Field(
        default="http://localhost:11434",
        description="Ollama API endpoint"
    )
    ollama_model: str = Field(
        default="llava:7b",
        description="LLM model name (llava or moondream)"
    )
    llm_timeout: int = Field(
        default=10,
        ge=1,
        le=60,
        description="LLM request timeout in seconds"
    )

    # Storage
    db_path: str = Field(
        default="data/events.db",
        description="SQLite database file path"
    )
    max_storage_gb: float = Field(
        default=4.0,
        gt=0,
        description="Maximum storage limit in GB"
    )
    min_retention_days: int = Field(
        default=7,
        ge=1,
        description="Minimum days to retain events"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging verbosity (DEBUG, INFO, WARNING, ERROR)"
    )
    metrics_interval: int = Field(
        default=60,
        ge=10,
        description="Metrics collection interval in seconds"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "camera_rtsp_url": "rtsp://admin:password@192.168.1.100:554/stream1",
                "camera_id": "front_door",
                "motion_threshold": 0.5,
                "frame_sample_rate": 5,
                "coreml_model_path": "models/yolov8n.mlmodel",
                "blacklist_objects": ["bird", "cat"],
                "min_object_confidence": 0.5,
                "ollama_base_url": "http://localhost:11434",
                "ollama_model": "llava:7b",
                "llm_timeout": 10,
                "db_path": "data/events.db",
                "max_storage_gb": 4.0,
                "min_retention_days": 7,
                "log_level": "INFO",
                "metrics_interval": 60
            }
        }
```

### Relationships
- **Loaded from** config/config.yaml file
- **Validated on** application startup

---

## MetricsSnapshot

**Purpose:** Performance metrics collected periodically and logged to logs/metrics.json for monitoring system health and validating NFR targets.

**Key Attributes:**
- `timestamp` (datetime): When metrics were collected
- `frames_processed` (int): Total frames processed
- `motion_detected` (int): Frames with motion detected
- `events_created` (int): Total events created
- `events_suppressed` (int): Events suppressed by de-duplication
- `coreml_inference_avg` (float): Average CoreML inference time (ms)
- `llm_inference_avg` (float): Average LLM inference time (ms)
- `cpu_usage` (float): Current CPU usage percentage
- `memory_usage_mb` (int): Current memory usage in MB
- `storage_usage_gb` (float): Current storage usage in GB

### Pydantic Schema

```python
class MetricsSnapshot(BaseModel):
    """Performance metrics snapshot logged periodically."""

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Metrics collection timestamp"
    )

    # Processing Statistics
    frames_processed: int = Field(default=0, description="Total frames processed")
    motion_detected: int = Field(default=0, description="Frames with motion")
    events_created: int = Field(default=0, description="Events created")
    events_suppressed: int = Field(default=0, description="Events suppressed by de-duplication")

    # Performance Metrics
    coreml_inference_avg: float = Field(
        default=0.0,
        description="Average CoreML inference time (ms)"
    )
    coreml_inference_p95: float = Field(
        default=0.0,
        description="95th percentile CoreML inference time (ms)"
    )
    llm_inference_avg: float = Field(
        default=0.0,
        description="Average LLM inference time (ms)"
    )
    llm_inference_p95: float = Field(
        default=0.0,
        description="95th percentile LLM inference time (ms)"
    )

    # System Resources
    cpu_usage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="CPU usage percentage"
    )
    memory_usage_mb: int = Field(
        default=0,
        ge=0,
        description="Memory usage in MB"
    )
    storage_usage_gb: float = Field(
        default=0.0,
        ge=0,
        description="Storage usage in GB"
    )

    # Uptime
    uptime_seconds: int = Field(
        default=0,
        ge=0,
        description="System uptime in seconds"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-08T14:32:00Z",
                "frames_processed": 1500,
                "motion_detected": 120,
                "events_created": 15,
                "events_suppressed": 5,
                "coreml_inference_avg": 85.3,
                "coreml_inference_p95": 95.7,
                "llm_inference_avg": 2400.0,
                "llm_inference_p95": 2850.0,
                "cpu_usage": 45.2,
                "memory_usage_mb": 1850,
                "storage_usage_gb": 1.2,
                "uptime_seconds": 86400
            }
        }
```

### Relationships
- **Logged to** logs/metrics.json in JSON Lines format
- **Collected by** MetricsCollector component every 60 seconds

---

# API Specification

## REST API Specification (Phase 2)

```yaml
openapi: 3.0.0
info:
  title: Local Video Recognition System API
  version: 1.0.0
  description: |
    REST API for the Local Video Recognition System web dashboard.
    Provides access to event data, system metrics, and real-time event streaming via WebSocket.

    **Authentication:** None (localhost-only access in Phase 2)
    **Base URL:** http://localhost:8000/api/v1

servers:
  - url: http://localhost:8000/api/v1
    description: Local development server

paths:
  /health:
    get:
      summary: Health check endpoint
      description: Returns system health status including service availability
      responses:
        '200':
          description: System is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "healthy"
                  services:
                    type: object
                    properties:
                      database:
                        type: string
                        example: "ok"
                      ollama:
                        type: string
                        example: "ok"
                      rtsp_camera:
                        type: string
                        example: "ok"
                  uptime_seconds:
                    type: integer
                    example: 86400

  /metrics:
    get:
      summary: Get current system metrics
      description: Returns latest performance metrics snapshot
      responses:
        '200':
          description: Current metrics
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MetricsSnapshot'

  /events:
    get:
      summary: List events with filtering
      description: Retrieve events with optional time range and pagination
      parameters:
        - name: start
          in: query
          schema:
            type: string
            format: date-time
          description: Start of time range (ISO 8601)
        - name: end
          in: query
          schema:
            type: string
            format: date-time
          description: End of time range (ISO 8601)
        - name: camera_id
          in: query
          schema:
            type: string
          description: Filter by camera ID
        - name: limit
          in: query
          schema:
            type: integer
            default: 100
            minimum: 1
            maximum: 1000
          description: Maximum number of results
        - name: offset
          in: query
          schema:
            type: integer
            default: 0
            minimum: 0
          description: Pagination offset
      responses:
        '200':
          description: List of events
          content:
            application/json:
              schema:
                type: object
                properties:
                  events:
                    type: array
                    items:
                      $ref: '#/components/schemas/Event'
                  total:
                    type: integer
                    description: Total count of events matching filters
                  limit:
                    type: integer
                  offset:
                    type: integer

  /events/{event_id}:
    get:
      summary: Get event by ID
      parameters:
        - name: event_id
          in: path
          required: true
          schema:
            type: string
          description: Event identifier
      responses:
        '200':
          description: Event details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Event'
        '404':
          description: Event not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /events/{event_id}/image:
    get:
      summary: Get annotated image for event
      parameters:
        - name: event_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Annotated image with bounding boxes
          content:
            image/jpeg:
              schema:
                type: string
                format: binary
        '404':
          description: Image not found

  /config:
    get:
      summary: Get current system configuration
      description: Returns sanitized configuration (excludes sensitive fields like passwords)
      responses:
        '200':
          description: System configuration
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SystemConfig'

components:
  schemas:
    Event:
      type: object
      properties:
        event_id:
          type: string
          example: "evt_1699459335_a7b3c"
        timestamp:
          type: string
          format: date-time
          example: "2025-11-08T14:32:15Z"
        camera_id:
          type: string
          example: "front_door"
        motion_confidence:
          type: number
          format: float
          minimum: 0
          maximum: 1
          example: 0.87
        detected_objects:
          type: array
          items:
            $ref: '#/components/schemas/DetectedObject'
        llm_description:
          type: string
          example: "Person in blue shirt carrying brown package approaching front door"
        image_path:
          type: string
          example: "data/events/2025-11-08/evt_1699459335_a7b3c.jpg"
        json_log_path:
          type: string
          example: "data/events/2025-11-08/events.json"
        created_at:
          type: string
          format: date-time
          example: "2025-11-08T14:32:16Z"

    DetectedObject:
      type: object
      properties:
        label:
          type: string
          example: "person"
        confidence:
          type: number
          format: float
          minimum: 0
          maximum: 1
          example: 0.92
        bbox:
          $ref: '#/components/schemas/BoundingBox'

    BoundingBox:
      type: object
      properties:
        x:
          type: integer
          minimum: 0
          example: 120
        y:
          type: integer
          minimum: 0
          example: 50
        width:
          type: integer
          minimum: 1
          example: 180
        height:
          type: integer
          minimum: 1
          example: 320

    MetricsSnapshot:
      type: object
      properties:
        timestamp:
          type: string
          format: date-time
        frames_processed:
          type: integer
        motion_detected:
          type: integer
        events_created:
          type: integer
        events_suppressed:
          type: integer
        coreml_inference_avg:
          type: number
          format: float
        coreml_inference_p95:
          type: number
          format: float
        llm_inference_avg:
          type: number
          format: float
        llm_inference_p95:
          type: number
          format: float
        cpu_usage:
          type: number
          format: float
        memory_usage_mb:
          type: integer
        storage_usage_gb:
          type: number
          format: float
        uptime_seconds:
          type: integer

    SystemConfig:
      type: object
      description: Sanitized system configuration (sensitive fields excluded)
      properties:
        camera_id:
          type: string
        motion_threshold:
          type: number
        frame_sample_rate:
          type: integer
        blacklist_objects:
          type: array
          items:
            type: string
        ollama_model:
          type: string
        max_storage_gb:
          type: number
        log_level:
          type: string

    Error:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
              example: "NOT_FOUND"
            message:
              type: string
              example: "Event not found"
            details:
              type: object
              additionalProperties: true
            timestamp:
              type: string
              format: date-time
            requestId:
              type: string
```

## WebSocket Endpoint (Phase 2)

**Endpoint:** `ws://localhost:8000/ws/events`

**Purpose:** Real-time event streaming to web dashboard clients

**Message Format:**
```json
{
  "type": "event",
  "data": {
    "event_id": "evt_1699459335_a7b3c",
    "timestamp": "2025-11-08T14:32:15Z",
    "camera_id": "front_door",
    "motion_confidence": 0.87,
    "detected_objects": [
      {
        "label": "person",
        "confidence": 0.92,
        "bbox": {"x": 120, "y": 50, "width": 180, "height": 320}
      }
    ],
    "llm_description": "Person in blue shirt carrying brown package approaching front door",
    "image_path": "data/events/2025-11-08/evt_1699459335_a7b3c.jpg"
  }
}
```

**Connection Lifecycle:**
1. Client opens WebSocket connection to `/ws/events`
2. Server accepts connection and adds to subscriber list
3. When new event is created, server broadcasts to all connected clients
4. Client closes connection when navigating away
5. Server removes client from subscriber list

**Error Handling:**
- Connection failures: Client implements exponential backoff reconnection (1s, 2s, 4s, 8s max)
- Server errors: Server sends error message with `{"type": "error", "message": "..."}`
- Missed events: No message replay - clients should query REST API for historical data

---

# Components

## RTSP Camera Client

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

## Motion Detector

**Responsibility:** Analyzes frames to detect motion using background subtraction algorithm. Only frames with significant motion trigger downstream processing.

**Key Interfaces:**
- `detect_motion(frame: np.ndarray) -> tuple[bool, float]`: Returns (has_motion, confidence_score)
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

## CoreML Object Detector

**Responsibility:** Runs CoreML model on Apple Neural Engine to detect objects in frames, extracts bounding boxes and confidence scores, filters by blacklist and minimum confidence.

**Key Interfaces:**
- `detect_objects(frame: np.ndarray) -> list[DetectedObject]`: Run inference, return detected objects
- `load_model(model_path: str) -> None`: Load CoreML model from file
- `is_model_loaded() -> bool`: Check if model is ready for inference

**Dependencies:**
- CoreML Tools (coremltools.models.MLModel)
- Pydantic DetectedObject model
- SystemConfig (for model path, blacklist, min confidence)

**Technology Stack:**
- Python 3.10+, CoreML Tools 7.0+, Vision framework (via coremltools)
- Module path: `platform/coreml_detector.py`
- Class: `CoreMLObjectDetector`

**Implementation Notes:**
- Validates model runs on Apple Neural Engine (ANE) at startup
- Converts frame from BGR (OpenCV) to RGB (CoreML) before inference
- Filters objects by: (1) confidence >= min_object_confidence, (2) label not in blacklist
- Inference target: <100ms per frame (NFR requirement)
- Logs WARNING if inference exceeds 100ms threshold

---

## Ollama LLM Processor

**Responsibility:** Sends annotated images to local Ollama service for semantic description generation using vision-capable LLM (LLaVA or Moondream).

**Key Interfaces:**
- `generate_description(image: np.ndarray, objects: list[DetectedObject]) -> str`: Generate semantic description
- `health_check() -> bool`: Verify Ollama service is available
- `get_available_models() -> list[str]`: List models available in Ollama

**Dependencies:**
- ollama-python client library
- SystemConfig (for ollama_base_url, ollama_model, llm_timeout)

**Technology Stack:**
- Python 3.10+, ollama-python 0.1.0+
- Module path: `integrations/ollama_client.py`
- Class: `OllamaLLMProcessor`

**Implementation Notes:**
- HTTP timeout set to llm_timeout from config (default 10s)
- Prompt template: "Describe what is happening in this image. Focus on: {object_labels}"
- Implements retry with exponential backoff (1 retry, 2s delay) for transient failures
- Falls back to generic description if LLM fails: "Detected: {object_labels}"
- Logs ERROR if Ollama service is unreachable, WARNING if LLM times out

---

## Event Manager

**Responsibility:** Creates Event objects from processed frame data, handles event de-duplication to suppress similar consecutive events, coordinates persistence across multiple loggers.

**Key Interfaces:**
- `create_event(frame, objects, description) -> Event | None`: Create event, returns None if suppressed
- `should_suppress(event: Event) -> bool`: Check if event is duplicate of recent event
- `reset_suppression() -> None`: Clear suppression cache

**Dependencies:**
- Pydantic Event model
- DatabaseManager, JSONEventLogger, PlaintextEventLogger
- SystemConfig (for suppression threshold and window)

**Technology Stack:**
- Python 3.10+
- Module path: `core/event_manager.py`
- Class: `EventManager`

**Implementation Notes:**
- De-duplication algorithm: Compare new event objects to last 5 events
- Suppression threshold: ≥80% overlap in detected object labels
- Generates event_id using format: `evt_{timestamp}_{random_suffix}`
- Delegates persistence to DatabaseManager and both loggers
- Tracks suppression count in metrics (events_suppressed)

---

## Database Manager

**Responsibility:** Manages SQLite database connection, handles schema initialization and migrations, provides CRUD operations for events.

**Key Interfaces:**
- `init_database(db_path: str) -> None`: Initialize database, create schema, apply migrations
- `insert_event(event: Event) -> bool`: Persist event to database
- `get_event_by_id(event_id: str) -> Event | None`: Retrieve single event
- `get_events_by_timerange(start: datetime, end: datetime) -> list[Event]`: Query events by time
- `get_recent_events(limit: int) -> list[Event]`: Get N most recent events
- `count_events() -> int`: Total event count

**Dependencies:**
- sqlite3 (Python stdlib)
- Pydantic Event model
- SystemConfig (for db_path)

**Technology Stack:**
- Python 3.10+ (stdlib sqlite3 module)
- Module path: `core/database.py`
- Class: `DatabaseManager`

**Implementation Notes:**
- Single shared connection for entire application (no connection pooling needed)
- Schema version tracking in schema_version table
- Migration scripts in migrations/ directory (manual SQL files)
- Uses parameterized queries to prevent SQL injection
- Transaction wrapping for atomicity (insert_event wrapped in BEGIN/COMMIT)
- Index on timestamp DESC for efficient recent event queries

---

## JSON Event Logger

**Responsibility:** Writes events to date-organized JSON log files in JSON Lines format for programmatic processing by external tools.

**Key Interfaces:**
- `log_event(event: Event) -> None`: Append event to appropriate JSON file

**Dependencies:**
- Pydantic Event model (for .model_dump_json())
- SystemConfig (for log directory path)

**Technology Stack:**
- Python 3.10+ (stdlib json and pathlib)
- Module path: `core/json_logger.py`
- Class: `JSONEventLogger`

**Implementation Notes:**
- File organization: `data/events/YYYY-MM-DD/events.json`
- One file per day, new file created at midnight (based on event timestamp)
- JSON Lines format: one JSON object per line, not a JSON array
- Atomic writes: write to temp file, then os.rename() for atomicity
- Auto-creates date directories if missing
- File permissions: 0644 (user read/write, group/others read)

---

## Plaintext Event Logger

**Responsibility:** Writes human-readable plaintext event logs for quick manual review without parsing JSON or querying database.

**Key Interfaces:**
- `log_event(event: Event) -> None`: Append formatted event to plaintext log

**Dependencies:**
- Pydantic Event model
- SystemConfig (for log directory path)

**Technology Stack:**
- Python 3.10+ (stdlib)
- Module path: `core/plaintext_logger.py`
- Class: `PlaintextEventLogger`

**Implementation Notes:**
- File organization: `data/events/YYYY-MM-DD/events.log`
- Log format:
  ```
  [2025-11-08 14:32:15] EVENT: Person detected at front door (confidence: 92%)
    - Objects: person (92%), package (87%)
    - Description: Person in blue shirt carrying brown package approaching front door
    - Image: data/events/2025-11-08/evt_12345.jpg
  ```
- Timestamp in local timezone (YYYY-MM-DD HH:MM:SS)
- Blank line between events for readability
- File rotation synchronized with JSON logger (same midnight boundary)

---

## Storage Monitor

**Responsibility:** Monitors disk usage of data directory, enforces 4GB storage limit, triggers warnings and graceful shutdown when limit approached.

**Key Interfaces:**
- `check_usage() -> StorageStats`: Calculate total storage usage
- `is_over_limit() -> bool`: Check if storage exceeds max_storage_gb

**Dependencies:**
- SystemConfig (for max_storage_gb, storage_check_interval)

**Technology Stack:**
- Python 3.10+ (stdlib os and pathlib)
- Module path: `core/storage_monitor.py`
- Class: `StorageMonitor`

**Implementation Notes:**
- Calculates total size of data/events directory recursively
- Check frequency: every 100 events (configurable)
- Warning threshold: 80% of limit (logs WARNING)
- Critical threshold: 100% of limit (logs ERROR, triggers graceful shutdown)
- Returns StorageStats: total_bytes, limit_bytes, percentage_used, is_over_limit

---

## Log Rotator

**Responsibility:** Implements FIFO log rotation to manage disk space by deleting oldest date directories when storage limit approached.

**Key Interfaces:**
- `rotate_logs() -> int`: Delete old logs, returns bytes freed
- `get_deletion_candidates() -> list[str]`: Identify date directories to delete

**Dependencies:**
- StorageMonitor (to check current usage)
- SystemConfig (for min_retention_days)

**Technology Stack:**
- Python 3.10+ (stdlib shutil for directory deletion)
- Module path: `core/log_rotation.py`
- Class: `LogRotator`

**Implementation Notes:**
- Deletion strategy: oldest first (by YYYY-MM-DD directory name)
- Continues deleting until storage <80% of limit
- Protection: never delete current day's directory
- Minimum retention: at least 7 days regardless of storage (configurable)
- Logs WARNING for each deleted directory with bytes freed

---

## Metrics Collector

**Responsibility:** Collects system performance metrics (frame processing, inference times, CPU/memory usage), calculates percentiles, logs to metrics.json.

**Key Interfaces:**
- `collect() -> MetricsSnapshot`: Gather current metrics
- `record_inference_time(component: str, time_ms: float) -> None`: Track inference time
- `increment_counter(metric: str) -> None`: Increment event/frame counters

**Dependencies:**
- psutil (for CPU/memory monitoring)
- Pydantic MetricsSnapshot model
- SystemConfig (for metrics_interval)

**Technology Stack:**
- Python 3.10+, psutil library
- Module path: `core/metrics.py`
- Class: `MetricsCollector`

**Implementation Notes:**
- Metrics logged every 60 seconds (configurable via metrics_interval)
- Inference times stored in rolling window (last 1000 events)
- Percentiles calculated using numpy.percentile (p95)
- Metrics file: logs/metrics.json (JSON Lines format)
- Overhead target: <1% CPU (measured via profiling)

---

## Processing Pipeline

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

## FastAPI Server (Phase 2)

**Responsibility:** Provides REST API endpoints for web dashboard to query events, retrieve images, and access system metrics.

**Key Interfaces:**
- FastAPI route handlers for all OpenAPI endpoints
- CORS middleware for localhost:3000 (dev) and localhost (prod)
- Static file serving for annotated images

**Dependencies:**
- DatabaseManager (to query events)
- MetricsCollector (to provide current metrics)
- SystemConfig (to provide sanitized config)

**Technology Stack:**
- Python 3.10+, FastAPI 0.104+, Uvicorn ASGI server
- Module path: `api/server.py`
- Class: `FastAPIServer`

**Implementation Notes:**
- Runs in separate process from processing pipeline (dual-process architecture)
- Shares SQLite database via file access (read-only for API)
- No authentication in Phase 2 (localhost-only)
- CORS enabled for http://localhost:3000 (development)
- Static files served from /images route (maps to data/events directory)
- Startup validation: check database exists and is readable

---

## WebSocket Server (Phase 2)

**Responsibility:** Broadcasts new events to connected web dashboard clients in real-time via WebSocket protocol.

**Key Interfaces:**
- WebSocket endpoint: `/ws/events`
- Connection manager tracks active clients
- Broadcast method sends events to all subscribers

**Dependencies:**
- FastAPI WebSocket support
- Event serialization (Pydantic model)

**Technology Stack:**
- Python 3.10+, FastAPI WebSocket, websockets library
- Module path: `api/websocket.py`
- Class: `WebSocketManager`

**Implementation Notes:**
- Integrated with EventManager to receive new events
- Maintains list of active WebSocket connections
- Broadcasts to all clients when new event created
- Removes disconnected clients from subscriber list
- No authentication in Phase 2

---

## Web Dashboard (Phase 2)

**Responsibility:** Provides web UI for viewing events, filtering by time/camera, displaying annotated images, and real-time event notifications.

**Key Interfaces:**
- 5 core screens: Dashboard, Event Timeline, Event Detail, Settings, System Status
- WebSocket client for real-time updates
- REST API client for historical data

**Dependencies:**
- FastAPI server (REST API)
- WebSocket server (real-time events)

**Technology Stack:**
- Vanilla JavaScript ES6+, native CSS, no frameworks
- Module path: `web/` directory
- File structure: `index.html`, `app.js`, `styles.css`, `components/`, `services/`

**Implementation Notes:**
- SPA with hash-based routing (#/dashboard, #/events, etc.)
- Custom Observer pattern for state management
- Dark mode optimized for 4K displays
- Component-based architecture (functional approach)
- No build step - served directly from web/ directory
- API calls via fetch() with error handling

---

# External APIs

## Ollama Local LLM Service

- **Purpose:** Local LLM inference for generating semantic descriptions of detected events
- **Documentation:** https://github.com/ollama/ollama/blob/main/docs/api.md
- **Base URL(s):** http://localhost:11434 (default), configurable via SystemConfig
- **Authentication:** None (local service, no auth required)
- **Rate Limits:** None (local service, limited only by hardware)

**Key Endpoints Used:**
- `POST /api/generate` - Generate text completion with vision model
- `GET /api/tags` - List available models (for health check)

**Integration Notes:**
- Requires Ollama service running locally before application startup
- Recommended models: llava:7b (better accuracy) or moondream:latest (faster inference)
- Health check validates Ollama is reachable and model is downloaded
- Timeout: 10 seconds (configurable via llm_timeout)
- Error handling: Falls back to generic description if LLM unavailable
- Vision models accept image + text prompt, return natural language description

**Installation:**
```bash
# Install Ollama
brew install ollama

# Start Ollama service
ollama serve

# Download vision model
ollama pull llava:7b
```

---

## RTSP Camera Protocol

- **Purpose:** Capture video stream from IP camera for motion detection and object recognition
- **Documentation:** RTSP standard (RFC 2326), camera manufacturer docs for specific URL format
- **Base URL(s):** rtsp://[username:password]@[camera_ip]:[port]/[stream_path]
- **Authentication:** Basic auth via RTSP URL credentials
- **Rate Limits:** Limited by camera's maximum frame rate (typically 15-30 fps)

**Key Endpoints Used:**
- Primary stream: High resolution (1920x1080) for object detection
- Substream: Lower resolution (640x480) for motion detection (camera-dependent)

**Integration Notes:**
- OpenCV VideoCapture handles RTSP protocol negotiation automatically
- URL format varies by manufacturer (Hikvision, Dahua, Reolink, etc.)
- Connection stability depends on network quality
- Implements reconnection logic with exponential backoff
- Frame capture timeout: 5 seconds
- Supports only H.264/H.265 video codecs (most common)

**Example URLs:**
```
# Hikvision
rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101

# Reolink
rtsp://admin:password@192.168.1.100:554/h264Preview_01_main

# Generic
rtsp://username:password@camera-ip:554/stream1
```

---

# Core Workflows

## 1. Motion-Triggered Event Creation (Happy Path)

```mermaid
sequenceDiagram
    participant Pipeline as Processing Pipeline
    participant RTSP as RTSP Camera Client
    participant Motion as Motion Detector
    participant CoreML as CoreML Detector
    participant LLM as Ollama LLM
    participant EventMgr as Event Manager
    participant DB as Database Manager
    participant JSON as JSON Logger
    participant TXT as Plaintext Logger

    Pipeline->>RTSP: get_frame()
    RTSP-->>Pipeline: frame (np.ndarray)

    Pipeline->>Motion: detect_motion(frame)
    Motion-->>Pipeline: (True, 0.87)

    Note over Pipeline: Motion detected, proceed with inference

    Pipeline->>CoreML: detect_objects(frame)
    CoreML-->>Pipeline: [DetectedObject("person", 0.92), DetectedObject("package", 0.87)]

    Note over Pipeline: Objects detected, call LLM

    Pipeline->>LLM: generate_description(frame, objects)
    LLM-->>Pipeline: "Person in blue shirt carrying brown package approaching front door"

    Pipeline->>EventMgr: create_event(frame, objects, description)

    EventMgr->>EventMgr: should_suppress(event)
    Note over EventMgr: Not duplicate, proceed

    EventMgr->>DB: insert_event(event)
    DB-->>EventMgr: True

    EventMgr->>JSON: log_event(event)
    JSON-->>EventMgr: void

    EventMgr->>TXT: log_event(event)
    TXT-->>EventMgr: void

    EventMgr-->>Pipeline: Event created

    Note over Pipeline: Event persisted, continue to next frame
```

---

## 2. Event De-duplication (Suppression Logic)

```mermaid
sequenceDiagram
    participant Pipeline as Processing Pipeline
    participant EventMgr as Event Manager
    participant Cache as Suppression Cache

    Pipeline->>EventMgr: create_event(frame, objects, description)

    EventMgr->>Cache: get_recent_events(limit=5)
    Cache-->>EventMgr: [event1, event2, event3]

    EventMgr->>EventMgr: calculate_object_overlap(new_event, event1)
    Note over EventMgr: 85% overlap - exceeds 80% threshold

    EventMgr->>EventMgr: increment_suppression_counter()

    EventMgr-->>Pipeline: None (event suppressed)

    Note over Pipeline: No persistence, continue to next frame
```

**Suppression Algorithm:**
- Compare new event's detected object labels to last 5 events
- Calculate overlap: `len(set(new) & set(old)) / len(set(new) | set(old))`
- Suppress if overlap ≥ 80%
- Example: ["person", "package"] vs ["person", "dog"] = 1/3 = 33% → NOT suppressed
- Example: ["person", "package"] vs ["person", "package"] = 2/2 = 100% → suppressed

---

## 3. Graceful Shutdown (SIGINT/SIGTERM Handling)

```mermaid
sequenceDiagram
    participant OS as Operating System
    participant Main as main.py
    participant Pipeline as Processing Pipeline
    participant RTSP as RTSP Client
    participant DB as Database Manager
    participant Loggers as JSON/Plaintext Loggers

    OS->>Main: SIGINT (Ctrl+C)

    Main->>Pipeline: shutdown()
    Pipeline->>Pipeline: set shutdown_event

    Note over Pipeline: Complete current frame processing

    Pipeline->>RTSP: disconnect()
    RTSP-->>Pipeline: void

    Pipeline->>DB: close_connection()
    DB-->>Pipeline: void

    Pipeline->>Loggers: flush_buffers()
    Loggers-->>Pipeline: void

    Pipeline-->>Main: shutdown complete

    Main->>Main: log("System shutdown gracefully")
    Main->>OS: exit(0)
```

**Signal Handling:**
- SIGINT (Ctrl+C): Graceful shutdown, logs "User interrupted"
- SIGTERM: Graceful shutdown, logs "Termination signal received"
- SIGHUP (Phase 2): Hot-reload configuration without restart

---

## 4. Error Recovery (RTSP Reconnection)

```mermaid
sequenceDiagram
    participant Pipeline as Processing Pipeline
    participant RTSP as RTSP Client
    participant Logger as Application Logger

    Pipeline->>RTSP: get_frame()
    RTSP-->>Pipeline: None (connection lost)

    Pipeline->>Logger: log.warning("RTSP connection lost")

    Pipeline->>RTSP: is_connected()
    RTSP-->>Pipeline: False

    Pipeline->>Pipeline: sleep(1s)
    Pipeline->>RTSP: connect()
    RTSP-->>Pipeline: False (retry 1 failed)

    Pipeline->>Pipeline: sleep(2s)
    Pipeline->>RTSP: connect()
    RTSP-->>Pipeline: False (retry 2 failed)

    Pipeline->>Pipeline: sleep(4s)
    Pipeline->>RTSP: connect()
    RTSP-->>Pipeline: True (reconnected)

    Pipeline->>Logger: log.info("RTSP connection restored")

    Note over Pipeline: Resume normal processing
```

**Reconnection Strategy:**
- Exponential backoff: 1s, 2s, 4s, 8s (max)
- After 5 consecutive failures: log ERROR and exit
- Reset backoff counter on successful connection
- Continue processing other frames during reconnection attempts

---

## 5. Phase 2 Real-Time Event Streaming (WebSocket)

```mermaid
sequenceDiagram
    participant WebUI as Web Dashboard
    participant WS as WebSocket Server
    participant EventMgr as Event Manager
    participant Pipeline as Processing Pipeline

    WebUI->>WS: connect("ws://localhost:8000/ws/events")
    WS-->>WebUI: connection accepted

    Note over WS: Add client to subscribers

    Pipeline->>EventMgr: create_event(...)
    EventMgr->>EventMgr: persist to DB/logs

    EventMgr->>WS: broadcast_event(event)

    WS->>WebUI: send(event_json)

    Note over WebUI: Update UI with new event

    WebUI->>WebUI: display_notification("New event: Person detected")
    WebUI->>WebUI: prepend_to_timeline(event)

    Note over WebUI: User navigates away

    WebUI->>WS: close()
    WS->>WS: remove_subscriber(client)
```

---

# Database Schema

## Events Table (SQLite)

```sql
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    timestamp DATETIME NOT NULL,
    camera_id TEXT NOT NULL,
    motion_confidence REAL,
    detected_objects TEXT,  -- JSON array: [{"label": "person", "confidence": 0.92, "bbox": {...}}, ...]
    llm_description TEXT,
    image_path TEXT,
    json_log_path TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_camera ON events(camera_id);
CREATE INDEX IF NOT EXISTS idx_events_event_id ON events(event_id);
```

**Field Details:**
- `id`: Auto-incrementing primary key (SQLite ROWID alias)
- `event_id`: Unique identifier for application use (e.g., `evt_1699459335_a7b3c`)
- `timestamp`: Event occurrence time (stored as ISO 8601 string in UTC)
- `camera_id`: Camera identifier (enables future multi-camera queries)
- `motion_confidence`: Motion detection score (0.0-1.0), NULL if not applicable
- `detected_objects`: JSON TEXT field storing array of DetectedObject instances
- `llm_description`: Natural language description from Ollama LLM
- `image_path`: Relative path to annotated image (e.g., `data/events/2025-11-08/evt_12345.jpg`)
- `json_log_path`: Relative path to JSON log file containing this event
- `created_at`: Database insertion timestamp (auto-generated)

**Indexes:**
- `idx_events_timestamp`: Descending order for efficient recent event queries
- `idx_events_camera`: Filter events by camera (Phase 2/3 multi-camera)
- `idx_events_event_id`: Unique lookup by event_id

---

## Schema Migration Strategy

**Migration Table:**
```sql
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_version (version) VALUES (1);
```

**Migration Files:**
```
migrations/
├── 001_initial.sql          # Initial schema (events table + indexes)
├── 002_add_camera_table.sql # Future: Add cameras table for multi-camera
├── 003_add_metadata.sql     # Future: Add event metadata JSON field
└── README.md                # Migration process documentation
```

**Migration Process:**
1. On startup, check current schema_version (SELECT MAX(version))
2. Find migrations with version > current version
3. Apply migrations in sequence within transaction
4. Update schema_version table after each successful migration
5. Log ERROR and exit if migration fails (prevents running with incompatible schema)

**Rollback Strategy:**
- For MVP Phase 1: Backup → delete → recreate (acceptable for single-user system)
- Backup script: `sqlite3 data/events.db .dump > backup.sql`
- Restore script: `sqlite3 data/events.db < backup.sql`

---

## Common Query Patterns

**Get recent events (dashboard):**
```sql
SELECT * FROM events
ORDER BY timestamp DESC
LIMIT 100;
```
Performance: <50ms with 10,000 events (uses idx_events_timestamp)

**Get events in time range (timeline view):**
```sql
SELECT * FROM events
WHERE timestamp BETWEEN '2025-11-08 00:00:00' AND '2025-11-08 23:59:59'
ORDER BY timestamp DESC;
```
Performance: <100ms with 10,000 events (uses idx_events_timestamp)

**Get events by camera (multi-camera):**
```sql
SELECT * FROM events
WHERE camera_id = 'front_door'
ORDER BY timestamp DESC
LIMIT 100;
```
Performance: <50ms with 10,000 events (uses idx_events_camera + idx_events_timestamp)

**Search events by object (future enhancement):**
```sql
SELECT * FROM events
WHERE detected_objects LIKE '%"label": "person"%'
ORDER BY timestamp DESC;
```
Performance: Slow (full table scan) - consider adding FTS5 virtual table in Phase 3

---

## Future Tables (Phase 2/3)

**Cameras Table (Phase 2):**
```sql
CREATE TABLE IF NOT EXISTS cameras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    rtsp_url TEXT NOT NULL,
    location TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**System Metrics Table (Phase 3):**
```sql
CREATE TABLE IF NOT EXISTS system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_timestamp ON system_metrics(timestamp DESC);
```

---

# Frontend Architecture

## Component Architecture

### Component Organization

```
web/
├── index.html                    # SPA entry point
├── app.js                        # Application bootstrap
├── styles.css                    # Global styles and dark mode theme
├── components/
│   ├── Dashboard.js              # Main dashboard view
│   ├── EventTimeline.js          # Event list with timeline
│   ├── EventCard.js              # Single event card component
│   ├── EventDetail.js            # Event detail modal/view
│   ├── Settings.js               # Settings form
│   ├── SystemStatus.js           # System health dashboard
│   ├── ImageViewer.js            # Annotated image viewer with zoom
│   ├── FilterBar.js              # Date/camera filter controls
│   └── Notification.js           # Toast notification component
├── services/
│   ├── apiClient.js              # REST API client wrapper
│   ├── websocketClient.js        # WebSocket client for real-time events
│   └── stateManager.js           # Custom Observer pattern state management
└── utils/
    ├── dateFormatter.js          # Date/time formatting utilities
    ├── router.js                 # Hash-based SPA routing
    └── imageHelper.js            # Image loading and caching
```

### Component Template (Functional Pattern)

```javascript
// components/EventCard.js
/**
 * EventCard component - Displays single event with thumbnail and metadata
 * @param {Event} event - Event object from API
 * @param {Function} onClick - Click handler for event detail navigation
 * @returns {HTMLElement} Rendered event card DOM element
 */
export function EventCard(event, onClick) {
  const card = document.createElement('div');
  card.className = 'event-card';
  card.setAttribute('data-event-id', event.event_id);

  card.innerHTML = `
    <div class="event-card__image">
      <img src="/api/v1/events/${event.event_id}/image"
           alt="${event.llm_description}"
           loading="lazy">
    </div>
    <div class="event-card__content">
      <div class="event-card__header">
        <span class="event-card__time">${formatTimestamp(event.timestamp)}</span>
        <span class="event-card__camera">${event.camera_id}</span>
      </div>
      <p class="event-card__description">${event.llm_description}</p>
      <div class="event-card__objects">
        ${event.detected_objects.map(obj =>
          `<span class="object-tag">${obj.label} (${(obj.confidence * 100).toFixed(0)}%)</span>`
        ).join('')}
      </div>
    </div>
  `;

  card.addEventListener('click', () => onClick(event.event_id));

  return card;
}

// Helper function
function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
}
```

**Component Pattern Guidelines:**
- Components are pure functions that return DOM elements
- No JSX - use template literals and DOM APIs
- Accept data and callbacks as parameters
- Return HTMLElement (not strings)
- Event listeners attached directly to elements
- CSS classes follow BEM naming convention

---

## State Management Architecture

### State Structure (Custom Observer Pattern)

```javascript
// services/stateManager.js
/**
 * AppState - Centralized application state with Observer pattern
 * Notifies subscribers when state changes occur
 */
class AppState {
  constructor() {
    this.state = {
      events: [],
      filters: {
        startDate: null,
        endDate: null,
        cameraId: null
      },
      currentView: 'dashboard',
      selectedEventId: null,
      systemMetrics: null,
      isLoading: false,
      error: null
    };

    this.observers = new Map(); // Map<stateKey, Set<callback>>
  }

  /**
   * Subscribe to state changes for specific key
   * @param {string} key - State key to observe
   * @param {Function} callback - Called when state[key] changes
   * @returns {Function} Unsubscribe function
   */
  subscribe(key, callback) {
    if (!this.observers.has(key)) {
      this.observers.set(key, new Set());
    }
    this.observers.get(key).add(callback);

    // Return unsubscribe function
    return () => {
      this.observers.get(key).delete(callback);
    };
  }

  /**
   * Update state and notify observers
   * @param {string} key - State key to update
   * @param {*} value - New value
   */
  setState(key, value) {
    const oldValue = this.state[key];
    this.state[key] = value;

    // Notify observers only if value changed
    if (oldValue !== value && this.observers.has(key)) {
      this.observers.get(key).forEach(callback => {
        callback(value, oldValue);
      });
    }
  }

  /**
   * Get current state value
   * @param {string} key - State key
   * @returns {*} Current value
   */
  getState(key) {
    return this.state[key];
  }

  /**
   * Batch update multiple state keys
   * @param {Object} updates - Key-value pairs to update
   */
  batchUpdate(updates) {
    Object.entries(updates).forEach(([key, value]) => {
      this.setState(key, value);
    });
  }
}

// Singleton instance
export const appState = new AppState();
```

### State Management Patterns

**Pattern 1: Component subscribes to state**
```javascript
// components/EventTimeline.js
import { appState } from '../services/stateManager.js';

export function EventTimeline() {
  const container = document.createElement('div');
  container.className = 'event-timeline';

  // Subscribe to events state
  const unsubscribe = appState.subscribe('events', (newEvents) => {
    renderEvents(container, newEvents);
  });

  // Initial render
  renderEvents(container, appState.getState('events'));

  // Cleanup on component removal
  container.addEventListener('remove', unsubscribe);

  return container;
}
```

**Pattern 2: API call updates state**
```javascript
// services/apiClient.js
import { appState } from './stateManager.js';

export async function fetchEvents(filters = {}) {
  appState.setState('isLoading', true);

  try {
    const queryParams = new URLSearchParams(filters);
    const response = await fetch(`/api/v1/events?${queryParams}`);

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = await response.json();
    appState.setState('events', data.events);
    appState.setState('error', null);
  } catch (error) {
    appState.setState('error', error.message);
    console.error('Failed to fetch events:', error);
  } finally {
    appState.setState('isLoading', false);
  }
}
```

**Pattern 3: User interaction triggers state change**
```javascript
// components/FilterBar.js
import { appState } from '../services/stateManager.js';
import { fetchEvents } from '../services/apiClient.js';

export function FilterBar() {
  const form = document.createElement('form');
  form.className = 'filter-bar';

  form.innerHTML = `
    <input type="date" name="startDate" id="filter-start">
    <input type="date" name="endDate" id="filter-end">
    <button type="submit">Apply Filters</button>
  `;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const formData = new FormData(form);

    const filters = {
      startDate: formData.get('startDate'),
      endDate: formData.get('endDate')
    };

    appState.setState('filters', filters);
    fetchEvents(filters); // Triggers API call, which updates events state
  });

  return form;
}
```

---

## Routing Architecture

### Route Organization (Hash-based Routing)

```javascript
// utils/router.js
/**
 * Simple hash-based router for SPA navigation
 * Routes map to component factory functions
 */
import { Dashboard } from '../components/Dashboard.js';
import { EventTimeline } from '../components/EventTimeline.js';
import { EventDetail } from '../components/EventDetail.js';
import { Settings } from '../components/Settings.js';
import { SystemStatus } from '../components/SystemStatus.js';

const routes = {
  '': Dashboard,           // #/ or #
  'dashboard': Dashboard,  // #/dashboard
  'events': EventTimeline, // #/events
  'event': EventDetail,    // #/event/:id
  'settings': Settings,    // #/settings
  'status': SystemStatus   // #/status
};

/**
 * Parse hash and extract route + params
 * Example: #/event/evt_12345 -> { route: 'event', params: { id: 'evt_12345' } }
 */
function parseHash() {
  const hash = window.location.hash.slice(1) || '/';
  const [path, ...paramParts] = hash.split('/').filter(Boolean);

  return {
    route: path || '',
    params: {
      id: paramParts[0] || null
    }
  };
}

/**
 * Render component for current route
 */
function render() {
  const { route, params } = parseHash();
  const Component = routes[route] || routes[''];

  const appRoot = document.getElementById('app');
  appRoot.innerHTML = ''; // Clear previous content
  appRoot.appendChild(Component(params));
}

/**
 * Navigate to route programmatically
 * @param {string} path - Route path (e.g., '/events', '/event/evt_12345')
 */
export function navigate(path) {
  window.location.hash = path;
}

/**
 * Initialize router
 */
export function initRouter() {
  window.addEventListener('hashchange', render);
  window.addEventListener('load', render);
}
```

### Navigation Example

```javascript
// components/EventCard.js
import { navigate } from '../utils/router.js';

export function EventCard(event, onClick) {
  // ...
  card.addEventListener('click', () => {
    navigate(`/event/${event.event_id}`);
  });
  // ...
}
```

---

## Frontend Services Layer

### API Client Setup

```javascript
// services/apiClient.js
/**
 * REST API client for backend communication
 * Centralized error handling and request configuration
 */

const BASE_URL = 'http://localhost:8000/api/v1';

/**
 * Generic fetch wrapper with error handling
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;

  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json'
    }
  };

  try {
    const response = await fetch(url, { ...defaultOptions, ...options });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error?.message || `HTTP ${response.status}`);
    }

    // Handle different response types
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) {
      return await response.json();
    } else {
      return await response.blob(); // For images
    }
  } catch (error) {
    console.error(`API request failed: ${endpoint}`, error);
    throw error;
  }
}

/**
 * Export typed API methods
 */
export const api = {
  health: () => apiRequest('/health'),

  metrics: () => apiRequest('/metrics'),

  events: {
    list: (filters = {}) => {
      const params = new URLSearchParams(filters);
      return apiRequest(`/events?${params}`);
    },

    getById: (eventId) => apiRequest(`/events/${eventId}`),

    getImage: (eventId) => apiRequest(`/events/${eventId}/image`)
  },

  config: () => apiRequest('/config')
};
```

### Service Example (WebSocket Client)

```javascript
// services/websocketClient.js
/**
 * WebSocket client for real-time event streaming
 */
import { appState } from './stateManager.js';

class WebSocketClient {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectDelay = 8000; // 8 seconds
  }

  connect() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        if (message.type === 'event') {
          this.handleNewEvent(message.data);
        } else if (message.type === 'error') {
          console.error('WebSocket error:', message.message);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.reconnect();
    };
  }

  reconnect() {
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), this.maxReconnectDelay);
    this.reconnectAttempts++;

    console.log(`Reconnecting in ${delay}ms...`);
    setTimeout(() => this.connect(), delay);
  }

  handleNewEvent(event) {
    // Prepend new event to state
    const currentEvents = appState.getState('events');
    appState.setState('events', [event, ...currentEvents]);

    // Show notification
    showNotification(`New event: ${event.llm_description}`);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Singleton instance
export const wsClient = new WebSocketClient('ws://localhost:8000/ws/events');

// Helper function for notifications
function showNotification(message) {
  // Implementation depends on Notification component
  console.log('Notification:', message);
}
```

---

# Backend Architecture

## Service Architecture (Traditional Server + Processing Engine)

### Dual-Process Architecture

The system runs two separate Python processes in Phase 2:

1. **Processing Engine** (`main.py`): Runs ProcessingPipeline, handles RTSP/CoreML/Ollama/persistence
2. **API Server** (`api/server.py`): Runs FastAPI server, provides REST/WebSocket APIs

**Communication:** Both processes share the SQLite database file (`data/events.db`). The processing engine has read/write access, while the API server has read-only access.

**Rationale:** Separating concerns allows the processing engine to run continuously without HTTP overhead, while the API server can be restarted independently for configuration changes.

---

### Processing Pipeline Organization

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

### FastAPI Server Structure

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

# Unified Project Structure

```
video-recognition/
├── .github/                          # CI/CD workflows
│   └── workflows/
│       ├── ci.yaml                   # Run tests on push/PR
│       └── lint.yaml                 # Code quality checks
│
├── core/                             # Platform-independent business logic
│   ├── __init__.py
│   ├── processing_pipeline.py        # Main orchestration pipeline
│   ├── motion_detector.py            # Motion detection (OpenCV)
│   ├── event_manager.py              # Event creation and de-duplication
│   ├── database.py                   # DatabaseManager (SQLite)
│   ├── json_logger.py                # JSON event logging
│   ├── plaintext_logger.py           # Plaintext event logging
│   ├── storage_monitor.py            # Disk usage monitoring
│   ├── log_rotation.py               # FIFO log rotation
│   ├── metrics.py                    # MetricsCollector
│   └── config.py                     # Configuration loading (Pydantic)
│
├── platform/                         # Apple Silicon-specific implementations
│   ├── __init__.py
│   └── coreml_detector.py            # CoreML Object Detector (Neural Engine)
│
├── integrations/                     # External service clients
│   ├── __init__.py
│   ├── rtsp_client.py                # RTSP Camera Client (OpenCV)
│   └── ollama_client.py              # Ollama LLM Processor
│
├── api/                              # Phase 2: FastAPI web server
│   ├── __init__.py
│   ├── server.py                     # FastAPI application
│   ├── websocket.py                  # WebSocket manager
│   └── middleware/                   # Custom middleware (future)
│
├── web/                              # Phase 2: Vanilla JavaScript web dashboard
│   ├── index.html                    # SPA entry point
│   ├── app.js                        # Application bootstrap
│   ├── styles.css                    # Global styles and dark mode theme
│   ├── components/
│   │   ├── Dashboard.js
│   │   ├── EventTimeline.js
│   │   ├── EventCard.js
│   │   ├── EventDetail.js
│   │   ├── Settings.js
│   │   ├── SystemStatus.js
│   │   ├── ImageViewer.js
│   │   ├── FilterBar.js
│   │   └── Notification.js
│   ├── services/
│   │   ├── apiClient.js              # REST API client
│   │   ├── websocketClient.js        # WebSocket client
│   │   └── stateManager.js           # Custom Observer pattern state
│   └── utils/
│       ├── dateFormatter.js
│       ├── router.js                 # Hash-based routing
│       └── imageHelper.js
│
├── config/                           # Configuration files
│   ├── config.yaml                   # Main system configuration
│   └── config.schema.json            # JSON Schema for validation
│
├── tests/                            # Test organization
│   ├── unit/                         # Unit tests (fast, isolated)
│   │   ├── test_motion_detector.py
│   │   ├── test_event_manager.py
│   │   ├── test_database.py
│   │   └── ...
│   ├── integration/                  # Integration tests (slower, real dependencies)
│   │   ├── test_pipeline_integration.py
│   │   ├── test_database_integration.py
│   │   └── test_api_integration.py
│   └── performance/                  # Performance tests (NFR validation)
│       ├── test_coreml_performance.py
│       └── test_llm_performance.py
│
├── data/                             # Runtime data (gitignored)
│   ├── events.db                     # SQLite database
│   └── events/                       # Date-organized event data
│       └── YYYY-MM-DD/
│           ├── events.json           # JSON Lines log
│           ├── events.log            # Plaintext log
│           └── evt_*.jpg             # Annotated images
│
├── logs/                             # Application logs (gitignored)
│   ├── app.log                       # Application log file
│   └── metrics.json                  # Metrics log (JSON Lines)
│
├── models/                           # CoreML models (gitignored, downloaded at setup)
│   └── yolov8n.mlmodel               # YOLO v8 Nano CoreML model
│
├── migrations/                       # Database migration scripts
│   ├── 001_initial.sql               # Initial schema
│   └── README.md                     # Migration process docs
│
├── scripts/                          # Setup and utility scripts
│   ├── setup.sh                      # Initial setup (venv, dependencies, directories)
│   ├── download_models.sh            # Download CoreML models
│   └── backup_database.sh            # SQLite backup script
│
├── main.py                           # CLI entry point for processing engine
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variables template
├── .gitignore                        # Git ignore patterns
├── pyproject.toml                    # Python project metadata and tool configs
└── README.md                         # Project documentation

```

---

## Directory Explanations

**core/**: Platform-independent business logic that could theoretically run on any OS. Contains the processing pipeline, event management, database access, logging, and metrics. No Apple-specific code here.

**platform/**: Apple Silicon-specific implementations. Currently only CoreML detector. Future: Metal-accelerated image processing, Vision framework integration.

**integrations/**: External service clients. RTSP camera client (OpenCV) and Ollama LLM client. These are abstracted to enable mocking in tests.

**api/**: Phase 2 FastAPI web server. Separate from core processing pipeline to enable dual-process architecture. Includes REST endpoints and WebSocket server.

**web/**: Phase 2 vanilla JavaScript web dashboard. No build step required - served directly from this directory. Uses ES6 modules with native browser imports.

**config/**: YAML configuration files with Pydantic schema validation. Keeps sensitive data (RTSP credentials) out of code.

**tests/**: Three-tier test organization:
- **unit/**: Fast, isolated tests with mocked dependencies (<1s per test)
- **integration/**: Tests with real dependencies (database, file system) (1-5s per test)
- **performance/**: NFR validation tests (inference times, throughput) (10-60s per test)

**data/**: Runtime data directory. Gitignored. Created automatically on first run. Contains SQLite database and date-organized event files.

**logs/**: Application logs. Gitignored. Contains rotating application log and metrics log (JSON Lines format).

**models/**: CoreML model files. Gitignored (large files). Downloaded during setup via scripts/download_models.sh.

**migrations/**: Manual SQL migration scripts. Versioned files (001_initial.sql, 002_*.sql, etc.) applied sequentially on startup.

**scripts/**: Setup and maintenance scripts. Bash scripts for environment setup, model downloads, database backups.

---

## File Naming Conventions

| Element | Convention | Example | Notes |
|---------|-----------|---------|-------|
| Python modules | snake_case | `motion_detector.py` | Lowercase with underscores |
| Python classes | PascalCase | `MotionDetector`, `DatabaseManager` | One class per file (generally) |
| Test files | `test_*.py` | `test_motion_detector.py` | Prefix with `test_` for pytest discovery |
| JavaScript files | PascalCase (components), camelCase (services) | `EventCard.js`, `apiClient.js` | Components capitalized, utilities/services camelCase |
| Configuration | lowercase | `config.yaml` | No underscores or capitals |
| SQL migrations | `NNN_description.sql` | `001_initial.sql` | Three-digit version prefix |
| Scripts | snake_case.sh | `download_models.sh` | Bash scripts with `.sh` extension |

---

## Import Path Examples

**Core module importing another core module:**
```python
# core/event_manager.py
from core.database import DatabaseManager
from core.json_logger import JSONEventLogger
```

**Platform module importing core:**
```python
# platform/coreml_detector.py
from core.config import SystemConfig
```

**Integration importing core:**
```python
# integrations/ollama_client.py
from core.config import SystemConfig
```

**Main entry point:**
```python
# main.py
from core.processing_pipeline import ProcessingPipeline
from core.config import load_config
```

**API server importing core:**
```python
# api/server.py
from core.database import DatabaseManager
from core.metrics import MetricsCollector
from core.config import load_config
```

**Test importing module under test:**
```python
# tests/unit/test_motion_detector.py
from core.motion_detector import MotionDetector
```

---

## Gitignore Strategy

```.gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo

# macOS
.DS_Store

# Runtime data
data/
logs/
models/

# Environment
.env
.env.local

# Test coverage
.coverage
htmlcov/
.pytest_cache/
```

**Rationale:**
- `data/`, `logs/`, `models/` excluded because they're generated at runtime
- `.env` excluded to prevent credentials from being committed
- `__pycache__/` excluded (Python bytecode, regenerated on import)
- IDE configs excluded (developer preference, not project requirement)

---

## Environment Variables

**`.env.example` (committed):**
```bash
# Camera Configuration
CAMERA_RTSP_URL="rtsp://admin:password@192.168.1.100:554/stream1"
CAMERA_ID="front_door"

# Ollama Configuration
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL="llava:7b"

# Database
DB_PATH="data/events.db"

# Storage
MAX_STORAGE_GB="4.0"

# Logging
LOG_LEVEL="INFO"
```

**`.env` (gitignored, created by developer):**
```bash
# Copy from .env.example and fill in actual credentials
CAMERA_RTSP_URL="rtsp://admin:MyRealPassword@192.168.1.100:554/stream1"
CAMERA_ID="garage_camera"
OLLAMA_MODEL="moondream:latest"
```

**Loading in Python:**
```python
# core/config.py
from pydantic_settings import BaseSettings

class SystemConfig(BaseSettings):
    camera_rtsp_url: str
    camera_id: str = "camera_1"
    # ... other fields

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

---

## Project Metadata (pyproject.toml)

```toml
[project]
name = "video-recognition-system"
version = "1.0.0"
description = "Local video recognition system optimized for Apple Silicon"
authors = [{name = "Your Name", email = "you@example.com"}]
requires-python = ">=3.10"
dependencies = [
    "opencv-python>=4.8.1",
    "coremltools>=7.0",
    "ollama>=0.1.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "pyyaml>=6.0",
    "fastapi>=0.104",
    "uvicorn>=0.24",
    "websockets>=12.0",
    "psutil>=5.9",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-cov>=4.1",
    "black>=23.0",
    "ruff>=0.1",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
addopts = "--cov=core --cov=platform --cov=integrations --cov-report=html --cov-report=term"

[tool.black]
line-length = 100
target-version = ["py310"]

[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I"]
ignore = ["E501"]  # Line too long (handled by black)
```

---

## Rationale

**Why monorepo over polyrepo?**
- All code changes are atomic (single commit touches backend + frontend + tests)
- Shared types/models between Python and JavaScript (via JSON schema generation)
- Simpler dependency management (single requirements.txt)
- Better suited for AI-driven development (agent sees complete context)

**Why functional grouping (core/, platform/, integrations/) over feature-based (events/, cameras/)?**
- Clear separation of concerns by architectural layer
- Platform-specific code isolated in platform/ (easier to port to other OSes in future)
- Dependencies flow one direction (integrations → platform → core)
- Aligns with testing strategy (unit tests for core, integration tests for integrations)

**Why three-tier test organization (unit/, integration/, performance/)?**
- Fast feedback loop: unit tests run in <10s, integration in <60s
- Selective test execution: `pytest tests/unit` for quick checks
- Clear expectations: unit tests must have mocked dependencies
- NFR validation: performance tests explicitly validate quantitative targets

**Why models not in git?**
- CoreML files are large (50-500MB), would bloat repository
- Model versions may change frequently during experimentation
- Download script (scripts/download_models.sh) ensures reproducibility
- Models are effectively binary artifacts, not source code

**Why config as example file (.env.example vs .env)?**
- Prevents accidental credential leaks (RTSP passwords)
- Documents required environment variables for new developers
- Allows per-developer customization (different camera URLs)

---

# Development Workflow

## Local Development Setup

### Prerequisites

```bash
# macOS with Apple Silicon (M1/M2/M3)
system_profiler SPHardwareDataType | grep "Chip:"

# Python 3.10 or higher
python3 --version

# Homebrew (for Ollama installation)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Node.js and npm (optional, only needed if using md-tree for PRD sharding)
node --version
npm --version
```

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd video-recognition/

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Ollama
brew install ollama

# Start Ollama service (in separate terminal)
ollama serve

# Download vision model (7B parameter model, ~4GB download)
ollama pull llava:7b
# Alternative: Faster but less accurate model
# ollama pull moondream:latest

# Create data and log directories
mkdir -p data/events logs models

# Download CoreML model
bash scripts/download_models.sh

# Copy environment template and configure
cp .env.example .env
nano .env  # Edit with your RTSP camera URL and credentials

# Initialize database
python main.py --dry-run  # Validates config and creates database schema

# Run tests to verify setup
pytest tests/unit -v
```

### Development Commands

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Start processing engine (Phase 1 CLI)
python main.py

# Start processing engine with debug logging
python main.py --log-level DEBUG

# Dry-run mode (validates config, tests connections, doesn't process)
python main.py --dry-run

# Phase 2: Start API server (separate terminal)
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000

# Phase 2: Serve web dashboard (separate terminal)
python -m http.server 3000 --directory web/

# Run all tests
pytest

# Run only unit tests (fast)
pytest tests/unit -v

# Run tests with coverage report
pytest --cov=core --cov=platform --cov=integrations --cov-report=html

# Run performance tests (validates NFRs)
pytest tests/performance -v --log-cli-level=INFO

# Code formatting
black core/ platform/ integrations/ api/ tests/

# Lint code
ruff check core/ platform/ integrations/ api/

# Type checking (optional, Phase 3)
# mypy core/ platform/ integrations/ api/

# Database backup
bash scripts/backup_database.sh

# View database content
sqlite3 data/events.db
# SQL> SELECT * FROM events ORDER BY timestamp DESC LIMIT 10;

# View logs in real-time
tail -f logs/app.log

# View metrics
cat logs/metrics.json | jq .  # Pretty-print JSON Lines
```

## Environment Configuration

### Required Environment Variables

```bash
# Frontend (.env.local) - Not needed for Phase 1
# Phase 2 only, for web dashboard development
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws/events

# Backend (.env)
# Camera Configuration
CAMERA_RTSP_URL=rtsp://username:password@camera-ip:554/stream1
CAMERA_ID=front_door

# Motion Detection
MOTION_THRESHOLD=0.5
FRAME_SAMPLE_RATE=5

# Object Detection
COREML_MODEL_PATH=models/yolov8n.mlmodel
BLACKLIST_OBJECTS=bird,cat
MIN_OBJECT_CONFIDENCE=0.5

# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llava:7b
LLM_TIMEOUT=10

# Storage
DB_PATH=data/events.db
MAX_STORAGE_GB=4.0
MIN_RETENTION_DAYS=7

# Logging
LOG_LEVEL=INFO
METRICS_INTERVAL=60

# Shared (Backend + Frontend)
# None for Phase 1/2 - all config is backend-only
# Future: Phase 3 may introduce shared API keys, feature flags, etc.
```

**Environment Variable Loading:**
- Backend: Loaded via Pydantic Settings (`core/config.py`)
- Frontend: Not used in Phase 1; Phase 2 uses browser environment (no env vars)
- Precedence: `.env` file < environment variables < command-line arguments

**Validation:**
- Missing required variables: Application exits with clear error message
- Invalid values: Pydantic raises ValidationError with field-specific details
- Example error: `ValidationError: 1 validation error for SystemConfig\nmotion_threshold\n  ensure this value is between 0.0 and 1.0 (type=value_error.number.not_in_range)`

---

# Deployment Architecture

## Deployment Strategy

**Frontend Deployment (Phase 2):**
- **Platform:** Local machine (Mac Mini/Studio) - served via nginx or Python HTTP server
- **Build Command:** None - vanilla JavaScript served directly from `web/` directory
- **Output Directory:** `web/` (source files served as-is, no compilation)
- **CDN/Edge:** Not applicable - localhost-only access, no CDN needed

**Backend Deployment:**
- **Platform:** macOS (Mac Mini or Mac Studio with Apple Silicon)
- **Build Command:** None - Python is interpreted, no compilation step
- **Deployment Method:** Manual file transfer to production machine, managed as system service

**Processing Engine (Phase 1):**
- Runs as `launchd` service (macOS system daemon)
- Service file: `~/Library/LaunchAgents/com.local.video-recognition.plist`
- Auto-starts on boot, restarts on crash
- Logs to `logs/app.log` and system log

**API Server (Phase 2):**
- Runs as separate `launchd` service
- Service file: `~/Library/LaunchAgents/com.local.video-recognition.api.plist`
- Listens on `http://localhost:8000`
- Only accessible from local network (no public internet exposure)

**Web Dashboard (Phase 2):**
- Served via nginx reverse proxy or Python HTTP server
- Accessible at `http://[mac-mini-ip]:3000` on local network
- Static file serving (no server-side rendering)

**Rationale:**
- No cloud deployment needed - privacy-first architecture requires local processing
- systemd/launchd ensures 24/7 operation with automatic recovery
- Manual deployment acceptable for personal project (no CI/CD deployment pipeline)
- Nginx provides production-grade static file serving and reverse proxy

---

## CI/CD Pipeline

**GitHub Actions Configuration:**

```yaml
# .github/workflows/ci.yaml
name: Continuous Integration

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    name: Test Suite
    runs-on: macos-13  # macOS runner required for CoreML testing

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.10
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov black ruff

      - name: Run linters
        run: |
          black --check core/ platform/ integrations/ api/ tests/
          ruff check core/ platform/ integrations/ api/

      - name: Run unit tests
        run: |
          pytest tests/unit -v --cov=core --cov=platform --cov=integrations --cov-report=xml

      - name: Run integration tests
        run: |
          pytest tests/integration -v

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: false

      - name: Check coverage threshold
        run: |
          coverage report --fail-under=70

  lint-frontend:
    name: Lint Frontend (Phase 2)
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run ESLint (if configured)
        run: |
          # Phase 2: Add ESLint check for web/ directory
          echo "Frontend linting placeholder"

  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Bandit (Python security linter)
        run: |
          pip install bandit
          bandit -r core/ platform/ integrations/ api/ -ll

      - name: Check dependencies for vulnerabilities
        run: |
          pip install safety
          safety check -r requirements.txt
```

**CI/CD Limitations:**
- **No automatic deployment** - CI only runs tests, deployment is manual
- **macOS runners required** - CoreML tests only run on Apple Silicon (expensive on GitHub Actions)
- **Performance tests skipped in CI** - NFR validation tests run too long for CI (run manually)
- **WebSocket tests may be flaky** - Integration tests with real WebSocket connections can timeout

**Manual Deployment Process:**
1. Run full test suite locally (including performance tests)
2. Tag release version: `git tag v1.0.0 && git push --tags`
3. Copy files to production machine via rsync or git pull
4. Restart services: `launchctl restart com.local.video-recognition`
5. Verify health check: `curl http://localhost:8000/api/v1/health`

---

## Environments

| Environment | Frontend URL | Backend URL | Purpose |
|-------------|-------------|-------------|---------|
| **Development** | http://localhost:3000 | http://localhost:8000 | Local development on MacBook Pro, uses test RTSP stream or recorded video file |
| **Production** | http://[mac-mini-ip]:3000 | http://[mac-mini-ip]:8000 | 24/7 operation on Mac Mini/Studio with live RTSP camera, accessible on local network only |

**Environment Differences:**

**Development Environment:**
- **Hardware:** M1 MacBook Pro (developer machine)
- **Camera Source:** Test RTSP stream or recorded video file (`data/test-video.mp4`)
- **Ollama Model:** Smaller model (moondream:latest) for faster iteration
- **Storage Limit:** 1GB (lower limit for faster testing)
- **Log Level:** DEBUG (verbose logging for troubleshooting)
- **Startup:** Manual start via `python main.py` or `pytest`

**Production Environment:**
- **Hardware:** Mac Mini or Mac Studio (dedicated 24/7 machine)
- **Camera Source:** Live RTSP camera stream (192.168.1.100)
- **Ollama Model:** Full model (llava:7b) for better accuracy
- **Storage Limit:** 4GB (full limit per NFR)
- **Log Level:** INFO (minimal logging, only warnings/errors)
- **Startup:** Automatic via launchd, restarts on crash

**No Staging Environment:**
- Not needed for personal learning project
- Development → Production is sufficient
- Manual testing on production machine before switching to live camera

**Environment Configuration:**

Development (`.env`):
```bash
CAMERA_RTSP_URL=rtsp://demo:demo@192.168.1.200:554/test
LOG_LEVEL=DEBUG
OLLAMA_MODEL=moondream:latest
MAX_STORAGE_GB=1.0
```

Production (`.env` on Mac Mini):
```bash
CAMERA_RTSP_URL=rtsp://admin:SecurePassword@192.168.1.100:554/stream1
LOG_LEVEL=INFO
OLLAMA_MODEL=llava:7b
MAX_STORAGE_GB=4.0
```

---

## Deployment Procedures

### Initial Production Setup

```bash
# On Production Machine (Mac Mini/Studio)

# 1. Install system dependencies
brew install python@3.10 ollama sqlite

# 2. Start Ollama service
brew services start ollama

# 3. Download LLM model
ollama pull llava:7b

# 4. Clone repository
git clone <repository-url> /opt/video-recognition
cd /opt/video-recognition

# 5. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 6. Install dependencies
pip install -r requirements.txt

# 7. Download CoreML model
bash scripts/download_models.sh

# 8. Configure environment
cp .env.example .env
nano .env  # Edit with production values

# 9. Create data directories
mkdir -p data/events logs models

# 10. Initialize database
python main.py --dry-run

# 11. Test run (foreground)
python main.py
# Ctrl+C after verifying it works

# 12. Install as launchd service
cp scripts/com.local.video-recognition.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.local.video-recognition.plist

# 13. Verify service is running
launchctl list | grep video-recognition
tail -f logs/app.log
```

### launchd Service Configuration

**Processing Engine Service** (`com.local.video-recognition.plist`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.local.video-recognition</string>

    <key>ProgramArguments</key>
    <array>
        <string>/opt/video-recognition/venv/bin/python</string>
        <string>/opt/video-recognition/main.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/opt/video-recognition</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>

    <key>StandardOutPath</key>
    <string>/opt/video-recognition/logs/stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/opt/video-recognition/logs/stderr.log</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>  <!-- Restart on crash -->
    </dict>

    <key>ProcessType</key>
    <string>Interactive</string>  <!-- Allows access to GPU/Neural Engine -->
</dict>
</plist>
```

**API Server Service (Phase 2)** (`com.local.video-recognition.api.plist`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.local.video-recognition.api</string>

    <key>ProgramArguments</key>
    <array>
        <string>/opt/video-recognition/venv/bin/uvicorn</string>
        <string>api.server:app</string>
        <string>--host</string>
        <string>0.0.0.0</string>
        <string>--port</string>
        <string>8000</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/opt/video-recognition</string>

    <key>StandardOutPath</key>
    <string>/opt/video-recognition/logs/api-stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/opt/video-recognition/logs/api-stderr.log</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

### Updating Production Deployment

```bash
# On Production Machine

# 1. Stop services
launchctl unload ~/Library/LaunchAgents/com.local.video-recognition.plist
launchctl unload ~/Library/LaunchAgents/com.local.video-recognition.api.plist  # Phase 2

# 2. Backup database
bash scripts/backup_database.sh

# 3. Pull latest code
cd /opt/video-recognition
git pull origin main

# 4. Update dependencies (if requirements.txt changed)
source venv/bin/activate
pip install -r requirements.txt

# 5. Run migrations (if database schema changed)
python scripts/run_migrations.py

# 6. Restart services
launchctl load ~/Library/LaunchAgents/com.local.video-recognition.plist
launchctl load ~/Library/LaunchAgents/com.local.video-recognition.api.plist  # Phase 2

# 7. Verify deployment
sleep 5
curl http://localhost:8000/api/v1/health  # Phase 2
tail -f logs/app.log
```

### Rollback Procedure

```bash
# If deployment fails, rollback to previous version

# 1. Stop services
launchctl unload ~/Library/LaunchAgents/com.local.video-recognition.plist

# 2. Rollback code
git reset --hard HEAD~1  # Or specific commit: git reset --hard <commit-sha>

# 3. Restore database backup (if schema changed)
cp backups/events_backup_<timestamp>.db data/events.db

# 4. Restart services
launchctl load ~/Library/LaunchAgents/com.local.video-recognition.plist

# 5. Verify rollback
tail -f logs/app.log
```

### Monitoring Production

```bash
# Check service status
launchctl list | grep video-recognition

# View recent logs
tail -n 100 logs/app.log

# View real-time logs
tail -f logs/app.log

# Check health endpoint (Phase 2)
curl http://localhost:8000/api/v1/health | jq .

# View metrics
tail -n 10 logs/metrics.json | jq .

# Check disk usage
du -sh data/
df -h .

# Check system resources
top -pid $(pgrep -f "python main.py")

# View database stats
sqlite3 data/events.db "SELECT COUNT(*) FROM events;"
sqlite3 data/events.db "SELECT DATE(timestamp) as day, COUNT(*) as count FROM events GROUP BY day ORDER BY day DESC LIMIT 7;"
```

---

# Security and Performance

## Security Requirements

### Frontend Security (Phase 2)

**CSP Headers:** Not implemented in Phase 1/2 (localhost-only access)
- Phase 3 consideration: If remote access is added, implement Content Security Policy headers
- Recommended policy: `default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'`
- Rationale for Phase 2: Localhost-only deployment means CSP provides minimal security benefit

**XSS Prevention:**
- Strategy: Escape all user-generated content before rendering to DOM
- Implementation: Use `textContent` instead of `innerHTML` for dynamic text
- Example: `element.textContent = event.llm_description` (safe) vs `element.innerHTML = event.llm_description` (unsafe)
- LLM descriptions sanitized: Ollama output is plain text, no HTML/script injection risk
- Object labels from CoreML: Predefined class names (person, car, dog), no user input

**Secure Storage:**
- Strategy: No sensitive data stored in browser (no auth tokens, no credentials)
- LocalStorage: Not used (all state is ephemeral, reloaded from API on page refresh)
- SessionStorage: Not used
- Cookies: Not used (no authentication in Phase 2)
- Rationale: Stateless frontend reduces attack surface

### Backend Security

**Input Validation:**
- Approach: Pydantic validation for all configuration and API inputs
- Configuration: SystemConfig Pydantic model validates all environment variables
- API requests: FastAPI automatically validates query parameters and request bodies
- Example: `limit` parameter constrained to 1-1000, `confidence` to 0.0-1.0
- SQL injection prevention: Parameterized queries used exclusively (no string concatenation)

**Rate Limiting:**
- Configuration: Not implemented in Phase 2 (localhost-only, single user)
- Phase 3 consideration: If remote access added, implement rate limiting via FastAPI middleware
- Recommended: 100 requests/minute per IP, 1000 requests/hour
- Implementation: `slowapi` library (FastAPI-compatible rate limiter)

**CORS Policy:**
- Configuration: Restricted to localhost origins only
- Allowed origins: `http://localhost:3000`, `http://localhost`
- Allowed methods: `GET`, `POST` (no `DELETE` or `PUT` in API)
- Credentials: Enabled (allow cookies for future auth)
- Example configuration in `api/server.py`:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:3000", "http://localhost"],
      allow_credentials=True,
      allow_methods=["GET", "POST"],
      allow_headers=["*"],
  )
  ```

### Authentication Security (Phase 2: None, Phase 3: Planned)

**Token Storage (Phase 3):**
- Strategy: HttpOnly cookies for refresh tokens, memory-only for access tokens
- Rationale: HttpOnly cookies prevent XSS theft, memory storage prevents CSRF
- Implementation: FastAPI OAuth2PasswordBearer with JWT tokens

**Session Management (Phase 3):**
- Approach: Stateless JWT tokens with 15-minute expiration
- Refresh tokens: 7-day expiration, stored in HttpOnly cookie
- Session invalidation: Token blacklist in Redis (if remote access added)

**Password Policy (Phase 3):**
- Requirements: Not applicable - no user accounts in Phase 1/2
- Future: If multi-user support added, enforce minimum 12 characters, complexity requirements
- Recommendation: Use passkeys/WebAuthn instead of passwords for better security

### Additional Security Considerations

**RTSP Credentials:**
- Storage: Environment variables only (`.env` file, gitignored)
- Never logged: Credentials redacted from all log output
- Example: Log shows `rtsp://***:***@192.168.1.100:554/stream1` instead of actual password
- Transmission: RTSP uses Basic Auth over local network (acceptable for home use)
- Phase 3: Consider RTSP over TLS (RTSPS) if camera supports it

**Database Security:**
- File permissions: SQLite database file has 0600 permissions (owner read/write only)
- Access control: Single application user, no multi-user access
- Encryption at rest: Not implemented (macOS FileVault provides disk-level encryption)
- Backup security: Database backups inherit same file permissions

**API Endpoint Security:**
- Localhost binding: API server only binds to `0.0.0.0` (all interfaces) for local network access
- Firewall: macOS firewall blocks external access (only local network can reach API)
- No public internet exposure: Router firewall prevents WAN access
- Phase 3: Add basic auth or API keys if exposing to internet

**Secret Management:**
- Current approach: `.env` file with restrictive permissions (0600)
- Production: Ensure `.env` is not readable by other users on system
- Future: Consider macOS Keychain integration for RTSP credentials
- No cloud secrets: No AWS/Azure/GCP credentials needed (100% local)

**Vulnerability Management:**
- Dependency scanning: GitHub Dependabot enabled for automated security updates
- Python packages: `safety check` runs in CI pipeline (checks for known vulnerabilities)
- Update cadence: Monthly review of dependency updates, immediate for critical CVEs
- Minimal dependencies: Only 10 production dependencies reduces attack surface

---

## Performance Optimization

### Frontend Performance (Phase 2)

**Bundle Size Target:** Not applicable - no bundling, vanilla JavaScript served directly
- Actual size: ~50KB total (all JS files combined)
- No framework overhead: React bundle would be ~140KB min+gzip, avoided entirely
- Image optimization: Annotated images served as JPEG with 85% quality (balance size vs clarity)
- Lazy loading: Images loaded on-demand with `loading="lazy"` attribute

**Loading Strategy:**
- ES6 modules: Browser-native module loading, no webpack/vite needed
- Code splitting: Manual - dashboard, timeline, settings loaded as separate modules
- Initial page load: <100ms (only loads app.js and minimal CSS)
- Subsequent navigation: Instant (hash-based routing, no server round-trip)
- Time to interactive: <500ms on 4K display

**Caching Strategy:**
- Service Worker: Not implemented (Phase 3 enhancement)
- Browser cache: Leverage HTTP cache headers for static assets
  - `.js` files: `Cache-Control: public, max-age=3600` (1 hour)
  - `.css` files: `Cache-Control: public, max-age=3600`
  - Images: `Cache-Control: public, max-age=86400` (24 hours)
- API responses: No caching (always fetch fresh data)
- WebSocket: Real-time updates bypass cache entirely

**Rendering Performance:**
- Virtual scrolling: Implemented for event timeline (only render visible events)
- Batch DOM updates: Use DocumentFragment for multi-element inserts
- Debounced filters: Filter inputs debounced to 300ms to avoid excessive re-renders
- Image thumbnails: Generate smaller thumbnails server-side (future enhancement)
- CSS animations: GPU-accelerated (use `transform` and `opacity`, avoid `left`/`top`)

### Backend Performance

**Response Time Target:**
- Health check: <10ms
- Event list (100 events): <50ms
- Event detail: <20ms
- Image retrieval: <100ms (depends on file size, ~500KB images)
- Metrics endpoint: <30ms

**Database Optimization:**
- Indexes: Three indexes on events table (timestamp DESC, camera_id, event_id)
- Query optimization: Use `LIMIT` and `OFFSET` for pagination, avoid full table scans
- Connection pooling: Single shared connection (sufficient for read-only API access)
- Prepared statements: SQLite query plan cached for repeated queries
- Vacuum schedule: Run `VACUUM` monthly to reclaim deleted space and rebuild indexes
- Performance monitoring: Log slow queries (>100ms) at WARNING level

**Caching Strategy:**
- In-memory cache: Not implemented in Phase 1/2 (database is fast enough)
- Phase 3: Consider Redis cache for frequently accessed events
- Static files: nginx/Python HTTP server handles static file caching
- No cache invalidation needed: Events are immutable (never updated after creation)

**CoreML Inference Optimization:**
- Neural Engine utilization: Validate model runs on ANE (not GPU or CPU)
- Model selection: YOLOv8 Nano (smallest YOLO variant, <10MB, <100ms inference)
- Input preprocessing: Batch preprocessing outside timed section
  - Resize frame to 640x640 before inference
  - Convert BGR (OpenCV) to RGB (CoreML) once
- Inference frequency: Only run on frames with motion (reduces 95% of frames)
- Target: <100ms per frame (NFR requirement)
- Monitoring: Log inference times, alert if p95 exceeds 100ms

**Ollama LLM Optimization:**
- Model selection: llava:7b (balance of speed vs accuracy)
  - Alternative: moondream:latest (3x faster, lower accuracy)
- Prompt optimization: Minimal prompt to reduce token count
  - Template: "Describe what is happening in this image. Focus on: {object_labels}"
  - Avoid verbose instructions (each token adds latency)
- Timeout: 10 seconds (prevent hanging on slow responses)
- Inference frequency: Only run when objects detected (not every frame)
- Target: <3 seconds per event (NFR requirement)
- Monitoring: Track p95 latency, consider model downgrade if consistently >3s

**Processing Pipeline Optimization:**
- Sequential execution: No threading/async overhead for MVP
- Frame skipping: Skip frames during processing (capture at 30fps, process at 5fps during motion)
- Early exit: Return immediately from pipeline stages if no work to do
  - No motion? Skip CoreML and LLM
  - No objects? Skip LLM
  - Duplicate event? Skip persistence
- Resource efficiency: <2GB memory usage, <50% CPU on M1

**Storage Optimization:**
- Image compression: JPEG quality 85% (reduces 500KB images to ~150KB)
- FIFO rotation: Automatically delete old events when storage limit reached
- Database size: SQLite file size stays <100MB with 30 days of data
- Log rotation: Compress old logs with gzip (10:1 compression ratio)
- Efficient indexing: Indexes add <10% overhead to database size

**API Server Optimization:**
- Async framework: FastAPI with uvicorn (handles concurrent requests efficiently)
- Database queries: Read-only access, no write locks, high concurrency
- Static file serving: nginx serves images directly (no Python overhead)
- WebSocket: Broadcast to all clients in <10ms
- Connection limits: No limit (localhost-only, single user, low traffic)

### Performance Monitoring

**Key Performance Indicators:**
- CoreML inference time: p50, p95, p99 (target: <100ms p95)
- LLM inference time: p50, p95, p99 (target: <3s p95)
- Frame processing latency: End-to-end time from motion detection to event logged (target: <5s)
- API response times: Per endpoint (target: <50ms for event list)
- Memory usage: Current and peak (target: <2GB)
- CPU usage: Average and peak (target: <50% sustained on M1)
- Storage growth rate: MB per day (target: <150MB/day for 4GB/30days)

**Performance Testing:**
- Unit tests: Mock expensive operations (CoreML, LLM) for fast feedback
- Integration tests: Use small test models for faster execution
- Performance tests: Separate test suite in `tests/performance/`
  - `test_coreml_performance.py`: Validates <100ms inference on real model
  - `test_llm_performance.py`: Validates <3s LLM response on real Ollama
  - `test_pipeline_throughput.py`: Measures events/minute processing rate
- Load testing: Not needed (single user, local deployment)

**Performance Baselines (M1 MacBook Pro):**
- CoreML inference (YOLOv8n): 65ms average, 85ms p95
- LLM inference (llava:7b): 2.1s average, 2.8s p95
- Frame processing (motion → event): 3.2s average
- Database insert: 5ms average
- API response (list 100 events): 32ms
- Memory usage: 1.2GB steady state
- CPU usage: 25% average, 60% during motion events

**Optimization Priorities:**
1. **Critical (NFR violations):** CoreML >100ms, LLM >3s, Storage >4GB
2. **High (Performance degradation):** Memory >2GB, CPU >80%, API >100ms
3. **Medium (User experience):** Frontend >1s page load, WebSocket >100ms latency
4. **Low (Nice to have):** Further inference optimization, thumbnail generation

---

# Testing Strategy

## Testing Pyramid

```
                    E2E Tests (5%)
                   /            \
                  /   Manual     \
                 /   Exploratory  \
                /                  \
           Integration Tests (25%)
          /                        \
         /    API Tests              \
        /    Database Tests           \
       /     Pipeline Tests            \
      /                                \
 Unit Tests (70%)
/    Core Logic                        \
     Platform Code
     Integrations
     Mocking External Dependencies
```

**Testing Distribution:**
- **Unit Tests (70%):** Fast, isolated tests with mocked dependencies
- **Integration Tests (25%):** Tests with real dependencies (database, file system, external services)
- **E2E Tests (5%):** Full workflow validation (Phase 3, manual for Phase 1/2)

**Rationale:**
- Heavy unit test coverage provides fast feedback loop (<10s execution)
- Integration tests validate component interactions without mocking
- E2E tests deferred to Phase 3 (manual testing sufficient for MVP)
- 70% unit test coverage meets ≥70% code coverage NFR requirement

---

## Test Organization

### Frontend Tests (Phase 2)

```
tests/frontend/
├── unit/
│   ├── test_state_manager.test.js       # State management logic
│   ├── test_api_client.test.js          # API client wrapper
│   ├── test_websocket_client.test.js    # WebSocket reconnection
│   └── test_date_formatter.test.js      # Utility functions
├── integration/
│   ├── test_component_rendering.test.js # Component DOM tests
│   └── test_api_integration.test.js     # Real API calls
└── e2e/
    ├── test_dashboard_workflow.spec.js  # Full user journey
    └── test_event_timeline.spec.js      # Timeline interactions
```

**Frontend Testing Tools (Phase 2):**
- Unit: Vitest or Jest (JavaScript testing framework)
- DOM testing: @testing-library/dom (vanilla JS component testing)
- E2E: Playwright (Phase 3)
- Coverage: c8 or Istanbul

**Not Implemented in Phase 1:**
- Frontend tests deferred to Phase 2 (no web UI in Phase 1)
- Manual testing of web dashboard sufficient for personal project

---

### Backend Tests

```
tests/
├── unit/
│   ├── test_motion_detector.py          # Motion detection algorithm
│   ├── test_event_manager.py            # Event creation and de-duplication
│   ├── test_database.py                 # DatabaseManager (mocked SQLite)
│   ├── test_storage_monitor.py          # Storage calculations
│   ├── test_log_rotation.py             # FIFO deletion logic
│   ├── test_metrics.py                  # Metrics collection
│   ├── test_json_logger.py              # JSON log writing
│   ├── test_plaintext_logger.py         # Plaintext log writing
│   └── test_config.py                   # Pydantic config validation
│
├── integration/
│   ├── test_database_integration.py     # Real SQLite operations
│   ├── test_rtsp_integration.py         # RTSP connection (mock camera)
│   ├── test_ollama_integration.py       # Ollama service calls
│   ├── test_pipeline_integration.py     # Full pipeline with test data
│   ├── test_api_integration.py          # FastAPI endpoints (Phase 2)
│   └── test_websocket_integration.py    # WebSocket streaming (Phase 2)
│
└── performance/
    ├── test_coreml_performance.py       # CoreML <100ms validation
    ├── test_llm_performance.py          # Ollama <3s validation
    ├── test_pipeline_throughput.py      # Events/minute throughput
    └── test_storage_growth.py           # Storage limit enforcement
```

**Backend Testing Tools:**
- Test framework: pytest 7.4+
- Coverage: pytest-cov (target ≥70%)
- Mocking: pytest-mock, unittest.mock
- Fixtures: pytest fixtures for common test data
- Performance: pytest-benchmark (for performance tests)

---

## Test Examples

### Frontend Component Test (Phase 2)

```javascript
// tests/frontend/unit/test_event_card.test.js
import { describe, it, expect, vi } from 'vitest';
import { EventCard } from '../../../web/components/EventCard.js';

describe('EventCard Component', () => {
  const mockEvent = {
    event_id: 'evt_12345',
    timestamp: '2025-11-08T14:32:15Z',
    camera_id: 'front_door',
    motion_confidence: 0.87,
    detected_objects: [
      { label: 'person', confidence: 0.92, bbox: { x: 120, y: 50, width: 180, height: 320 } }
    ],
    llm_description: 'Person approaching front door',
    image_path: 'data/events/2025-11-08/evt_12345.jpg'
  };

  it('should render event card with correct content', () => {
    const onClick = vi.fn();
    const card = EventCard(mockEvent, onClick);

    expect(card.className).toBe('event-card');
    expect(card.textContent).toContain('Person approaching front door');
    expect(card.textContent).toContain('person (92%)');
  });

  it('should call onClick handler when clicked', () => {
    const onClick = vi.fn();
    const card = EventCard(mockEvent, onClick);

    card.click();

    expect(onClick).toHaveBeenCalledWith('evt_12345');
  });

  it('should render multiple detected objects', () => {
    const eventWithMultipleObjects = {
      ...mockEvent,
      detected_objects: [
        { label: 'person', confidence: 0.92, bbox: {} },
        { label: 'package', confidence: 0.87, bbox: {} }
      ]
    };

    const card = EventCard(eventWithMultipleObjects, vi.fn());

    expect(card.textContent).toContain('person (92%)');
    expect(card.textContent).toContain('package (87%)');
  });

  it('should lazy load images', () => {
    const card = EventCard(mockEvent, vi.fn());
    const img = card.querySelector('img');

    expect(img.getAttribute('loading')).toBe('lazy');
    expect(img.getAttribute('src')).toContain('/api/v1/events/evt_12345/image');
  });
});
```

---

### Backend API Test

```python
# tests/integration/test_api_integration.py
"""Integration tests for FastAPI endpoints (Phase 2)."""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from api.server import app
from core.database import DatabaseManager
from core.models import Event, DetectedObject, BoundingBox


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def db_with_events(tmp_path):
    """Create test database with sample events."""
    db_path = tmp_path / "test_events.db"
    db = DatabaseManager(str(db_path))
    db.init_database()

    # Insert test events
    for i in range(5):
        event = Event(
            event_id=f"evt_test_{i}",
            timestamp=datetime.utcnow() - timedelta(hours=i),
            camera_id="test_camera",
            motion_confidence=0.8 + (i * 0.01),
            detected_objects=[
                DetectedObject(
                    label="person",
                    confidence=0.9,
                    bbox=BoundingBox(x=100, y=50, width=200, height=350)
                )
            ],
            llm_description=f"Test event {i}",
            image_path=f"data/test/evt_test_{i}.jpg",
            json_log_path="data/test/events.json"
        )
        db.insert_event(event)

    return db


def test_health_check(client):
    """Test health check endpoint returns 200."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data


def test_list_events_default(client, db_with_events):
    """Test listing events with default parameters."""
    response = client.get("/api/v1/events")

    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "total" in data
    assert len(data["events"]) == 5
    assert data["total"] == 5


def test_list_events_with_limit(client, db_with_events):
    """Test pagination with limit parameter."""
    response = client.get("/api/v1/events?limit=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data["events"]) == 2
    assert data["limit"] == 2


def test_list_events_with_time_range(client, db_with_events):
    """Test filtering events by time range."""
    start = (datetime.utcnow() - timedelta(hours=3)).isoformat()
    end = (datetime.utcnow() - timedelta(hours=1)).isoformat()

    response = client.get(f"/api/v1/events?start={start}&end={end}")

    assert response.status_code == 200
    data = response.json()
    assert len(data["events"]) >= 1  # At least one event in range


def test_get_event_by_id(client, db_with_events):
    """Test retrieving single event by ID."""
    response = client.get("/api/v1/events/evt_test_0")

    assert response.status_code == 200
    event = response.json()
    assert event["event_id"] == "evt_test_0"
    assert event["llm_description"] == "Test event 0"
    assert len(event["detected_objects"]) == 1


def test_get_event_by_id_not_found(client, db_with_events):
    """Test 404 error for non-existent event."""
    response = client.get("/api/v1/events/evt_nonexistent")

    assert response.status_code == 404
    error = response.json()
    assert "detail" in error
    assert error["detail"] == "Event not found"


def test_get_metrics(client):
    """Test metrics endpoint returns valid data."""
    response = client.get("/api/v1/metrics")

    assert response.status_code == 200
    metrics = response.json()
    assert "frames_processed" in metrics
    assert "events_created" in metrics
    assert "coreml_inference_avg" in metrics


def test_cors_headers(client):
    """Test CORS headers are set correctly."""
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:3000"}
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
```

---

### E2E Test (Phase 3)

```javascript
// tests/e2e/test_dashboard_workflow.spec.js
import { test, expect } from '@playwright/test';

test.describe('Dashboard Workflow', () => {
  test('should display recent events on dashboard', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Wait for events to load
    await page.waitForSelector('.event-card');

    // Check that events are displayed
    const eventCards = await page.locator('.event-card').count();
    expect(eventCards).toBeGreaterThan(0);

    // Verify event card contains expected elements
    const firstCard = page.locator('.event-card').first();
    await expect(firstCard.locator('.event-card__description')).toBeVisible();
    await expect(firstCard.locator('.event-card__image img')).toBeVisible();
  });

  test('should filter events by date range', async ({ page }) => {
    await page.goto('http://localhost:3000/#/events');

    // Open filter bar
    await page.click('#filter-toggle');

    // Set date range
    await page.fill('#filter-start', '2025-11-01');
    await page.fill('#filter-end', '2025-11-08');
    await page.click('button[type="submit"]');

    // Wait for filtered results
    await page.waitForSelector('.event-card');

    // Verify results are within date range
    const firstEventTime = await page.locator('.event-card__time').first().textContent();
    expect(firstEventTime).toContain('Nov');
  });

  test('should navigate to event detail', async ({ page }) => {
    await page.goto('http://localhost:3000/#/events');

    // Click on first event card
    await page.click('.event-card:first-child');

    // Wait for detail view
    await page.waitForURL(/.*#\/event\/.*/);

    // Verify detail view elements
    await expect(page.locator('.event-detail__image')).toBeVisible();
    await expect(page.locator('.event-detail__description')).toBeVisible();
    await expect(page.locator('.event-detail__metadata')).toBeVisible();
  });

  test('should receive real-time event updates via WebSocket', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Wait for WebSocket connection
    await page.waitForTimeout(1000);

    // Simulate new event (would require triggering actual event in test environment)
    // This is a placeholder - actual implementation would need test event generator

    // Verify notification appears
    // await expect(page.locator('.notification')).toBeVisible();
    // await expect(page.locator('.notification')).toContainText('New event');
  });
});
```

---

## Unit Test Best Practices

**1. Use pytest fixtures for common test data:**

```python
# tests/conftest.py
"""Shared pytest fixtures for all tests."""
import pytest
from datetime import datetime
from core.models import Event, DetectedObject, BoundingBox


@pytest.fixture
def sample_event():
    """Create sample Event object for testing."""
    return Event(
        event_id="evt_test_12345",
        timestamp=datetime.utcnow(),
        camera_id="test_camera",
        motion_confidence=0.87,
        detected_objects=[
            DetectedObject(
                label="person",
                confidence=0.92,
                bbox=BoundingBox(x=120, y=50, width=180, height=320)
            )
        ],
        llm_description="Test person approaching",
        image_path="data/test/evt_test_12345.jpg",
        json_log_path="data/test/events.json"
    )


@pytest.fixture
def mock_frame():
    """Create mock OpenCV frame (numpy array)."""
    import numpy as np
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def temp_database(tmp_path):
    """Create temporary SQLite database for testing."""
    from core.database import DatabaseManager
    db_path = tmp_path / "test.db"
    db = DatabaseManager(str(db_path))
    db.init_database()
    return db
```

**2. Mock external dependencies:**

```python
# tests/unit/test_event_manager.py
"""Unit tests for EventManager."""
import pytest
from unittest.mock import Mock, patch
from core.event_manager import EventManager


def test_create_event_success(sample_event, mock_frame):
    """Test event creation with valid inputs."""
    # Mock dependencies
    mock_db = Mock()
    mock_json_logger = Mock()
    mock_txt_logger = Mock()

    event_manager = EventManager(
        db_manager=mock_db,
        json_logger=mock_json_logger,
        txt_logger=mock_txt_logger
    )

    # Create event
    event = event_manager.create_event(
        frame=mock_frame,
        objects=sample_event.detected_objects,
        description=sample_event.llm_description,
        motion_confidence=0.87
    )

    # Verify event created
    assert event is not None
    assert event.llm_description == sample_event.llm_description

    # Verify persistence methods called
    mock_db.insert_event.assert_called_once()
    mock_json_logger.log_event.assert_called_once()
    mock_txt_logger.log_event.assert_called_once()


def test_event_suppression(sample_event):
    """Test event de-duplication logic."""
    event_manager = EventManager(
        db_manager=Mock(),
        json_logger=Mock(),
        txt_logger=Mock()
    )

    # Create first event
    event1 = event_manager.create_event(
        frame=Mock(),
        objects=sample_event.detected_objects,
        description="Person detected",
        motion_confidence=0.87
    )
    assert event1 is not None

    # Create duplicate event (same objects)
    event2 = event_manager.create_event(
        frame=Mock(),
        objects=sample_event.detected_objects,
        description="Person detected again",
        motion_confidence=0.88
    )
    assert event2 is None  # Suppressed due to overlap
```

**3. Test edge cases and error conditions:**

```python
# tests/unit/test_storage_monitor.py
"""Unit tests for StorageMonitor."""
import pytest
from core.storage_monitor import StorageMonitor


def test_storage_within_limit(tmp_path):
    """Test storage check when under limit."""
    monitor = StorageMonitor(max_storage_gb=1.0)
    stats = monitor.check_usage()

    assert stats.is_over_limit is False
    assert 0 <= stats.percentage_used <= 100


def test_storage_over_limit(tmp_path):
    """Test storage check when over limit."""
    # Create large file to exceed limit
    large_file = tmp_path / "data/events/large.dat"
    large_file.parent.mkdir(parents=True, exist_ok=True)

    # Write 1.1GB file (exceeds 1GB limit)
    with open(large_file, 'wb') as f:
        f.write(b'0' * (1100 * 1024 * 1024))

    monitor = StorageMonitor(max_storage_gb=1.0, data_dir=str(tmp_path / "data"))
    stats = monitor.check_usage()

    assert stats.is_over_limit is True
    assert stats.percentage_used > 100


def test_storage_calculation_empty_directory(tmp_path):
    """Test storage calculation with empty directory."""
    monitor = StorageMonitor(max_storage_gb=1.0, data_dir=str(tmp_path))
    stats = monitor.check_usage()

    assert stats.total_bytes == 0
    assert stats.percentage_used == 0.0
```

**4. Parametrize tests for multiple scenarios:**

```python
# tests/unit/test_motion_detector.py
"""Unit tests for MotionDetector."""
import pytest
import numpy as np
from core.motion_detector import MotionDetector


@pytest.mark.parametrize("threshold,expected_motion", [
    (0.1, True),   # Low threshold, should detect motion
    (0.5, True),   # Medium threshold, should detect motion
    (0.9, False),  # High threshold, might not detect motion
])
def test_motion_detection_thresholds(threshold, expected_motion, mock_frame):
    """Test motion detection with different thresholds."""
    detector = MotionDetector(motion_threshold=threshold)

    # Build background model
    for _ in range(100):
        detector.detect_motion(mock_frame)

    # Create frame with slight change
    changed_frame = mock_frame.copy()
    changed_frame[100:200, 100:200] = 255  # White square

    has_motion, confidence = detector.detect_motion(changed_frame)

    assert isinstance(has_motion, bool)
    assert 0.0 <= confidence <= 1.0
```

---

## Integration Test Strategy

**Database Integration Tests:**
- Use real SQLite database in temp directory
- Test schema creation, migrations, CRUD operations
- Verify indexes are created correctly
- Test concurrent reads (multiple queries simultaneously)

**RTSP Integration Tests:**
- Mock RTSP camera using test video file
- Test connection establishment and reconnection logic
- Validate frame capture and timeout handling
- Skip if no test camera available (pytest.mark.skipif)

**Ollama Integration Tests:**
- Require Ollama service running locally
- Use smaller model (moondream) for faster tests
- Test health check, model availability, inference
- Skip if Ollama not available (pytest.mark.skipif)

**Pipeline Integration Tests:**
- Use test video file instead of live camera
- Mock CoreML with fast detector (returns predefined objects)
- Use real database, loggers, storage monitor
- Verify events created and persisted correctly

---

## Performance Test Examples

```python
# tests/performance/test_coreml_performance.py
"""Performance tests for CoreML inference (NFR validation)."""
import pytest
import numpy as np
import time
from platform.coreml_detector import CoreMLObjectDetector


@pytest.mark.performance
def test_coreml_inference_speed():
    """Validate CoreML inference meets <100ms NFR target."""
    detector = CoreMLObjectDetector("models/yolov8n.mlmodel")
    assert detector.is_model_loaded()

    # Create test frame (640x640 RGB)
    test_frame = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

    # Warm-up inference (first run is slower)
    detector.detect_objects(test_frame)

    # Measure inference time over 100 runs
    inference_times = []
    for _ in range(100):
        start = time.perf_counter()
        objects = detector.detect_objects(test_frame)
        end = time.perf_counter()
        inference_times.append((end - start) * 1000)  # Convert to ms

    # Calculate percentiles
    p50 = np.percentile(inference_times, 50)
    p95 = np.percentile(inference_times, 95)
    p99 = np.percentile(inference_times, 99)

    print(f"\nCoreML Inference Times:")
    print(f"  p50: {p50:.2f}ms")
    print(f"  p95: {p95:.2f}ms")
    print(f"  p99: {p99:.2f}ms")

    # Validate NFR: p95 should be <100ms
    assert p95 < 100.0, f"CoreML p95 inference time {p95:.2f}ms exceeds 100ms target"


@pytest.mark.performance
@pytest.mark.skipif(not ollama_available(), reason="Ollama service not running")
def test_llm_inference_speed():
    """Validate Ollama LLM inference meets <3s NFR target."""
    from integrations.ollama_client import OllamaLLMProcessor

    llm = OllamaLLMProcessor("http://localhost:11434", "llava:7b")
    assert llm.health_check()

    # Create test image and objects
    test_frame = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    test_objects = [
        DetectedObject(label="person", confidence=0.9, bbox=BoundingBox(x=0, y=0, width=100, height=200))
    ]

    # Measure LLM inference time over 10 runs
    inference_times = []
    for _ in range(10):
        start = time.perf_counter()
        description = llm.generate_description(test_frame, test_objects)
        end = time.perf_counter()
        inference_times.append(end - start)

    # Calculate percentiles
    p50 = np.percentile(inference_times, 50)
    p95 = np.percentile(inference_times, 95)

    print(f"\nLLM Inference Times:")
    print(f"  p50: {p50:.2f}s")
    print(f"  p95: {p95:.2f}s")

    # Validate NFR: p95 should be <3s
    assert p95 < 3.0, f"LLM p95 inference time {p95:.2f}s exceeds 3s target"
```

---

## Test Coverage Requirements

**Coverage Target:** ≥70% code coverage (NFR requirement)

**Coverage by Module:**
- `core/`: ≥80% (critical business logic)
- `platform/`: ≥70% (CoreML integration)
- `integrations/`: ≥60% (external service clients, harder to test)
- `api/`: ≥75% (FastAPI endpoints, Phase 2)

**Excluded from Coverage:**
- `main.py`: Entry point, tested manually
- `scripts/`: Utility scripts, not production code
- Test files themselves

**Coverage Reporting:**
```bash
# Generate HTML coverage report
pytest --cov=core --cov=platform --cov=integrations --cov-report=html

# View report
open htmlcov/index.html

# Fail CI if coverage below 70%
pytest --cov --cov-fail-under=70
```

---

## Testing CI/CD Integration

**GitHub Actions Test Workflow:**
- Run on every push and pull request
- Separate jobs for unit, integration, and performance tests
- Unit tests must pass for PR to merge
- Integration tests may be skipped if dependencies unavailable
- Performance tests run manually (too slow for CI)

**Local Pre-commit Testing:**
```bash
# Run before committing
pytest tests/unit -v              # Fast unit tests only
black --check core/ platform/     # Code formatting
ruff check core/ platform/        # Linting

# Full test suite before push
pytest tests/ -v --cov            # All tests with coverage
```

---

# Coding Standards

## Critical Fullstack Rules

These are **MANDATORY** rules that prevent common mistakes and ensure consistency across the codebase. All AI agents and developers must follow these rules.

- **Type Safety:** Use Pydantic models for all configuration and data entities. Never use raw dictionaries for structured data that crosses module boundaries.

- **Dependency Injection:** Components must receive dependencies through constructor parameters, never instantiate dependencies internally. This enables testing with mocks.

- **Error Handling:** All exceptions must be caught at module boundaries, logged with context, and either handled gracefully or re-raised with additional context. Never silently swallow exceptions.

- **Configuration Access:** Access configuration only through SystemConfig Pydantic model, never read environment variables directly with `os.getenv()` in application code.

- **Database Access:** All database operations must go through DatabaseManager methods. Never execute raw SQL queries outside the DatabaseManager class.

- **Logging Standards:** Use structured logging with consistent format: `logger.info(f"Event created: {event_id}", extra={"event_id": event_id})`. Include relevant context in log messages.

- **API Error Responses:** All API endpoints must use standard error format (see Error Handling section). Never return plain text error messages.

- **Resource Cleanup:** Always use context managers (`with` statements) for file operations, database connections, and external service clients. Never leave resources open after use.

- **Secrets in Logs:** Never log credentials, API keys, or RTSP URLs with passwords. Redact sensitive data: `rtsp://***:***@192.168.1.100:554/stream1`

- **Immutable Events:** Events are write-once, never modify after creation. No UPDATE statements on events table, only INSERT and SELECT.

- **Path Handling:** Use `pathlib.Path` for all file path operations, never string concatenation. Ensures cross-platform compatibility and prevents path injection.

- **Timezone Awareness:** All datetime objects must be timezone-aware (UTC). Use `datetime.utcnow()` and store with timezone info.

- **Import Organization:** Follow PEP 8 import order: standard library, third-party, local application. Use absolute imports, avoid relative imports outside of tests.

- **Frontend DOM Manipulation:** Use `textContent` for plain text, `innerHTML` only for trusted content. Always escape user-generated content before rendering.

- **Frontend API Calls:** All API calls must go through `services/apiClient.js`, never use `fetch()` directly in components. Centralizes error handling and request configuration.

---

## Naming Conventions

| Element | Frontend | Backend | Example |
|---------|----------|---------|---------|
| **Components** | PascalCase | - | `EventCard.js`, `EventTimeline.js` |
| **Hooks/Composables** | camelCase with prefix | - | `useAuth.js`, `useWebSocket.js` |
| **Services** | camelCase | - | `apiClient.js`, `websocketClient.js` |
| **Python Modules** | - | snake_case | `motion_detector.py`, `event_manager.py` |
| **Python Classes** | - | PascalCase | `MotionDetector`, `EventManager` |
| **Python Functions** | - | snake_case | `detect_motion()`, `create_event()` |
| **Python Constants** | - | UPPER_SNAKE_CASE | `MAX_STORAGE_GB`, `DEFAULT_THRESHOLD` |
| **API Routes** | - | kebab-case | `/api/v1/events`, `/api/v1/system-metrics` |
| **Database Tables** | - | snake_case | `events`, `schema_version` |
| **Database Columns** | - | snake_case | `event_id`, `motion_confidence` |
| **Environment Variables** | - | UPPER_SNAKE_CASE | `CAMERA_RTSP_URL`, `OLLAMA_MODEL` |
| **CSS Classes** | BEM: block__element--modifier | - | `.event-card`, `.event-card__image`, `.event-card--highlighted` |
| **Test Files** | `test_*.test.js` | `test_*.py` | `test_event_card.test.js`, `test_event_manager.py` |
| **Configuration Files** | lowercase | lowercase | `config.yaml`, `.env.example` |

**Rationale:**
- Follows community conventions for each language/framework
- PascalCase for classes/components makes them visually distinct
- snake_case for Python aligns with PEP 8
- BEM for CSS prevents naming conflicts in component-heavy UIs

---

## Python Code Style

### PEP 8 Compliance

Follow [PEP 8](https://peps.python.org/pep-0008/) with these specific requirements:

**Line Length:**
- Maximum 100 characters (not 79) for better readability on modern displays
- Configured in `.pyproject.toml`: `line-length = 100`

**Indentation:**
- 4 spaces per indentation level (never tabs)
- Hanging indents: 4 spaces for continuation lines

**Whitespace:**
- One blank line between methods in a class
- Two blank lines between top-level functions and classes
- No trailing whitespace on any lines

**Imports:**
```python
# Standard library imports
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Third-party imports
import numpy as np
from pydantic import BaseModel, Field

# Local application imports
from core.database import DatabaseManager
from core.models import Event, DetectedObject
```

**String Quotes:**
- Prefer double quotes `"` for strings (configured in Black)
- Use f-strings for formatting, not `.format()` or `%` operator
- Example: `logger.info(f"Event created: {event.event_id}")`

**Type Hints:**
```python
from typing import List, Optional, Tuple

def detect_motion(frame: np.ndarray) -> Tuple[bool, float]:
    """Detect motion in frame.

    Args:
        frame: OpenCV frame (numpy array)

    Returns:
        Tuple of (has_motion, confidence_score)
    """
    # Implementation
    return True, 0.87
```

**Docstrings:**
- Use Google style docstrings for all public functions and classes
- Include Args, Returns, Raises sections
- Example:
```python
def create_event(
    self,
    frame: np.ndarray,
    objects: List[DetectedObject],
    description: str,
    motion_confidence: float
) -> Optional[Event]:
    """Create event from processed frame data.

    Args:
        frame: OpenCV frame with detected objects
        objects: List of detected objects from CoreML
        description: Semantic description from LLM
        motion_confidence: Motion detection confidence score (0.0-1.0)

    Returns:
        Event object if created, None if suppressed by de-duplication

    Raises:
        ValueError: If motion_confidence not in range [0.0, 1.0]
    """
```

---

## JavaScript Code Style

### ES6+ Standards

Use modern JavaScript (ES6+) with these conventions:

**Module System:**
- Use ES6 modules (`import`/`export`), not CommonJS (`require`)
- Named exports for utilities, default export for main component
```javascript
// Good
export function EventCard(event, onClick) { ... }
export function formatTimestamp(timestamp) { ... }

// Also good for main component
export default function Dashboard() { ... }
```

**Variable Declaration:**
- Use `const` by default, `let` only when reassignment needed
- Never use `var`
```javascript
const event = { ... };  // Immutable reference
let counter = 0;        // Will be reassigned
```

**Arrow Functions:**
- Use arrow functions for callbacks and short functions
- Use regular functions for component factories (better stack traces)
```javascript
// Arrow for callbacks
events.map(event => EventCard(event, handleClick));

// Regular function for components
export function EventCard(event, onClick) {
  const card = document.createElement('div');
  // ...
}
```

**Template Literals:**
- Use template literals for string interpolation and multiline strings
```javascript
card.innerHTML = `
  <div class="event-card__header">
    <span>${event.camera_id}</span>
    <span>${formatTimestamp(event.timestamp)}</span>
  </div>
`;
```

**Object and Array Destructuring:**
```javascript
// Object destructuring
const { event_id, timestamp, llm_description } = event;

// Array destructuring
const [events, setEvents] = useState([]);
```

**Async/Await:**
- Prefer async/await over raw Promises
```javascript
// Good
async function fetchEvents() {
  try {
    const response = await fetch('/api/v1/events');
    const data = await response.json();
    return data.events;
  } catch (error) {
    console.error('Failed to fetch events:', error);
    throw error;
  }
}

// Avoid
function fetchEvents() {
  return fetch('/api/v1/events')
    .then(response => response.json())
    .then(data => data.events)
    .catch(error => console.error(error));
}
```

**No Semicolons:**
- Omit semicolons (consistent with modern JavaScript style guides)
- Exception: Required when line starts with `[` or `(`
```javascript
const events = []
const card = document.createElement('div')

// Exception
;[1, 2, 3].forEach(n => console.log(n))
```

---

## Code Organization Patterns

### Python Module Structure

**Standard module template:**
```python
"""Module description.

This module provides [brief description of functionality].
Example usage is in tests/unit/test_[module_name].py.
"""
import logging
from typing import List, Optional

from core.models import Event
from core.config import SystemConfig

logger = logging.getLogger(__name__)


class ComponentName:
    """Class description.

    Attributes:
        config: System configuration
        dependency: Injected dependency
    """

    def __init__(self, config: SystemConfig, dependency: DependencyType):
        """Initialize component with dependencies.

        Args:
            config: System configuration
            dependency: External dependency to inject
        """
        self.config = config
        self.dependency = dependency
        self._internal_state = None

    def public_method(self, param: str) -> bool:
        """Public method description.

        Args:
            param: Parameter description

        Returns:
            Success status
        """
        return self._private_method(param)

    def _private_method(self, param: str) -> bool:
        """Private method (leading underscore).

        Args:
            param: Parameter description

        Returns:
            Success status
        """
        # Implementation
        return True


# Module-level functions (if needed, prefer class methods)
def utility_function(value: int) -> int:
    """Utility function description."""
    return value * 2
```

### JavaScript Component Pattern

**Functional component template:**
```javascript
/**
 * EventCard component - Displays single event with thumbnail
 *
 * @param {Event} event - Event object from API
 * @param {Function} onClick - Click handler
 * @returns {HTMLElement} Rendered card element
 */
export function EventCard(event, onClick) {
  // Create container
  const card = document.createElement('div')
  card.className = 'event-card'

  // Render content
  card.innerHTML = `
    <div class="event-card__image">
      <img src="/api/v1/events/${event.event_id}/image"
           alt="${event.llm_description}"
           loading="lazy">
    </div>
    <div class="event-card__content">
      <h3>${event.llm_description}</h3>
      <p>${formatTimestamp(event.timestamp)}</p>
    </div>
  `

  // Attach event listeners
  card.addEventListener('click', () => onClick(event.event_id))

  return card
}

// Helper functions at bottom
function formatTimestamp(timestamp) {
  return new Date(timestamp).toLocaleString()
}
```

---

## Error Handling Standards

### Python Error Handling

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

### JavaScript Error Handling

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

## Comments and Documentation

### When to Comment

**DO comment:**
- Complex algorithms (e.g., motion detection, de-duplication logic)
- Non-obvious business rules (e.g., "80% overlap triggers suppression")
- Performance optimizations (e.g., "Skip frames to reduce CPU usage")
- Workarounds for bugs in third-party libraries
- Security considerations (e.g., "Redact credentials before logging")

**DON'T comment:**
- Self-explanatory code (good naming is better than comments)
- What the code does (docstrings cover this)
- Commented-out code (use version control instead)

**Good comments:**
```python
# De-duplication: Compare new event to last 5 events
# Suppress if object labels overlap ≥80%
# This prevents duplicate alerts for stationary objects
overlap_threshold = 0.8
recent_events = self._get_recent_events(limit=5)
```

**Bad comments:**
```python
# Create event
event = Event(...)

# Insert into database
db.insert_event(event)
```

### TODO Comments

Use TODO comments sparingly, only for planned enhancements:
```python
# TODO(Phase 3): Add multi-camera support - requires cameras table
# TODO: Optimize by caching recent events in memory (low priority)
```

Format: `TODO(context): Description`

---

## Git Commit Standards

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring (no behavior change)
- `test`: Add or update tests
- `docs`: Documentation changes
- `perf`: Performance improvements
- `style`: Code style changes (formatting, no logic change)
- `chore`: Build process, dependency updates

**Examples:**
```
feat(coreml): add YOLOv8 model support for object detection

Implement CoreMLObjectDetector class with YOLOv8n model.
Validates model runs on Apple Neural Engine for <100ms inference.

Closes #12
```

```
fix(pipeline): prevent crash when RTSP connection lost

Add reconnection logic with exponential backoff (1s, 2s, 4s, 8s).
Log warning on connection loss, error after 5 consecutive failures.

Fixes #23
```

```
test(database): add integration tests for SQLite migrations

Cover schema version tracking, migration application, and rollback.
```

---

## Linting and Formatting

### Python Tools

**Black (code formatter):**
```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ["py310"]
```

**Ruff (linter):**
```toml
# pyproject.toml
[tool.ruff]
line-length = 100
select = [
  "E",   # pycodestyle errors
  "F",   # pyflakes
  "W",   # pycodestyle warnings
  "I",   # isort (import sorting)
  "N",   # pep8-naming
  "UP",  # pyupgrade
]
ignore = [
  "E501",  # Line too long (handled by Black)
]
```

**Running linters:**
```bash
# Format code
black core/ platform/ integrations/ api/

# Check formatting (CI)
black --check core/ platform/ integrations/ api/

# Lint code
ruff check core/ platform/ integrations/ api/

# Fix auto-fixable issues
ruff check --fix core/
```

### JavaScript Tools (Phase 2)

**ESLint configuration:**
```json
{
  "env": {
    "browser": true,
    "es2021": true
  },
  "extends": "eslint:recommended",
  "parserOptions": {
    "ecmaVersion": 2021,
    "sourceType": "module"
  },
  "rules": {
    "no-console": "off",
    "no-unused-vars": "warn",
    "prefer-const": "error",
    "no-var": "error"
  }
}
```

**Prettier (code formatter):**
```json
{
  "semi": false,
  "singleQuote": true,
  "trailingComma": "es5",
  "printWidth": 100
}
```

---

# Error Handling Strategy

## Error Flow

### End-to-End Error Flow (Frontend → Backend → Frontend)

```mermaid
sequenceDiagram
    participant UI as Web Dashboard
    participant API as API Client
    participant Server as FastAPI Server
    participant DB as Database Manager
    participant Log as Logger

    UI->>API: fetchEvents()
    API->>Server: GET /api/v1/events

    alt Success Path
        Server->>DB: get_recent_events(limit=100)
        DB-->>Server: list[Event]
        Server-->>API: 200 OK + JSON data
        API-->>UI: events array
        UI->>UI: Render events
    end

    alt Client Error (400-499)
        Server->>Server: Validate request params
        Server->>Log: log.warning("Invalid limit parameter")
        Server-->>API: 400 Bad Request + Error JSON
        API->>API: Parse error response
        API-->>UI: throw APIError("Invalid parameters")
        UI->>UI: Display error toast
    end

    alt Server Error (500-599)
        Server->>DB: get_recent_events()
        DB-->>Server: DatabaseError (connection failed)
        Server->>Log: log.error("Database unavailable", exc_info=True)
        Server-->>API: 500 Internal Server Error + Error JSON
        API->>API: Parse error response
        API-->>UI: throw APIError("Server error")
        UI->>UI: Display error banner + retry button
    end

    alt Network Error
        API->>Server: GET /api/v1/events
        Note over API,Server: Network timeout or offline
        API->>API: catch network exception
        API-->>UI: throw APIError("Network error")
        UI->>UI: Display offline message
    end
```

---

## Error Response Format

### Standard API Error Response

All API error responses follow this consistent JSON structure:

```typescript
interface ApiError {
  error: {
    code: string;           // Machine-readable error code
    message: string;        // Human-readable error message
    details?: Record<string, any>;  // Optional additional context
    timestamp: string;      // ISO 8601 timestamp
    requestId: string;      // Unique request identifier for debugging
  };
}
```

**Example Error Responses:**

**400 Bad Request (Invalid Parameters):**
```json
{
  "error": {
    "code": "INVALID_PARAMETERS",
    "message": "Query parameter 'limit' must be between 1 and 1000",
    "details": {
      "parameter": "limit",
      "value": 5000,
      "constraint": "1 <= limit <= 1000"
    },
    "timestamp": "2025-11-08T14:32:15.123Z",
    "requestId": "req_abc123def456"
  }
}
```

**404 Not Found (Resource Not Found):**
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Event not found",
    "details": {
      "event_id": "evt_nonexistent",
      "resource_type": "Event"
    },
    "timestamp": "2025-11-08T14:32:15.123Z",
    "requestId": "req_xyz789ghi012"
  }
}
```

**500 Internal Server Error (Database Failure):**
```json
{
  "error": {
    "code": "DATABASE_ERROR",
    "message": "Failed to retrieve events from database",
    "details": {
      "operation": "get_recent_events",
      "retryable": true
    },
    "timestamp": "2025-11-08T14:32:15.123Z",
    "requestId": "req_mno345pqr678"
  }
}
```

**503 Service Unavailable (Dependency Failure):**
```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Ollama service is unavailable",
    "details": {
      "service": "ollama",
      "url": "http://localhost:11434",
      "retryAfter": 60
    },
    "timestamp": "2025-11-08T14:32:15.123Z",
    "requestId": "req_stu901vwx234"
  }
}
```

---

## Frontend Error Handling

### API Client Error Handler

```javascript
// services/apiClient.js
/**
 * Centralized API client with error handling
 */

const BASE_URL = 'http://localhost:8000/api/v1'

/**
 * Custom error class for API errors
 */
export class APIError extends Error {
  constructor(message, status, code, details, requestId) {
    super(message)
    this.name = 'APIError'
    this.status = status
    this.code = code
    this.details = details
    this.requestId = requestId
  }

  /**
   * Check if error is retryable
   */
  isRetryable() {
    return this.status >= 500 || this.status === 0
  }

  /**
   * Check if error is client-side
   */
  isClientError() {
    return this.status >= 400 && this.status < 500
  }
}

/**
 * Generic API request wrapper with error handling
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`
  const requestId = generateRequestId()

  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      'X-Request-ID': requestId
    }
  }

  try {
    const response = await fetch(url, { ...defaultOptions, ...options })

    // Success response
    if (response.ok) {
      const contentType = response.headers.get('content-type')
      if (contentType?.includes('application/json')) {
        return await response.json()
      } else if (contentType?.includes('image/')) {
        return await response.blob()
      } else {
        return await response.text()
      }
    }

    // Error response - parse error JSON
    let errorData
    try {
      errorData = await response.json()
    } catch {
      // Response body is not JSON
      errorData = {
        error: {
          code: 'UNKNOWN_ERROR',
          message: `HTTP ${response.status}: ${response.statusText}`,
          timestamp: new Date().toISOString(),
          requestId
        }
      }
    }

    throw new APIError(
      errorData.error.message,
      response.status,
      errorData.error.code,
      errorData.error.details,
      errorData.error.requestId
    )

  } catch (error) {
    // Network error or fetch failure
    if (error instanceof APIError) {
      throw error
    }

    // Network timeout, offline, or CORS error
    throw new APIError(
      'Network request failed. Please check your connection.',
      0,  // Status 0 indicates network error
      'NETWORK_ERROR',
      { originalError: error.message },
      requestId
    )
  }
}

/**
 * Generate unique request ID
 */
function generateRequestId() {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Exported API methods with retry logic
 */
export const api = {
  async events(filters = {}, retries = 2) {
    let lastError
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const params = new URLSearchParams(filters)
        return await apiRequest(`/events?${params}`)
      } catch (error) {
        lastError = error

        // Don't retry client errors (4xx)
        if (error.isClientError && error.isClientError()) {
          throw error
        }

        // Retry server errors with exponential backoff
        if (attempt < retries && error.isRetryable && error.isRetryable()) {
          const delay = Math.pow(2, attempt) * 1000
          console.log(`Request failed, retrying in ${delay}ms...`)
          await new Promise(resolve => setTimeout(resolve, delay))
          continue
        }
      }
    }
    throw lastError
  },

  async getEvent(eventId) {
    return await apiRequest(`/events/${eventId}`)
  },

  async getEventImage(eventId) {
    return await apiRequest(`/events/${eventId}/image`)
  },

  async health() {
    return await apiRequest('/health')
  },

  async metrics() {
    return await apiRequest('/metrics')
  }
}
```

### UI Error Display Component

```javascript
// components/ErrorBanner.js
/**
 * Error banner component for displaying API errors to users
 */
export function ErrorBanner(error, onRetry, onDismiss) {
  const banner = document.createElement('div')
  banner.className = 'error-banner'

  // Determine error severity and styling
  const severity = error.isClientError ? error.isClientError() ? 'warning' : 'error' : 'error'
  banner.classList.add(`error-banner--${severity}`)

  // User-friendly error message
  const userMessage = getUserFriendlyMessage(error)

  banner.innerHTML = `
    <div class="error-banner__content">
      <span class="error-banner__icon">${getErrorIcon(severity)}</span>
      <div class="error-banner__message">
        <strong>${userMessage}</strong>
        ${error.details ? `<p class="error-banner__details">${formatDetails(error.details)}</p>` : ''}
      </div>
      <div class="error-banner__actions">
        ${error.isRetryable && error.isRetryable() ?
          '<button class="btn btn--retry">Retry</button>' : ''}
        <button class="btn btn--dismiss">Dismiss</button>
      </div>
    </div>
  `

  // Attach event listeners
  if (error.isRetryable && error.isRetryable()) {
    banner.querySelector('.btn--retry').addEventListener('click', onRetry)
  }
  banner.querySelector('.btn--dismiss').addEventListener('click', () => {
    banner.remove()
    if (onDismiss) onDismiss()
  })

  return banner
}

/**
 * Convert technical error to user-friendly message
 */
function getUserFriendlyMessage(error) {
  const messages = {
    'NETWORK_ERROR': 'Unable to connect to the server. Please check your internet connection.',
    'DATABASE_ERROR': 'Database is temporarily unavailable. Please try again in a moment.',
    'RESOURCE_NOT_FOUND': 'The requested item could not be found.',
    'INVALID_PARAMETERS': 'Invalid request. Please check your input.',
    'SERVICE_UNAVAILABLE': 'Service is temporarily unavailable. Please try again later.',
    'UNKNOWN_ERROR': 'An unexpected error occurred. Please try again.'
  }

  return messages[error.code] || error.message || messages['UNKNOWN_ERROR']
}

/**
 * Get icon for error severity
 */
function getErrorIcon(severity) {
  const icons = {
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️'
  }
  return icons[severity] || icons['error']
}

/**
 * Format error details for display
 */
function formatDetails(details) {
  if (typeof details === 'string') return details
  return Object.entries(details)
    .map(([key, value]) => `${key}: ${value}`)
    .join(', ')
}
```

### Usage Example in Component

```javascript
// components/EventTimeline.js
import { api, APIError } from '../services/apiClient.js'
import { ErrorBanner } from './ErrorBanner.js'
import { appState } from '../services/stateManager.js'

export function EventTimeline() {
  const container = document.createElement('div')
  container.className = 'event-timeline'

  // Load events
  loadEvents(container)

  return container
}

async function loadEvents(container) {
  // Show loading state
  container.innerHTML = '<div class="loading">Loading events...</div>'

  try {
    const data = await api.events({ limit: 100 })
    appState.setState('events', data.events)
    renderEvents(container, data.events)

  } catch (error) {
    if (error instanceof APIError) {
      // Display error banner with retry
      const errorBanner = ErrorBanner(
        error,
        () => loadEvents(container),  // Retry callback
        () => container.innerHTML = '<p>Unable to load events</p>'
      )
      container.innerHTML = ''
      container.appendChild(errorBanner)

      // Log error for debugging
      console.error('Failed to load events:', {
        code: error.code,
        message: error.message,
        requestId: error.requestId,
        details: error.details
      })
    } else {
      // Unexpected error
      console.error('Unexpected error loading events:', error)
      container.innerHTML = '<div class="error">An unexpected error occurred</div>'
    }
  }
}

function renderEvents(container, events) {
  // Render event list
  container.innerHTML = ''
  events.forEach(event => {
    const card = EventCard(event, handleEventClick)
    container.appendChild(card)
  })
}
```

---

## Backend Error Handling

### FastAPI Error Handler

```python
# api/server.py
"""FastAPI server with centralized error handling."""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime
import logging
import traceback
import uuid

from core.exceptions import (
    VideoRecognitionError,
    DatabaseError,
    RTSPConnectionError,
    CoreMLInferenceError,
    OllamaServiceError
)

logger = logging.getLogger(__name__)
app = FastAPI()


# Standard error response model
class ErrorResponse:
    """Standard error response format."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        details: dict = None,
        request_id: str = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.request_id = request_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self):
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "timestamp": self.timestamp,
                "requestId": self.request_id
            }
        }


# Exception handlers

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors (invalid request parameters)."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    # Extract validation error details
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(
        f"Validation error: {errors}",
        extra={"request_id": request_id, "path": request.url.path}
    )

    error_response = ErrorResponse(
        code="INVALID_PARAMETERS",
        message="Request validation failed",
        status_code=400,
        details={"errors": errors},
        request_id=request_id
    )

    return JSONResponse(
        status_code=400,
        content=error_response.to_dict()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTPException (404, 403, etc.)."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    # Map status codes to error codes
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "RESOURCE_NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "RATE_LIMIT_EXCEEDED"
    }

    error_code = code_map.get(exc.status_code, "HTTP_ERROR")

    logger.warning(
        f"{exc.status_code} error: {exc.detail}",
        extra={"request_id": request_id, "path": request.url.path}
    )

    error_response = ErrorResponse(
        code=error_code,
        message=exc.detail,
        status_code=exc.status_code,
        details=getattr(exc, "details", {}),
        request_id=request_id
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.to_dict()
    )


@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    """Handle database-related errors."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    logger.error(
        f"Database error: {exc}",
        exc_info=True,
        extra={"request_id": request_id, "path": request.url.path}
    )

    error_response = ErrorResponse(
        code="DATABASE_ERROR",
        message="Failed to retrieve data from database",
        status_code=500,
        details={"retryable": True},
        request_id=request_id
    )

    return JSONResponse(
        status_code=500,
        content=error_response.to_dict()
    )


@app.exception_handler(OllamaServiceError)
async def ollama_error_handler(request: Request, exc: OllamaServiceError):
    """Handle Ollama LLM service errors."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    logger.error(
        f"Ollama service error: {exc}",
        exc_info=True,
        extra={"request_id": request_id}
    )

    error_response = ErrorResponse(
        code="SERVICE_UNAVAILABLE",
        message="LLM service is unavailable",
        status_code=503,
        details={
            "service": "ollama",
            "retryAfter": 60
        },
        request_id=request_id
    )

    return JSONResponse(
        status_code=503,
        content=error_response.to_dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unexpected errors."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    # Log full traceback for debugging
    logger.critical(
        f"Unexpected error: {exc}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )

    # Don't expose internal error details to client
    error_response = ErrorResponse(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please try again later.",
        status_code=500,
        details={
            "requestId": request_id  # Include for support/debugging
        },
        request_id=request_id
    )

    return JSONResponse(
        status_code=500,
        content=error_response.to_dict()
    )
```

### Raising HTTP Exceptions in Endpoints

```python
# api/endpoints.py
from fastapi import HTTPException
from core.database import DatabaseManager
from core.exceptions import DatabaseError

@app.get("/api/v1/events/{event_id}")
async def get_event(event_id: str, db: DatabaseManager = Depends(get_db)):
    """Get event by ID."""
    try:
        event = db.get_event_by_id(event_id)

        if event is None:
            # Resource not found - raise 404
            raise HTTPException(
                status_code=404,
                detail="Event not found",
                # Optional: Add custom details
                # details={"event_id": event_id, "resource_type": "Event"}
            )

        return event.model_dump()

    except DatabaseError as e:
        # Database error - will be caught by database_error_handler
        raise

    except Exception as e:
        # Unexpected error - will be caught by general_exception_handler
        logger.error(f"Error retrieving event {event_id}: {e}", exc_info=True)
        raise
```

### Custom Exception Raising in Business Logic

```python
# core/database.py
from core.exceptions import DatabaseError

class DatabaseManager:
    """Database manager with proper error handling."""

    def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """Get event by ID with error handling."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM events WHERE event_id = ?",
                (event_id,)
            )
            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_event(row)

        except sqlite3.Error as e:
            # Wrap SQLite error in custom exception
            logger.error(
                f"Database query failed: {e}",
                exc_info=True,
                extra={"event_id": event_id}
            )
            raise DatabaseError(f"Failed to retrieve event {event_id}") from e

        except Exception as e:
            # Unexpected error
            logger.critical(
                f"Unexpected error in get_event_by_id: {e}",
                exc_info=True
            )
            raise
```

---

## Error Logging Standards

### Structured Logging with Context

```python
# core/processing_pipeline.py
import logging

logger = logging.getLogger(__name__)

def process_frame(self, frame: np.ndarray) -> Optional[Event]:
    """Process frame with comprehensive error logging."""
    frame_id = f"frame_{int(time.time() * 1000)}"

    try:
        # Stage 1: Motion detection
        has_motion, confidence = self.motion_detector.detect_motion(frame)

        if not has_motion:
            logger.debug(
                f"No motion detected",
                extra={"frame_id": frame_id, "confidence": confidence}
            )
            return None

        # Stage 2: Object detection
        logger.info(
            f"Motion detected, running object detection",
            extra={"frame_id": frame_id, "motion_confidence": confidence}
        )

        objects = self.object_detector.detect_objects(frame)

        # ... rest of processing

    except CoreMLInferenceError as e:
        # Recoverable error - log and skip frame
        logger.error(
            f"CoreML inference failed, skipping frame",
            exc_info=True,
            extra={
                "frame_id": frame_id,
                "frame_shape": frame.shape,
                "error_type": type(e).__name__
            }
        )
        return None

    except Exception as e:
        # Unexpected error - log with full context
        logger.critical(
            f"Unexpected error in frame processing",
            exc_info=True,
            extra={
                "frame_id": frame_id,
                "frame_shape": frame.shape,
                "pipeline_stage": "unknown",
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        )
        raise
```

### Log Levels

- **DEBUG**: Detailed diagnostic information (motion detection results, frame counts)
- **INFO**: Normal operational messages (event created, pipeline started)
- **WARNING**: Recoverable issues (RTSP reconnection, storage approaching limit)
- **ERROR**: Errors that skip current operation (CoreML inference failed, LLM timeout)
- **CRITICAL**: Fatal errors requiring shutdown (database corruption, config invalid)

---

# Monitoring and Observability

## Monitoring Stack

**Frontend Monitoring (Phase 2):**
- **Tool:** Browser DevTools + Console Logging
- **Metrics Collected:** Page load time, API response times, JavaScript errors
- **Implementation:** Custom performance marks and console error tracking
- **Phase 3 Enhancement:** Consider Sentry or LogRocket for production error tracking

**Backend Monitoring:**
- **Tool:** Custom metrics collection to `logs/metrics.json`
- **Metrics Collected:** Frame processing rate, inference times, CPU/memory usage, event counts
- **Implementation:** MetricsCollector class with 60-second sampling interval
- **Storage:** JSON Lines format in `logs/metrics.json` (enables easy parsing and analysis)

**Error Tracking:**
- **Tool:** Python logging module with structured logging
- **Storage:** `logs/app.log` (rotating file handler, max 100MB, 5 backups)
- **Log Format:** `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- **Structured Data:** Extra fields via `logger.info(..., extra={...})`
- **Phase 3 Enhancement:** Consider centralized logging with Loki or ELK stack

**Performance Monitoring:**
- **Tool:** Custom timing instrumentation in processing pipeline
- **Metrics Tracked:** CoreML inference time (p50, p95, p99), LLM inference time, end-to-end latency
- **Validation:** Performance tests in `tests/performance/` validate NFR targets
- **Alerting:** Log WARNING if metrics exceed thresholds (CoreML >100ms, LLM >3s)

**System Resource Monitoring:**
- **Tool:** psutil library for CPU/memory monitoring
- **Metrics:** CPU usage (%), memory usage (MB), disk usage (GB)
- **Frequency:** Collected every 60 seconds, logged to metrics.json
- **Alerts:** Storage >80% logs WARNING, >100% triggers graceful shutdown

**Rationale:**
- Simple, file-based monitoring sufficient for Phase 1/2 (single user, local deployment)
- No external monitoring service needed (privacy-first, no cloud dependencies)
- JSON Lines format enables easy analysis with standard tools (jq, Python, spreadsheets)
- Phase 3 can add Prometheus + Grafana if needed for advanced dashboards

---

## Key Metrics

### Frontend Metrics (Phase 2)

**Core Web Vitals:**
- **LCP (Largest Contentful Paint):** <2.5s (time until main content is visible)
- **FID (First Input Delay):** <100ms (time until page is interactive)
- **CLS (Cumulative Layout Shift):** <0.1 (visual stability score)

**Application Metrics:**
- **Page Load Time:** Time from navigation to interactive (<500ms target)
- **API Response Time:** Time for API calls to complete (<100ms for event list)
- **WebSocket Latency:** Time from server send to client receive (<50ms)
- **JavaScript Errors:** Count of unhandled exceptions (target: 0)
- **API Error Rate:** Percentage of failed API calls (target: <1%)

**Collection Method:**
```javascript
// Performance measurement
performance.mark('events-fetch-start')
const events = await api.events()
performance.mark('events-fetch-end')
performance.measure('events-fetch', 'events-fetch-start', 'events-fetch-end')

const measure = performance.getEntriesByName('events-fetch')[0]
console.log(`Events fetch took ${measure.duration}ms`)
```

---

### Backend Metrics

**Processing Pipeline Metrics:**
- **frames_processed**: Total frames captured from RTSP stream
- **motion_detected**: Count of frames with motion (hit rate: motion/total)
- **events_created**: Total events generated (after filtering and de-duplication)
- **events_suppressed**: Count of events suppressed by de-duplication logic

**Performance Metrics:**
- **coreml_inference_time**: CoreML object detection time in ms (p50, p95, p99)
  - **Target:** p95 <100ms (NFR requirement)
- **llm_inference_time**: Ollama LLM inference time in seconds (p50, p95, p99)
  - **Target:** p95 <3s (NFR requirement)
- **frame_processing_latency**: End-to-end time from motion detection to event logged (ms)
  - **Target:** <5s average
- **db_write_time**: Database insert operation time (ms)
  - **Target:** <10ms average

**Resource Metrics:**
- **cpu_usage**: Current CPU usage percentage (0-100%)
  - **Target:** <50% sustained on M1
- **memory_usage_mb**: Current memory usage in MB
  - **Target:** <2GB
- **storage_usage_gb**: Total storage used by data/events directory
  - **Target:** <4GB (hard limit)
- **storage_percentage**: Percentage of max_storage_gb used
  - **Warning:** >80% (triggers log rotation)
  - **Critical:** >100% (triggers graceful shutdown)

**Availability Metrics:**
- **uptime_seconds**: Time since pipeline started
- **system_availability**: Uptime as percentage (target: >99% during 24/7 operation)
- **rtsp_connection_failures**: Count of RTSP reconnection attempts
- **ollama_failures**: Count of Ollama service unavailable errors

**Metrics Collection Example:**

```python
# core/metrics.py
from dataclasses import dataclass
from datetime import datetime
from typing import List
import numpy as np
import psutil
import time

@dataclass
class MetricsSnapshot:
    """Snapshot of system metrics at a point in time."""
    timestamp: datetime
    frames_processed: int
    motion_detected: int
    events_created: int
    events_suppressed: int
    coreml_inference_avg: float
    coreml_inference_p95: float
    llm_inference_avg: float
    llm_inference_p95: float
    cpu_usage: float
    memory_usage_mb: int
    storage_usage_gb: float
    uptime_seconds: int


class MetricsCollector:
    """Collects and logs system performance metrics."""

    def __init__(self, interval: int = 60):
        self.interval = interval
        self.start_time = time.time()

        # Counters
        self.frames_processed = 0
        self.motion_detected = 0
        self.events_created = 0
        self.events_suppressed = 0

        # Performance metrics (rolling window)
        self.coreml_times: List[float] = []
        self.llm_times: List[float] = []
        self.max_samples = 1000  # Keep last 1000 samples

    def record_inference_time(self, component: str, time_ms: float):
        """Record inference time for CoreML or LLM."""
        if component == "coreml":
            self.coreml_times.append(time_ms)
            if len(self.coreml_times) > self.max_samples:
                self.coreml_times.pop(0)
        elif component == "llm":
            self.llm_times.append(time_ms)
            if len(self.llm_times) > self.max_samples:
                self.llm_times.pop(0)

    def increment_counter(self, metric: str):
        """Increment a counter metric."""
        if metric == "frames_processed":
            self.frames_processed += 1
        elif metric == "motion_detected":
            self.motion_detected += 1
        elif metric == "events_created":
            self.events_created += 1
        elif metric == "events_suppressed":
            self.events_suppressed += 1

    def collect(self) -> MetricsSnapshot:
        """Collect current metrics snapshot."""
        # Calculate percentiles
        coreml_avg = np.mean(self.coreml_times) if self.coreml_times else 0.0
        coreml_p95 = np.percentile(self.coreml_times, 95) if self.coreml_times else 0.0
        llm_avg = np.mean(self.llm_times) if self.llm_times else 0.0
        llm_p95 = np.percentile(self.llm_times, 95) if self.llm_times else 0.0

        # Get system resources
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory_usage_mb = psutil.Process().memory_info().rss / (1024 * 1024)

        # Calculate storage usage
        storage_usage_gb = self._calculate_storage_usage()

        # Calculate uptime
        uptime_seconds = int(time.time() - self.start_time)

        return MetricsSnapshot(
            timestamp=datetime.utcnow(),
            frames_processed=self.frames_processed,
            motion_detected=self.motion_detected,
            events_created=self.events_created,
            events_suppressed=self.events_suppressed,
            coreml_inference_avg=coreml_avg,
            coreml_inference_p95=coreml_p95,
            llm_inference_avg=llm_avg,
            llm_inference_p95=llm_p95,
            cpu_usage=cpu_usage,
            memory_usage_mb=int(memory_usage_mb),
            storage_usage_gb=storage_usage_gb,
            uptime_seconds=uptime_seconds
        )

    def _calculate_storage_usage(self) -> float:
        """Calculate total storage usage in GB."""
        from pathlib import Path
        total_bytes = sum(
            f.stat().st_size
            for f in Path("data/events").rglob("*")
            if f.is_file()
        )
        return total_bytes / (1024 ** 3)  # Convert to GB
```

**Metrics Logging:**

```python
# Log metrics to JSON Lines file every 60 seconds
import json

def log_metrics(metrics: MetricsSnapshot):
    """Log metrics snapshot to metrics.json."""
    with open("logs/metrics.json", "a") as f:
        f.write(json.dumps({
            "timestamp": metrics.timestamp.isoformat(),
            "frames_processed": metrics.frames_processed,
            "motion_detected": metrics.motion_detected,
            "events_created": metrics.events_created,
            "events_suppressed": metrics.events_suppressed,
            "coreml_inference_avg": round(metrics.coreml_inference_avg, 2),
            "coreml_inference_p95": round(metrics.coreml_inference_p95, 2),
            "llm_inference_avg": round(metrics.llm_inference_avg, 2),
            "llm_inference_p95": round(metrics.llm_inference_p95, 2),
            "cpu_usage": round(metrics.cpu_usage, 1),
            "memory_usage_mb": metrics.memory_usage_mb,
            "storage_usage_gb": round(metrics.storage_usage_gb, 2),
            "uptime_seconds": metrics.uptime_seconds
        }) + "\n")
```

---

## Metrics Analysis

### Analyzing Metrics with Command-Line Tools

**View latest metrics:**
```bash
# View last 10 metrics snapshots
tail -n 10 logs/metrics.json | jq .

# Pretty-print latest snapshot
tail -n 1 logs/metrics.json | jq .
```

**Calculate averages over time:**
```bash
# Average CoreML inference time over last 100 snapshots
tail -n 100 logs/metrics.json | jq -s 'map(.coreml_inference_avg) | add / length'

# Average CPU usage
tail -n 100 logs/metrics.json | jq -s 'map(.cpu_usage) | add / length'
```

**Check for NFR violations:**
```bash
# Find snapshots where CoreML p95 exceeds 100ms
cat logs/metrics.json | jq 'select(.coreml_inference_p95 > 100)'

# Find snapshots where LLM p95 exceeds 3000ms
cat logs/metrics.json | jq 'select(.llm_inference_p95 > 3000)'

# Check storage approaching limit
cat logs/metrics.json | jq 'select(.storage_usage_gb > 3.2)' | tail -n 5
```

**Generate time-series data for plotting:**
```bash
# Extract timestamp and CPU usage for plotting
cat logs/metrics.json | jq -r '[.timestamp, .cpu_usage] | @csv' > cpu_usage.csv

# Extract inference times
cat logs/metrics.json | jq -r '[.timestamp, .coreml_inference_avg, .llm_inference_avg] | @csv' > inference_times.csv
```

### Python Analysis Script

```python
# scripts/analyze_metrics.py
"""Analyze metrics.json to generate performance report."""
import json
from pathlib import Path
from datetime import datetime, timedelta

def analyze_metrics(metrics_file="logs/metrics.json"):
    """Generate performance report from metrics."""
    metrics = []

    with open(metrics_file) as f:
        for line in f:
            metrics.append(json.loads(line))

    if not metrics:
        print("No metrics found")
        return

    # Get metrics from last 24 hours
    cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_metrics = [
        m for m in metrics
        if datetime.fromisoformat(m["timestamp"].replace("Z", "")) > cutoff
    ]

    # Calculate statistics
    print("=== Performance Report (Last 24 Hours) ===\n")

    print(f"Total Snapshots: {len(recent_metrics)}")
    print(f"Uptime: {recent_metrics[-1]['uptime_seconds'] // 3600} hours\n")

    # Processing stats
    total_frames = recent_metrics[-1]["frames_processed"]
    total_motion = recent_metrics[-1]["motion_detected"]
    total_events = recent_metrics[-1]["events_created"]

    print(f"Frames Processed: {total_frames:,}")
    print(f"Motion Detected: {total_motion:,} ({total_motion/total_frames*100:.1f}%)")
    print(f"Events Created: {total_events:,}\n")

    # Performance metrics
    avg_coreml = sum(m["coreml_inference_avg"] for m in recent_metrics) / len(recent_metrics)
    max_coreml_p95 = max(m["coreml_inference_p95"] for m in recent_metrics)

    avg_llm = sum(m["llm_inference_avg"] for m in recent_metrics) / len(recent_metrics)
    max_llm_p95 = max(m["llm_inference_p95"] for m in recent_metrics)

    print(f"CoreML Inference (avg): {avg_coreml:.1f}ms")
    print(f"CoreML Inference (max p95): {max_coreml_p95:.1f}ms {'❌ EXCEEDS TARGET' if max_coreml_p95 > 100 else '✅ MEETS TARGET'}")

    print(f"\nLLM Inference (avg): {avg_llm:.0f}ms")
    print(f"LLM Inference (max p95): {max_llm_p95:.0f}ms {'❌ EXCEEDS TARGET' if max_llm_p95 > 3000 else '✅ MEETS TARGET'}\n")

    # Resource usage
    avg_cpu = sum(m["cpu_usage"] for m in recent_metrics) / len(recent_metrics)
    max_cpu = max(m["cpu_usage"] for m in recent_metrics)
    avg_memory = sum(m["memory_usage_mb"] for m in recent_metrics) / len(recent_metrics)
    max_memory = max(m["memory_usage_mb"] for m in recent_metrics)

    print(f"CPU Usage (avg): {avg_cpu:.1f}%")
    print(f"CPU Usage (max): {max_cpu:.1f}%")
    print(f"Memory Usage (avg): {avg_memory:.0f}MB")
    print(f"Memory Usage (max): {max_memory:.0f}MB\n")

    # Storage
    current_storage = recent_metrics[-1]["storage_usage_gb"]
    print(f"Storage Usage: {current_storage:.2f}GB / 4.00GB ({current_storage/4*100:.1f}%)")

if __name__ == "__main__":
    analyze_metrics()
```

---

## Dashboard Visualization (Phase 3)

For Phase 3, consider adding Grafana dashboard for visual monitoring:

**Setup:**
1. Export metrics to Prometheus format (add `/metrics` endpoint)
2. Run Prometheus server locally to scrape metrics
3. Configure Grafana to visualize Prometheus data

**Key Dashboards:**
- **Processing Pipeline:** Frames processed, motion detection rate, events created
- **Performance:** CoreML/LLM inference times with NFR target lines
- **Resources:** CPU, memory, storage usage over time
- **Errors:** Error rates by type, recent error log tail

**Alternative:** Simple web dashboard in Phase 2 can display latest metrics from `logs/metrics.json` via API endpoint.

---

