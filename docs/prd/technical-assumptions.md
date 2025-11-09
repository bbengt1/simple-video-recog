# Technical Assumptions

The following technical decisions guide the Architecture and constrain implementation choices. These assumptions are based on the project's goals (learning, privacy, M1 optimization) and constraints (zero budget, solo developer, local-only).

## Repository Structure

**Decision: Monorepo**

**Rationale:**
- **Simplicity:** Single repository simplifies solo developer workflow (one clone, one dependency install, one deploy)
- **Code Sharing:** Core logic, utilities, and types shared between CLI and future web dashboard without package management overhead
- **Atomic Changes:** Changes spanning processing engine + API can be committed together
- **Learning Goal:** Easier to understand entire system in one codebase for portfolio/learning purposes

**Structure:**
```
video-recognition/
├── core/               # Core processing logic (platform-independent)
│   ├── motion.py       # Motion detection
│   ├── events.py       # Event de-duplication, logging
│   ├── config.py       # Configuration validation
│   └── pipeline.py     # Processing pipeline orchestration
├── platform/           # Platform-specific code (M1/macOS)
│   ├── coreml_detector.py    # CoreML object detection
│   └── thermal.py            # M1 thermal monitoring
├── integrations/       # External service integrations
│   ├── rtsp.py         # RTSP camera client
│   └── ollama.py       # Ollama LLM client
├── api/                # FastAPI server (Phase 2)
│   ├── server.py       # API routes
│   └── websocket.py    # Real-time event streaming
├── web/                # Web dashboard frontend (Phase 2)
│   ├── index.html      # SPA entry point
│   └── app.js          # Frontend logic
├── config/             # Configuration schemas and examples
│   ├── config.example.yaml
│   └── schema.json     # JSON schema for validation
├── tests/              # Test suite
│   ├── unit/
│   ├── integration/
│   └── performance/
├── docs/               # Documentation
├── main.py             # CLI entry point
├── requirements.txt    # Python dependencies
└── README.md
```

**Future-Proofing:** Clear separation (core/, platform/, api/, web/) enables future multi-platform support without refactoring

---

## Service Architecture

**Decision: Monolith (MVP) → Modular Monolith (Phase 2) → Future Microservices (Phase 3+)**

**MVP Architecture:**
- **Single Python Process:** All components run in one process
- **Threaded RTSP Capture:** Dedicated thread for continuous frame capture
- **Sequential Processing:** Motion detection → CoreML → LLM in main thread (simplicity over parallelism)
- **Shared Memory:** Frame queue in-memory (max 100 frames per NFR27)

**Rationale for MVP:**
- Solo developer maintainability
- Simpler debugging (single process, no IPC)
- Sufficient performance for single camera (motion-triggered processing reduces load)
- Faster MVP delivery

**Phase 2 Architecture (Modular Monolith):**
- **Core Processing Service:** Runs as before (single process)
- **FastAPI Server:** Separate process communicating via filesystem (reads event logs/images) or IPC
- **WebSocket Server:** Real-time event streaming to web dashboard
- **Shared Data:** SQLite database for event queries, filesystem for images

**Rationale for Phase 2:**
- Web dashboard doesn't block processing engine
- API server can restart independently for updates
- Still simple deployment (two processes, no orchestration)

**Phase 3+ Considerations (Out of Scope):**
- Message queue (RabbitMQ, Redis) for multi-camera scaling
- Separate services: Camera Manager, Object Detector, LLM Processor, Event Aggregator
- Only if performance requires it (6+ cameras, complex workflows)

---

## Programming Languages & Frameworks

### Core Processing

**Language: Python 3.10+**

**Rationale:**
- **M1 Native Support:** Python 3.10+ runs natively on Apple Silicon (no Rosetta translation)
- **ML Ecosystem:** Best-in-class libraries for computer vision (OpenCV), ML (coremltools), and LLM integration (Ollama client)
- **Rapid Development:** Solo developer can iterate quickly with Python's expressiveness
- **Learning Goal:** Python is accessible for portfolio review and knowledge sharing
- **Performance:** Acceptable when heavy lifting delegated to CoreML (C++/Metal) and Ollama (Go/C++)

**Alternatives Considered:**
- **Go:** Better concurrency, faster, but lacks ML ecosystem and CoreML bindings
- **Rust:** Maximum performance, but steep learning curve and limited ML libraries
- **C++:** Direct Metal access, but development time 3-5x longer for solo dev

**Key Libraries:**
- **OpenCV 4.8+:** Motion detection, frame manipulation, RTSP client
- **coremltools 7.0+:** CoreML model loading and inference, ANE compatibility
- **ollama-python 0.1.0+:** Ollama API client for LLM inference
- **PyYAML:** Configuration file parsing
- **Pydantic:** Configuration validation and schema enforcement
- **psutil:** System resource monitoring (CPU, memory)

### API Server (Phase 2)

**Framework: FastAPI**

**Rationale:**
- **Async Support:** Handles WebSocket connections efficiently for real-time event streaming
- **Auto-Generated Docs:** OpenAPI/Swagger UI for API exploration (supports learning goal)
- **Type Safety:** Leverages Python type hints with Pydantic for validation
- **Performance:** Comparable to Node.js/Go for I/O-bound operations (API requests)
- **Developer Experience:** Simple routing, dependency injection, built-in testing support

