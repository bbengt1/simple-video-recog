# AI Coding Assistant Instructions for Simple Video Recognition System

## Project Overview
Privacy-first, local-only video recognition system for Apple Silicon processing RTSP streams via motion detection, CoreML object detection, and local Ollama LLM semantic understanding. Zero cloud dependencies, all processing on-device.

## Architecture Essentials
- **Pipeline Pattern**: RTSP capture → motion detection → frame sampling → CoreML inference → LLM description → event persistence → WebSocket broadcasting
- **Dependency Injection**: All components receive dependencies via constructor injection (see `ProcessingPipeline.__init__`)
- **Pydantic Models**: Type-safe configuration and data models with validation (see `core/models.py`, `core/config.py`)
- **Structured Logging**: `core.logging_config.get_logger(__name__)` for ISO 8601 timestamps with configurable levels
- **Repository Pattern**: DatabaseManager abstracts SQLite operations with atomic transactions
- **Web Dashboard**: FastAPI server with WebSocket real-time updates and static file serving
- **Split-Screen UI**: Real-time metrics display with curses-based terminal interface

## Critical Developer Workflows

### Testing & Validation
```bash
# Comprehensive validation without processing (startup health checks only)
python main.py --dry-run --config config/config.yaml

# Run all tests with coverage (core + integrations + api)
pytest --cov=core --cov=integrations --cov=api --cov-report=term -v

# Generate HTML coverage report
pytest --cov=core --cov=integrations --cov-report=html
open htmlcov/index.html

# Run integration tests (RTSP, Ollama, database)
pytest tests/integration -v

# Test RTSP connectivity specifically
python main.py --test-rtsp --config config/config.yaml
```

### Development Commands
```bash
# Start system with split-screen UI (default - top: metrics, bottom: logs)
python main.py --config config/config.yaml

# Traditional console output (no split-screen)
python main.py --config config/config.yaml --no-split-screen

# Debug mode with verbose logging
python main.py --config config/config.yaml --log-level DEBUG

# Override config values (motion sensitivity, frame rate, etc.)
python main.py --config config/config.yaml --motion-threshold 0.3 --frame-sample-rate 10

# Start web dashboard (separate process)
python web_server.py
```

### Local Setup (Apple Silicon Required)
```bash
# Install Ollama and vision model
brew install ollama
ollama serve
ollama pull llava:7b

# Create conda environment (REQUIRED for CoreML on Apple Silicon)
conda create -n video-recog python=3.12 -y
conda activate video-recog

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Download CoreML model (place in models/ directory)
# Visit: https://developer.apple.com/machine-learning/models/
# Or: https://github.com/ultralytics/yolov8/releases (yolov8n.mlmodel)
```

**Critical:** Use conda instead of venv for CoreML support. Virtual environments cannot access the system CoreML framework required for Apple Silicon Neural Engine.

## Project-Specific Patterns

### Configuration Management
- Use `SystemConfig` Pydantic model with field validation and YAML loading
- Load via `load_config(config_path)` with comprehensive error messages
- Command-line overrides supported in `main.py` argument parser
- Hot reload via SIGHUP signal (reconnects RTSP/Ollama, reloads CoreML models)

### Error Handling & Exceptions
- Custom exceptions: `RTSPConnectionError`, `CoreMLLoadError`, `VideoRecognitionError`, `OllamaConnectionError`
- Graceful degradation: CoreML failures fall back to motion-only detection
- RTSP reconnection with exponential backoff (1s, 2s, 4s, 8s max)
- Health checks before startup via `HealthChecker` (validates all dependencies)

### Data Models & Event Creation
```python
# Pydantic BaseModel for all data structures
class DetectedObject(BaseModel):
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: BoundingBox

# Event IDs with timestamp + random suffix for uniqueness
event_id = f"evt_{int(time.time() * 1000)}_{secrets.token_hex(2)}"

# JSON serialization with proper indentation
event_json = event.model_dump_json(indent=2)

# Event persistence with image annotation
annotated_frame = image_annotator.annotate(frame, detections.objects)
cv2.imwrite(image_path, annotated_frame)
```

