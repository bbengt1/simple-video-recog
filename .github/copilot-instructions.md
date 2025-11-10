# AI Coding Assistant Instructions for Simple Video Recognition System

## Project Overview
This is a privacy-first, local-only video recognition system for Apple Silicon that processes RTSP camera streams using motion detection, CoreML object detection, and local Ollama LLM semantic understanding. All processing happens on-device with zero cloud dependencies.

## BMAD Method Integration
This project uses the BMAD (Make AI Do) method for AI-driven planning and development with specialized agents. The BMAD system is configured in `.bmad-core/` with agents for different roles:

- **`.bmad-core/agents/`**: Specialized agents (analyst, architect, dev, pm, po, qa, sm, ux-expert, bmad-master, bmad-orchestrator)
- **`.bmad-core/core-config.yaml`**: Project configuration for BMAD workflow
- **Development Workflow**: Follow BMAD planning → sharding → development cycle pattern
- **Agent Usage**: Use appropriate agents for tasks (@dev for implementation, @qa for testing, @architect for design)
- **Documentation Structure**: PRD in `docs/prd.md`, architecture in `docs/architecture.md`, sharded stories in `docs/stories/`

## Architecture Patterns
- **Pipeline Pattern**: Sequential processing through RTSP capture → motion detection → frame sampling → CoreML inference → LLM description → event persistence
- **Dependency Injection**: Components receive dependencies via constructor (e.g., `ProcessingPipeline(rtsp_client, motion_detector, frame_sampler, config)`)
- **Pydantic Validation**: All configuration and data models use Pydantic for type safety and validation
- **Structured Logging**: Use `core.logging_config.get_logger(__name__)` for consistent ISO 8601 timestamps and module names
- **Repository Pattern**: DatabaseManager abstracts SQLite operations behind clean interface
- **Observer Pattern**: Custom state management for frontend (Phase 2) with Observer pattern

## Critical Developer Workflows

### Testing
```bash
# Run all tests with coverage
pytest --cov=core --cov=integrations --cov-report=term -v

# Run specific test categories
pytest tests/unit/test_config.py -v
pytest tests/integration -v

# Generate HTML coverage report
pytest --cov=core --cov=integrations --cov-report=html
open htmlcov/index.html
```

### Code Quality
- Format with `black` (100 char line length) and lint with `ruff`
- Target 70%+ test coverage across core modules
- Use type hints and comprehensive docstrings
- Follow Google-style docstrings

### Testing Patterns
```bash
# Run specific test categories
pytest tests/unit/test_config.py -v                    # Unit tests for config validation
pytest tests/integration/test_pipeline.py -v          # Integration tests for full pipeline
pytest tests/unit/test_coreml_detector.py -v          # CoreML inference tests

# Run with coverage for specific modules
pytest --cov=core.config --cov=core.events -v

# Run performance tests
pytest tests/performance/ -v --tb=short
```

### Development Commands
```bash
# Quick validation without running full pipeline
python main.py --dry-run --config config/config.yaml

# Debug mode with verbose logging
python main.py --config config/config.yaml --log-level DEBUG

# Override config values from command line
python main.py --config config/config.yaml --motion-threshold 0.3 --frame-sample-rate 10
```

### Local Development Setup
```bash
# Install Ollama and pull vision model
brew install ollama
ollama serve
ollama pull llava:7b

# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configure CoreML model path in config.yaml
coreml_model_path: "models/yolov8n.mlmodel"
```

## Project-Specific Conventions

### Configuration Management
- Use `SystemConfig` Pydantic model for all settings with field validation
- Load via `load_config(config_path)` with YAML validation
- Example: `config = load_config("config/config.yaml")`
- Override config with command-line args in `main.py`

### Error Handling
- Custom exceptions: `RTSPConnectionError`, `CoreMLLoadError`, `VideoRecognitionError`, `OllamaConnectionError`
- Graceful degradation: Log errors but continue processing
- RTSP reconnection with exponential backoff (1s, 2s, 4s, 8s max)
- Health checks before startup in `HealthChecker`