**Alternatives Considered:**
- **Flask:** Simpler but lacks async and auto-docs
- **Django:** Too heavy, includes ORM/admin we don't need
- **Node.js (Express):** Strong ecosystem but adds second language to project

### Web Dashboard Frontend (Phase 2)

**Approach: Vanilla JavaScript (HTML/CSS/JS) → Future Framework if needed**

**Rationale for Vanilla JS:**
- **Zero Build Step:** Simple development, no webpack/vite/parcel complexity
- **Learning Goal:** Understanding fundamentals before frameworks
- **Minimal Dependencies:** No npm package management, no security vulnerabilities in frontend deps
- **Performance:** Native browser APIs are fast, no framework overhead
- **Solo Dev:** Avoid framework churn (React 18 → 19, Vue 3 → 4, etc.)

**Technology Stack:**
- **HTML5:** Semantic markup
- **CSS3:** Modern layout (Grid, Flexbox), CSS variables for theming
- **JavaScript ES6+:** Modules, async/await, fetch API
- **WebSocket API:** Real-time event streaming from FastAPI
- **Local Storage API:** User preferences (dark/light mode, filter settings)

**Future Framework Consideration:**
- If complexity grows beyond ~500 lines of JS, consider **Vue.js 3** or **React 18**
- Trigger: Need for component reusability, complex state management, or routing

**Styling:**
- **No CSS Framework:** Custom CSS for full control and minimal bloat
- **Alternative if needed:** TailwindCSS (utility-first, no unused CSS if purged)

---

## Data Storage

### Event Data

**Database: SQLite**

**Rationale:**
- **Zero Config:** File-based, no server process to manage
- **Local-First:** Aligns with privacy goal, all data stays on disk
- **Sufficient Performance:** Handles 1000s of events easily (50/day × 365 days = 18,250 events/year)
- **ACID Compliance:** Reliable for event logging
- **SQL Query Support:** Enables Phase 2 web dashboard search/filter
- **Portability:** Single .db file, easy backup

**Schema (Initial):**
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    camera_id TEXT NOT NULL,
    motion_confidence REAL,
    detected_objects TEXT,  -- JSON array
    llm_description TEXT,
    image_path TEXT,
    json_log_path TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_camera ON events(camera_id);
```

**Alternatives Considered:**
- **PostgreSQL:** Overkill for single-user local app, requires server process
- **JSON Files Only:** Simple but no query capability for Phase 2 dashboard
- **NoSQL (MongoDB):** Adds complexity, no advantage for structured event data

### Configuration

**Format: YAML Files**

**Rationale:**
- **Human-Readable:** Easy to edit manually, supports comments
- **Git-Friendly:** Text format works well with version control
- **Python Native:** PyYAML is mature and well-supported
- **Hierarchical:** Natural structure for nested config (camera settings, processing params, etc.)

**File: config.yaml**
```yaml
# Camera Configuration
camera:
  rtsp_url: "rtsp://192.168.1.100:554/stream"
  username: "admin"
  password: "password"

# Processing Configuration
processing:
  motion_threshold: 25
  frame_sampling_rate: 10
  object_blacklist: ["cat", "tree"]

# Model Configuration
models:
  coreml_model: "models/yolov3.mlmodel"
  ollama_model: "llava:latest"

# Storage Configuration
storage:
  event_data_dir: "data/events"
  max_storage_gb: 4

# Logging Configuration
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  console: true
  file: "logs/app.log"
```

**Validation:** Pydantic models validate config on load with detailed error messages

**Alternatives Considered:**
- **JSON:** No comments, less human-readable
- **TOML:** Less familiar to users, similar benefits to YAML
- **Python Files:** Executable config is security risk

### Logs

**Format: JSON (structured) + Plaintext (human-readable)**

**Rationale:**
- **Dual Format:** JSON for programmatic access, plaintext for manual review
- **No Database Required:** Filesystem is sufficient for logs
- **Rotation:** Simple FIFO deletion when storage limit reached (NFR10)

**Example JSON Log:**
```json
{
  "timestamp": "2025-11-08T14:32:15Z",
  "event_id": "evt_12345",
  "camera": "front_door",
  "detected_objects": [
    {"label": "person", "confidence": 0.92, "bbox": [100, 150, 200, 400]},
    {"label": "package", "confidence": 0.87, "bbox": [180, 380, 250, 450]}
  ],
  "llm_description": "Person in blue shirt carrying brown package approaching front door",
  "image_path": "data/events/2025-11-08/evt_12345.jpg"
}
```

**Example Plaintext Log:**
```
[2025-11-08 14:32:15] EVENT: Person detected at front door (confidence: 92%)
  - Objects: person (92%), package (87%)
  - Description: Person in blue shirt carrying brown package approaching front door
  - Image: data/events/2025-11-08/evt_12345.jpg
