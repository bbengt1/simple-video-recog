# AI Coding Assistant Instructions for Simple Video Recognition System

## Project Overview
This is a privacy-first, local-only video recognition system for Apple Silicon that processes RTSP camera streams using motion detection, CoreML object detection, and local Ollama LLM semantic understanding. All processing happens on-device with zero cloud dependencies.

## Architecture Patterns
- **Pipeline Pattern**: Sequential processing through RTSP capture → motion detection → frame sampling → CoreML inference → LLM description → event persistence
- **Dependency Injection**: Components receive dependencies via constructor (e.g., `ProcessingPipeline(rtsp_client, motion_detector, frame_sampler, config)`)
- **Pydantic Validation**: All configuration and data models use Pydantic for type safety and validation
- **Structured Logging**: Use `core.logging_config.get_logger(__name__)` for consistent JSON/plaintext logging

## Critical Developer Workflows

### Testing
```bash
# Run all tests with coverage
pytest --cov=core --cov=integrations --cov-report=term -v

# Run specific test categories
pytest tests/unit/test_config.py -v
pytest tests/integration -v
```

### Code Quality
- Format with `black` and lint with `ruff`
- Target 70%+ test coverage across core modules
- Use type hints and comprehensive docstrings

### Local Development Setup
```bash
# Install Ollama and pull vision model
brew install ollama
ollama serve
ollama pull llava:7b

# Configure CoreML model path in config.yaml
coreml_model_path: "models/yolov8n.mlmodel"
```

## Project-Specific Conventions

### Configuration Management
- Use `SystemConfig` Pydantic model for all settings
- Load via `load_config(config_path)` with YAML validation
- Example: `config = load_config("config/config.yaml")`

### Error Handling
- Custom exceptions: `RTSPConnectionError`, `CoreMLLoadError`, `VideoRecognitionError`
- Graceful degradation: Log errors but continue processing
- RTSP reconnection with exponential backoff (1s, 2s, 4s, 8s max)

### Data Models
```python
# Use Pydantic BaseModel for all data structures
class DetectedObject(BaseModel):
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: BoundingBox

# JSON serialization with .model_dump_json()
event_json = event.model_dump_json(indent=2)
```

### Performance Optimization
- Frame sampling reduces processing load (default: every 5th frame during motion)
- CoreML targets <100ms inference on Neural Engine
- LLM timeout: 10 seconds with fallback descriptions
- Storage monitoring with 4GB limit and FIFO rotation

### File Organization
- `core/`: Platform-independent business logic
- `apple_platform/`: Apple Silicon-specific implementations
- `integrations/`: External service clients (RTSP, Ollama)
- `tests/unit/`, `tests/integration/`: Comprehensive test organization
- `.bmad-core/`: MAD (Make AI Do) method implementation

## Common Patterns

### Component Initialization
```python
# Always inject dependencies, never create internally
def __init__(self, config: SystemConfig):
    self.config = config
    self.logger = get_logger(__name__)
```

### Frame Processing Loop
```python
while not shutdown_requested:
    frame = rtsp_client.get_frame()
    if frame is None:
        continue

    # Process frame through pipeline stages
    has_motion, confidence, mask = motion_detector.detect_motion(frame)
    if has_motion and frame_sampler.should_process(frame_count):
        # Run inference and create events
```

### Event Creation
```python
# Generate unique event IDs
event_id = f"evt_{int(time.time())}_{secrets.token_hex(2)}"

# Create with all metadata
event = Event(
    event_id=event_id,
    timestamp=datetime.utcnow(),
    camera_id=config.camera_id,
    detected_objects=objects,
    llm_description=description
)
```

## Integration Points
- **RTSP Cameras**: OpenCV VideoCapture with reconnection logic
- **Ollama LLM**: HTTP API at localhost:11434 with vision models
- **CoreML Models**: .mlmodel files optimized for Apple Neural Engine
- **SQLite Database**: Event storage with schema migrations

Focus on privacy-first design, Apple Silicon optimization, and robust error recovery in all implementations.