### Performance Optimizations
- Frame sampling reduces load (default: every 5th frame during motion)
- CoreML targets <100ms inference on Neural Engine with ANE compatibility validation
- LLM timeout: 10s with fallback: `"Detected: {', '.join(obj.label for obj in detections.objects)}"`
- Event deduplication prevents spam (30s default window, configurable)
- Storage monitoring with configurable GB limits and automatic cleanup
- Adaptive CPU-based rate limiting (reduces processing FPS when CPU >60%)

### Signal Handling & Lifecycle Management
- **SIGINT/SIGTERM**: Graceful shutdown with 10s timeout, session statistics logging
- **SIGHUP**: Hot reload configuration without restart (reconnects services, reloads models)
- **Exit Codes**: 0=success, 1=error, 2=config invalid, 3=storage full
- **Session Summary**: Runtime, frames processed, events created, storage used

### File Organization
- `core/`: Platform-independent business logic (config, models, pipeline, events, database)
- `apple_platform/`: Apple Silicon-specific implementations (CoreML detector, ANE optimization)
- `integrations/`: External service clients (RTSP via OpenCV, Ollama HTTP client)
- `api/`: FastAPI web server with WebSocket broadcasting and REST endpoints
- `tests/unit/`, `tests/integration/`: Comprehensive test suites with 70%+ coverage target
- `migrations/`: SQL schema migrations with version tracking
- `config/`: YAML configuration files with example templates
- `data/`: Runtime storage (events database, images, logs)
- `web/`: Static web assets for dashboard (HTML, CSS, JS)
- `.bmad-core/`: BMAD method agents and structured development workflow

## Integration Points

### RTSP Camera Integration
- OpenCV VideoCapture with background thread capture and frame queue (max 100 frames)
- URL format: `rtsp://username:password@ip:port/stream` (Hikvision, Reolink, etc.)
- Exponential backoff reconnection (1s, 2s, 4s, 8s max) with configurable attempts
- FFmpeg environment variables for RTSP over TCP and buffer optimization

### Ollama LLM Integration
- HTTP client to `localhost:11434` with vision models (llava:7b, moondream:latest)
- 10s timeout with structured fallback descriptions
- Prompt engineering: `"Describe what is happening in this image. Focus on: {object_labels}"`
- Base64 image encoding for vision API calls

### CoreML Model Integration
- .mlmodel files optimized for Apple Neural Engine (ANE compatibility required)
- Startup validation checks ANE support and warm-up inference timing
- RGB input preprocessing (convert from OpenCV BGR with `cv2.cvtColor`)
- Target <100ms inference on M1/M2/M3 hardware with fallback to CPU/GPU

### SQLite Database Integration
- Repository pattern via `DatabaseManager` with atomic transactions and context managers
- Timestamp-optimized indexing for event queries and multi-camera support
- Version-tracked migrations in `migrations/` directory
- Event persistence with JSON serialization of detected objects

### Web Dashboard Integration
- FastAPI server with automatic API documentation (`/docs`, `/redoc`)
- WebSocket broadcasting for real-time event notifications
- Static file serving for event images and web assets
- CORS middleware for local development access

## BMAD Method Development Workflow (REQUIRED)

This project uses the BMad Method for structured AI-driven development. **ALL AI agents must follow BMad Method guidelines and use the specified agents for their roles.**

### Essential BMad Files (Must Read)
- **`.bmad-core/user-guide.md`**: Complete BMad Method workflow and processes
- **`.bmad-core/core-config.yaml`**: Core configuration and devLoadAlwaysFiles
- **`.bmad-core/agents/`**: Agent definitions and role responsibilities
- **`.bmad-core/tasks/`**: Task definitions and execution guidelines
- **`.bmad-core/templates/`**: Document templates and schemas