### Data Models
```python
# Use Pydantic BaseModel for all data structures
class DetectedObject(BaseModel):
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: BoundingBox

# JSON serialization with .model_dump_json()
event_json = event.model_dump_json(indent=2)

# Event IDs use timestamp + random suffix
event_id = f"evt_{int(time.time() * 1000)}_{secrets.token_hex(2)}"
```

### Performance Optimization
- Frame sampling reduces processing load (default: every 5th frame during motion)
- CoreML targets <100ms inference on Neural Engine with ANE compatibility checking
- LLM timeout: 10 seconds with fallback descriptions
- Storage monitoring with configurable GB limits and retention policies
- Event deduplication prevents spam (30s default window)

### File Organization
- `core/`: Platform-independent business logic (config, models, pipeline, events)
- `apple_platform/`: Apple Silicon-specific implementations (CoreML detector)
- `integrations/`: External service clients (RTSP, Ollama)
- `tests/unit/`, `tests/integration/`: Comprehensive test organization
- `migrations/`: SQL migration scripts for database schema
- `config/`: YAML configuration files
- `data/`: Runtime data storage (events, database)
- `.bmad-core/`: BMAD method implementation (agents, tasks, workflows)
- `.bmad-core/agents/`: Specialized AI agents (dev, qa, architect, pm, etc.)
- `docs/prd.md`: Product requirements document
- `docs/architecture.md`: System architecture documentation
- `docs/stories/`: Sharded user stories from BMAD workflow

### Module-Specific Patterns

**Core Modules (`core/`):**
- Business logic only, no platform-specific code
- Use dependency injection for all external dependencies
- Include comprehensive type hints and docstrings
- Follow repository pattern for data access

**Platform Modules (`apple_platform/`):**
- Apple Silicon and macOS-specific implementations
- Abstract interfaces defined in `core/`
- CoreML and Metal-specific optimizations
- Hardware compatibility validation

**Integration Modules (`integrations/`):**
- External service clients (RTSP, Ollama, etc.)
- Error handling with exponential backoff
- Connection pooling and health checks
- Mock implementations for testing

**Test Organization:**
- `tests/unit/`: Individual component tests with mocks
- `tests/integration/`: End-to-end pipeline tests
- `tests/performance/`: Benchmarking and NFR validation
- Mirror source structure (e.g., `tests/unit/test_config.py`)

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

### Event Creation and Deduplication
```python
# Generate unique event IDs with millisecond precision
event_id = Event.generate_event_id()

# Create with all metadata
event = Event(
    event_id=event_id,
    timestamp=datetime.now(timezone.utc),
    camera_id=config.camera_id,
    detected_objects=detections.objects,
    llm_description=description
)

# Check deduplication before creating
if not event_deduplicator.should_create_event(detections):
    # Suppress duplicate events
```

### Database Operations
```python
# Use DatabaseManager for SQLite operations
db = DatabaseManager(config.db_path)
db.init_database()  # Applies migrations automatically

# Atomic event insertion
with db.conn:
    db.insert_event(event)
```

### Signal Handling and Graceful Shutdown
```python
# Handle SIGINT/SIGTERM for graceful shutdown
import signal

shutdown_requested = False

def signal_handler(signum, frame):
    global shutdown_requested
    logger.info("Shutdown signal received, stopping processing...")
    shutdown_requested = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

### Health Checks and Startup Validation
```python
# Comprehensive startup validation
def perform_health_checks(config: SystemConfig) -> bool:
    checks = [
        ("Configuration", validate_config(config)),
        ("CoreML Model", validate_coreml_model(config.coreml_model_path)),
        ("Ollama Service", check_ollama_service(config.ollama_base_url)),
        ("RTSP Camera", test_rtsp_connection(config.camera_rtsp_url)),
        ("Storage", check_storage_limits(config.max_storage_gb)),
    ]

    all_passed = True
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        logger.info(f"[{status}] {check_name}")
        all_passed &= passed

    return all_passed