```

---

## Testing Requirements

**Strategy: Comprehensive Testing Pyramid**

**Unit Testing:**
- **Coverage Target:** ≥70% for core logic (NFR29)
- **Framework:** pytest
- **Scope:** Core processing functions (motion detection, event de-duplication, config validation)
- **Mocking:** Mock external services (Ollama, RTSP) for isolated tests

**Integration Testing:**
- **Scope:** End-to-end pipeline with real dependencies
- **Test Data:** Recorded RTSP streams, known event sequences
- **Validation:** Verify event logs match expected outputs

**Performance Testing:**
- **Scope:** All NFRs (see test-plan.md)
- **Tools:** pytest-benchmark, psutil for profiling
- **Critical Tests:** CoreML inference <100ms, LLM <5s, 24hr uptime

**Manual Testing:**
- **Setup Validation:** Fresh install in <30min (NFR15)
- **UI Testing (Phase 2):** Web dashboard functionality, browser compatibility

**Test Environment:**
- **CI/CD:** GitHub Actions with macOS M1 runners
- **Pre-commit Hooks:** Platform checks, license audit, coverage threshold
- **Nightly Tests:** 24hr longevity, resource monitoring

---

## Deployment & Infrastructure

**Development Environment:**
- **Platform:** macOS 13+ on M1 MacBook Pro
- **Python:** 3.10+ with virtual environment (venv)
- **Ollama:** Local installation with LLaVA/Moondream models

**Production Deployment (24/7 Operation):**
- **Platform:** Mac Mini or Mac Studio (M1/M2)
- **Startup:** systemd-equivalent (launchd on macOS) for auto-start
- **Monitoring:** Built-in metrics logging, no external monitoring needed for MVP

**Containerization:**
- **MVP:** Not required (single binary + dependencies)
- **Phase 3+:** Docker for Linux deployment (requires platform abstraction)

**Version Control:**
- **Git:** GitHub repository (public for open source)
- **Branching:** main (stable) + feature branches
- **Releases:** Semantic versioning (v1.0.0, v1.1.0, etc.)

---

## Security & Privacy

**Network Isolation:**
- **No Internet Required:** System operates on local network only
- **Firewall:** Edge firewall blocks external access (NFR14)
- **RTSP Only:** Network traffic limited to camera stream (NFR13)

**Data Privacy:**
- **100% Local:** All processing on-premises (NFR13)
- **No Cloud APIs:** Zero external service calls
- **Data Retention:** User-controlled via storage limits

**Authentication:**
- **MVP/Phase 2:** None (local-only access via localhost)
- **Phase 3+:** HTTP Basic Auth or OIDC if remote access needed

**Dependency Security:**
- **License Compliance:** All dependencies open source (NFR12)
- **Vulnerability Scanning:** `pip-audit` in CI/CD to detect CVEs
- **Pinned Versions:** requirements.txt pins exact versions for reproducibility

---

## Performance Optimization

**Apple Silicon Optimization:**
- **CoreML on ANE:** Object detection runs on Apple Neural Engine (NFR2: <100ms)
- **Metal Acceleration:** GPU acceleration for image processing where available
- **Native ARM64:** All dependencies compiled for M1 (no Rosetta translation)

**Processing Efficiency:**
- **Motion-Triggered:** Process <1% of frames via motion detection filtering (NFR8: >90% filtered)
- **Frame Sampling:** Configurable skip rate (every Nth frame) to reduce load
- **Queue Management:** Max 100 frame queue to prevent memory growth (NFR27)

**Resource Management:**
- **Memory Monitoring:** Auto-shutdown at >8GB (NFR6)
- **Thermal Awareness:** Monitor temperature, reduce processing if >65°C to prevent throttling
- **Disk Management:** Simple FIFO rotation when storage limit reached

---

## Additional Technical Assumptions

**Error Handling:**
- **Fail Fast:** Invalid config exits immediately with clear error message
- **Graceful Degradation:** Single camera failure doesn't crash entire system (Phase 2 multi-camera)
- **Recovery:** Auto-retry for transient failures (RTSP disconnects), manual intervention for persistent failures

**Logging Strategy:**
- **Structured Logging:** JSON for machine parsing, plaintext for human reading
- **Log Levels:** DEBUG (development), INFO (production), WARNING/ERROR (issues)
- **Performance:** Async logging to avoid blocking processing (NFR22: <5% CPU overhead)

**Code Organization:**
- **Type Hints:** All functions use Python type hints for IDE support and validation
- **Docstrings:** Google-style docstrings for all public functions (NFR28: ≥80% coverage)
- **Linting:** Black (formatting), Pylint (linting), mypy (type checking) in pre-commit hooks

**Observability:**
- **Metrics:** Collected in-memory, logged periodically (NFR26: CPU, memory, inference times, frame rate)
- **Tracing:** Simple timestamp-based tracing for performance debugging
- **Profiling:** py-spy for production profiling when needed

**Development Tools:**
- **IDE:** VS Code with Python extension (recommended for solo dev)
- **Debugging:** Built-in Python debugger (pdb) + VS Code debugger
- **Testing:** pytest with coverage reporting
- **Documentation:** Markdown (README, architecture docs), auto-generated API docs (FastAPI)

---