### Agent Usage (REQUIRED)
```bash
# Use appropriate agents for each role
@pm    # Product Management - PRDs, epics, stories
@po    # Product Ownership - Story validation, acceptance criteria
@sm    # Story Management - Story drafting and refinement
@architect  # System Architecture - Technical design and patterns
@dev   # Development - Code implementation following BMad standards
@qa    # Quality Assurance - Risk assessment, test design, quality gates
```

### BMad Workflow Commands (REQUIRED)
```bash
# Planning Phase
@po Create PRD for {feature}           # Product requirements
@architect Create architecture        # System design
@po Shard documents                   # Break into stories

# Development Phase
@sm Draft story for {feature}         # Story creation
@qa *risk {story}                     # Risk assessment
@qa *design {story}                   # Test strategy
@dev Implement {story}                # Code implementation
@qa *review {story}                   # Quality assessment

# Quality Gates
@qa *gate {story}                     # Update gate status
```

### Document Structure (REQUIRED)
```
docs/
├── prd.md                    # Product Requirements Document
├── architecture.md           # System Architecture
├── stories/                  # Sharded user stories
├── epics/                    # Epic definitions
└── qa/
    ├── assessments/          # Risk profiles, test designs
    └── gates/               # Quality gate decisions
```

### Quality Standards (REQUIRED)
- **Risk Assessment**: Run `@qa *risk` before development
- **Test Design**: Run `@qa *design` before implementation
- **Quality Gates**: All stories must pass QA review
- **Documentation**: All decisions documented in appropriate folders

## Code Quality Standards
- Format with `black` (100 char line length) and lint with `ruff`
- Target 70%+ test coverage across core, integrations, and api modules
- Type hints and Google-style docstrings required
- Comprehensive error handling with custom exceptions
- ISO 8601 timestamps in all logging output

## BMAD Method Compliance (MANDATORY)

**ALL AI agents MUST abide by everything inside the `.bmad-core` folder.** This includes:

### Core Configuration
- **`.bmad-core/core-config.yaml`**: Defines document locations, versions, and devLoadAlwaysFiles
- **`.bmad-core/install-manifest.yaml`**: Installation and file integrity tracking
- **Dev Load Always Files**: Must always load and reference:
  - `docs/architecture/coding-standards.md`
  - `docs/architecture/tech-stack.md`
  - `docs/architecture/source-tree.md`

### Required Workflows
- **`.bmad-core/enhanced-ide-development-workflow.md`**: IDE-specific development process
- **`.bmad-core/working-in-the-brownfield.md`**: Brownfield development guidelines
- **`.bmad-core/user-guide.md`**: Complete BMad Method workflow and processes

### Agent Definitions (MANDATORY)
- **`.bmad-core/agents/`**: All agent role definitions and responsibilities
- **`.bmad-core/agent-teams/`**: Team configurations for different project types

### Quality Assurance Requirements
- **`.bmad-core/checklists/`**: All checklists must be followed
- **`.bmad-core/tasks/`**: Task definitions and execution guidelines
- **Risk Assessment**: Run `@qa *risk` before development
- **Test Design**: Run `@qa *design` before implementation
- **Quality Gates**: All stories must pass QA review

### Templates and Standards
- **`.bmad-core/templates/`**: All document templates must be used
- **`.bmad-core/data/`**: Reference data and frameworks
- **`.bmad-core/workflows/`**: Workflow definitions for different project types

### Critical Rules
1. **Never bypass BMad Method processes** - all development must follow BMad workflows
2. **Always load devLoadAlwaysFiles** before any development work
3. **Use appropriate agents** for each role (@pm, @po, @architect, @dev, @qa, etc.)
4. **Follow document structure** requirements from core-config.yaml
5. **Complete quality gates** before marking any work as done

**Violation of BMad Method guidelines will result in invalid development work.**

Focus on privacy-first design, Apple Silicon optimization, and robust error recovery with graceful degradation.