```

### Custom Exceptions
```python
# Use specific exception types for different failure modes
class RTSPConnectionError(Exception):
    """Failed to connect to RTSP camera stream."""

class CoreMLLoadError(Exception):
    """Failed to load or validate CoreML model."""

class VideoRecognitionError(Exception):
    """Generic video recognition processing error."""

class OllamaConnectionError(Exception):
    """Failed to connect to Ollama LLM service."""
```

## Integration Points

### RTSP Camera Integration
- **Client**: OpenCV VideoCapture with background thread capture and reconnection logic
- **Connection**: RTSP URL format: `rtsp://username:password@ip:port/stream`
- **Reconnection**: Exponential backoff (1s, 2s, 4s, 8s max) on connection failures
- **Error Handling**: RTSPConnectionError for network/camera issues
- **Frame Queue**: Max 100 frames to prevent memory overflow

### Ollama LLM Integration
- **API**: HTTP client to localhost:11434 with vision models (llava, moondream)
- **Timeout**: 10 seconds configurable via `llm_timeout`
- **Fallback**: Generic descriptions when LLM fails: "Detected: {object_labels}"
- **Error Handling**: OllamaConnectionError with retry logic
- **Prompt Template**: "Describe what is happening in this image. Focus on: {object_labels}"

### CoreML Model Integration
- **Format**: .mlmodel files optimized for Apple Neural Engine
- **Validation**: ANE compatibility checking at startup
- **Performance**: Target <100ms inference on M1/M2 hardware
- **Input**: RGB frames (convert from OpenCV BGR)
- **Error Handling**: CoreMLLoadError for model loading failures

### SQLite Database Integration
- **Schema**: Event storage with migrations in `migrations/` directory
- **Operations**: Repository pattern via DatabaseManager class
- **Transactions**: Atomic operations with context managers
- **Indexing**: Optimized for timestamp-based queries
- **Migrations**: Version-tracked schema updates

## Command-Line Interface
```bash
# Basic usage
python main.py config/config.yaml

# Dry-run validation
python main.py --config config.yaml --dry-run

# Override settings
python main.py --config config.yaml --log-level DEBUG --metrics-interval 30

# Show version
python main.py --version
```

## Enhanced IDE Development Workflow
- **Story Creation**: SM agent drafts stories from epics
- **Quality Gates**: QA agent provides risk assessment (*risk), test design (*design), and quality reviews (*review)
- **Implementation**: Dev agent executes stories with comprehensive testing
- **Iteration**: Address QA feedback and repeat cycle

Focus on privacy-first design, Apple Silicon optimization, and robust error recovery in all implementations.

## BMAD Development Workflow

### Agent Usage Patterns
- **@dev**: Code implementation, debugging, refactoring, and development best practices
- **@qa**: Test architecture, quality gates, risk assessment (*risk, *design, *trace, *review)
- **@architect**: System design, architecture decisions, and technical planning
- **@pm**: Product requirements, user stories, and project planning
- **@po**: Product ownership, backlog management, and story validation

### Development Cycle
1. **Planning Phase**: PRD → Architecture → Story Sharding (docs/stories/)
2. **Development Phase**: Story implementation with @dev agent
3. **Quality Phase**: @qa agent reviews with risk assessment and quality gates
4. **Iteration**: Address feedback and repeat cycle

### Documentation Structure
- **PRD**: `docs/prd.md` - Product requirements and features
- **Architecture**: `docs/architecture.md` - System design and technical decisions
- **Stories**: `docs/stories/` - Sharded user stories with acceptance criteria
- **QA Assessments**: `docs/qa/assessments/` - Risk profiles and test strategies
- **QA Gates**: `docs/qa/gates/` - Quality gate decisions

### Enhanced IDE Development Workflow
- **Story Creation**: SM agent drafts stories from epics
- **Quality Gates**: QA agent provides risk assessment (*risk), test design (*design), and quality reviews (*review)
- **Implementation**: Dev agent executes stories with comprehensive testing
- **Iteration**: Address QA feedback and repeat cycle

Focus on privacy-first design, Apple Silicon optimization, and robust error recovery in all implementations.