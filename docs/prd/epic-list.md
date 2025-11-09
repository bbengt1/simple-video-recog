# Epic List

The MVP is organized into **4 sequential epics**, each delivering a significant, deployable increment of functionality. Each epic builds upon the previous, enabling progressive delivery of value while maintaining focus on the core processing pipeline.

## Epic 1: Foundation & Motion-Triggered Frame Processing

**Goal:** Establish project infrastructure and implement motion detection pipeline that connects to RTSP camera, identifies frames with motion, and filters out static scenes.

**Value Delivered:** System can connect to camera, continuously monitor for motion, and identify when something interesting happens (>10x reduction in frames requiring further processing). This validates the core performance optimization strategy and proves the M1 can handle real-time RTSP processing.

**Key Capabilities:**
- Project setup (Git, Python environment, dependencies)
- YAML configuration loading and validation
- RTSP camera connection and frame capture
- Motion detection using OpenCV background subtraction
- Frame sampling (every Nth frame)
- Basic logging framework (console output)
- Health check / system status display

**Deployment Readiness:** Can run continuously, connect to camera, and log motion events to console.

---

## Epic 2: Object Detection & Semantic Understanding

**Goal:** Integrate CoreML object detection and Ollama LLM to identify what objects are present in motion-triggered frames and generate semantic event descriptions.

**Value Delivered:** System understands what's happening (not just that something moved). Provides natural language descriptions like "person carrying package approaching door" instead of raw motion signals. This is the core differentiator from traditional motion detection systems.

**Key Capabilities:**
- CoreML model loading and Apple Neural Engine validation
- Object detection inference on motion-triggered frames
- Object blacklist filtering (ignore cats, trees, etc.)
- Annotated image generation (bounding boxes + labels)
- Ollama service integration
- Vision LLM inference (LLaVA or Moondream)
- Structured JSON output with semantic descriptions
- Event de-duplication logic (time-based suppression)

**Deployment Readiness:** System processes events end-to-end and generates annotated images + semantic descriptions (outputs to files).

---

## Epic 3: Event Persistence & Data Management

**Goal:** Implement SQLite database for event storage, dual-format logging (JSON + plaintext), and storage management to enable event querying and long-term data retention within disk constraints.

**Value Delivered:** Events are permanently recorded and queryable. Users can review historical events, search by time/object type, and analyze patterns. Provides foundation for Phase 2 web dashboard.

**Key Capabilities:**
- SQLite database schema and initialization
- Event data model and storage
- JSON log file generation (structured)
- Plaintext log file generation (human-readable)
- Storage monitoring and limits enforcement
- Log rotation logic (FIFO when storage limit reached)
- Performance metrics logging (CPU, memory, inference times)

**Deployment Readiness:** All events persist to database and log files, queryable via SQL, storage stays within 4GB limit.

---

## Epic 4: CLI Interface & Production Readiness

**Goal:** Deliver production-ready CLI tool with professional command-line interface, graceful error handling, signal management, and operational features for 24/7 deployment.

**Value Delivered:** System is robust, user-friendly, and ready for continuous operation. Developers can quickly set up, configure, validate, and monitor the system. Supports the learning goal with comprehensive help, validation feedback, and runtime metrics.

**Key Capabilities:**
- Command-line argument parsing (--help, --dry-run, --version, config file)
- Startup health check summary (config, models, Ollama, RTSP)
- Version and build information display
- Dry-run mode (validate without processing)
- Signal handling (SIGINT, SIGTERM for shutdown, SIGHUP for hot-reload)
- Graceful shutdown with log flushing and resource cleanup
- Runtime performance metrics display (configurable intervals)
- Comprehensive error handling and validation feedback
- Platform compatibility checks (macOS, M1, Python version)
- Dependency version validation
- Example configuration file (config.example.yaml)
- README with setup instructions and troubleshooting

**Deployment Readiness:** Complete production system ready for 24/7 operation on Mac Mini/Studio with full CLI, error handling, and monitoring.

---

## Epic Sequencing Rationale

**Why 4 Epics:**
- **Epic 1:** Foundation is essential - can't build anything without infrastructure and basic connectivity. Motion detection validates performance approach early.
- **Epic 2:** Intelligence layer (CoreML + LLM) is the core value proposition - must come before persistence to ensure we're saving the right data.
- **Epic 3:** Persistence enables historical analysis and prepares for web dashboard - logical after we know what we're storing.
- **Epic 4:** Production features polish the MVP into a deployable system - best done last when core functionality is stable.

**Value at Each Stage:**
- After Epic 1: Can monitor camera for motion (basic security/awareness)
- After Epic 2: Can understand what's happening with semantic descriptions (full detection capability)
- After Epic 3: Can review historical events and analyze patterns (long-term value)
- After Epic 4: Production-ready system ready for continuous deployment (complete MVP)

**Alternative Considered:**
- Could merge Epic 3 + 4 into single "Persistence & Production" epic, reducing to 3 epics total
- Decided against: Epic 3 (data) and Epic 4 (CLI/ops) are distinct concerns, each substantial enough to warrant separate epic
- Keeps individual epics focused and stories manageable for AI agent execution

---
