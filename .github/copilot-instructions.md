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

## Integration Points
- **RTSP Cameras**: OpenCV VideoCapture with background thread capture and reconnection logic
- **Ollama LLM**: HTTP API at localhost:11434 with vision models (llava, moondream)
- **CoreML Models**: .mlmodel files optimized for Apple Neural Engine with compatibility validation
- **SQLite Database**: Event storage with schema migrations and foreign key constraints

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