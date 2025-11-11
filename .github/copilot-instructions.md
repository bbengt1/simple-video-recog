# AI Coding Assistant Instructions for Simple Video Recognition System

## Project Overview
Privacy-first, local-only video recognition system for Apple Silicon processing RTSP streams via motion detection, CoreML object detection, and local Ollama LLM semantic understanding. Zero cloud dependencies, all processing on-device.

## Architecture Essentials
- **Pipeline Pattern**: RTSP capture → motion detection → frame sampling → CoreML inference → LLM description → event persistence
- **Dependency Injection**: All components receive dependencies via constructor injection
- **Pydantic Models**: Type-safe configuration and data models with validation
- **Structured Logging**: `core.logging_config.get_logger(__name__)` for ISO 8601 timestamps
- **Repository Pattern**: DatabaseManager abstracts SQLite operations

## Critical Developer Workflows

### Testing & Validation
```bash
# Comprehensive validation without processing
python main.py --dry-run --config config/config.yaml

# Run all tests with coverage
pytest --cov=core --cov=integrations --cov-report=term -v

# Generate HTML coverage report
pytest --cov=core --cov=integrations --cov-report=html
open htmlcov/index.html
```

### Development Commands
```bash
# Start system with config (split-screen UI enabled by default)
python main.py --config config/config.yaml

# Traditional console output (disable split-screen)
python main.py --config config/config.yaml --no-split-screen

# Debug mode with verbose logging
python main.py --config config/config.yaml --log-level DEBUG

# Override config values
python main.py --config config/config.yaml --motion-threshold 0.3
```

### Local Setup
```bash
# Install Ollama and vision model
brew install ollama
ollama serve
ollama pull llava:7b

# Create conda environment (required for CoreML on Apple Silicon)
conda create -n video-recog python=3.12 -y
conda activate video-recog

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

**Important:** Use conda instead of venv for CoreML support. Virtual environments cannot access the system CoreML framework required for Apple Silicon.

## Project-Specific Patterns

### Configuration Management
- Use `SystemConfig` Pydantic model with field validation
- Load via `load_config(config_path)` with YAML validation
- Command-line overrides supported in `main.py`

### Error Handling & Exceptions
- Custom exceptions: `RTSPConnectionError`, `CoreMLLoadError`, `VideoRecognitionError`, `OllamaConnectionError`
- Graceful degradation: Log errors but continue processing
- RTSP reconnection with exponential backoff (1s, 2s, 4s, 8s max)
- Health checks before startup via `HealthChecker`

### Data Models & Event Creation
```python
# Pydantic BaseModel for all data structures
class DetectedObject(BaseModel):
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: BoundingBox

# Event IDs with timestamp + random suffix
event_id = f"evt_{int(time.time() * 1000)}_{secrets.token_hex(2)}"

# JSON serialization
event_json = event.model_dump_json(indent=2)
```

### Performance Optimizations
- Frame sampling reduces load (default: every 5th frame during motion)
- CoreML targets <100ms inference on Neural Engine with ANE compatibility
- LLM timeout: 10s with fallback descriptions
- Event deduplication prevents spam (30s default window)
- Storage monitoring with configurable GB limits

### File Organization
- `core/`: Platform-independent business logic (config, models, pipeline, events)
- `apple_platform/`: Apple Silicon-specific implementations (CoreML detector)
- `integrations/`: External service clients (RTSP, Ollama)
- `tests/unit/`, `tests/integration/`: Comprehensive test suites
- `migrations/`: SQL schema migrations
- `config/`: YAML configuration files
- `data/`: Runtime storage (events, database)
- `.bmad-core/`: BMAD method agents and workflows

## Integration Points

### RTSP Camera
- OpenCV VideoCapture with background thread capture
- URL format: `rtsp://username:password@ip:port/stream`
- Exponential backoff reconnection (1s, 2s, 4s, 8s max)
- Frame queue max 100 to prevent memory overflow

### Ollama LLM
- HTTP client to localhost:11434 with vision models (llava, moondream)
- 10s timeout with fallback: "Detected: {object_labels}"
- Prompt: "Describe what is happening in this image. Focus on: {object_labels}"

### CoreML Models
- .mlmodel files optimized for Apple Neural Engine
- ANE compatibility validation at startup
- Target <100ms inference on M1/M2 hardware
- RGB input (convert from OpenCV BGR)

### SQLite Database
- Repository pattern via DatabaseManager
- Atomic transactions with context managers
- Timestamp-optimized indexing
- Version-tracked migrations in `migrations/`

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
- Target 70%+ test coverage across core modules
- Type hints and Google-style docstrings required
- Comprehensive error handling and logging

Focus on privacy-first design, Apple Silicon optimization, and robust error recovery.
