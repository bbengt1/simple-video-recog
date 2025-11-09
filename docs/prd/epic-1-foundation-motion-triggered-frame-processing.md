# Epic 1: Foundation & Motion-Triggered Frame Processing

**Epic Goal:** Establish project infrastructure and implement motion detection pipeline that connects to RTSP camera, identifies frames with motion, and filters out static scenes, delivering a deployable system that validates the core performance optimization strategy.

## Story 1.1: Project Setup and Configuration Foundation

**As a** developer,
**I want** a properly initialized Python project with dependency management and YAML configuration,
**so that** I have a solid foundation to build the video recognition system with reproducible environments.

**Acceptance Criteria:**

1. Git repository initialized with .gitignore for Python (excludes __pycache__, *.pyc, venv/, .env, data/, logs/)
2. Python virtual environment setup documented in README with commands for creation and activation
3. requirements.txt file created with pinned versions: opencv-python>=4.8.0, pyyaml>=6.0, pydantic>=2.0
4. Directory structure created matching Technical Assumptions (core/, platform/, integrations/, config/, tests/, docs/)
5. config.example.yaml file created with commented examples for all required parameters (camera URL, motion threshold, frame sampling rate, logging settings)
6. Pydantic configuration model defined (ConfigModel class) with validation for all config fields
7. Configuration loading function (load_config) validates YAML against schema and returns typed ConfigModel instance
8. Invalid configuration triggers clear error message showing field name, expected type, and provided value
9. Unit tests for configuration validation covering valid config, missing required fields, invalid types, and out-of-range values
10. README.md created with sections: Overview, Setup Instructions, Configuration Guide (placeholder content acceptable)

---

## Story 1.2: RTSP Camera Connection and Frame Capture

**As a** developer,
**I want** to connect to an RTSP camera stream and continuously capture video frames,
**so that** I have a live video feed to process for motion detection.

**Acceptance Criteria:**

1. RTSP client module (integrations/rtsp.py) implements RTSPCamera class with connect() and capture_frame() methods
2. Camera connection uses opencv-python VideoCapture with RTSP URL from configuration
3. RTSP authentication (username/password) correctly handled via URL format: rtsp://user:pass@ip:port/stream
4. Connection failures (invalid URL, network timeout, auth failure) raise RTSPConnectionError with descriptive message
5. Successful connection logs message: "Connected to RTSP stream: [camera_id]"
6. capture_frame() returns numpy array (BGR format) representing current frame, or None if stream unavailable
7. Frame capture runs in dedicated background thread to avoid blocking main processing
8. Thread-safe frame queue (max 100 frames per NFR27) buffers frames from RTSP thread to main processing thread
9. Graceful handling of stream interruptions: logs warning, attempts reconnection with exponential backoff (1s, 2s, 4s, 8s, max 60s)
10. Unit tests with mocked VideoCapture verify connection, authentication, frame capture, error handling, and reconnection logic
11. Manual integration test documented: Connect to real RTSP camera, verify frames captured at expected rate (15 fps)

---

## Story 1.3: Motion Detection Implementation

**As a** developer,
**I want** to detect motion in video frames using OpenCV background subtraction,
**so that** I can filter out static scenes and only process frames with activity.

**Acceptance Criteria:**

1. Motion detection module (core/motion.py) implements MotionDetector class with detect_motion(frame) method
2. Uses OpenCV BackgroundSubtractorMOG2 algorithm for motion detection (handles lighting changes, shadows)
3. motion_threshold parameter from configuration controls sensitivity (0-255, lower = more sensitive)
4. detect_motion() returns tuple: (has_motion: bool, confidence: float, motion_mask: numpy array)
5. has_motion is True when percentage of changed pixels exceeds threshold (default: 2% of frame)
6. confidence score represents percentage of frame with detected motion (0.0 to 1.0)
7. motion_mask is binary image showing areas of detected motion (useful for debugging/visualization)
8. Background model learns over first 100 frames to establish baseline (ignores motion during learning phase)
9. Motion detector resets background model on manual trigger (via future API) or after major scene change
10. Performance: Motion detection completes in <50ms per frame on M1 (measured via unit test with time.perf_counter)
11. Unit tests verify: motion detected in test videos with known movement, static scenes return has_motion=False, threshold configuration works correctly
12. Edge cases tested: sudden lighting change, gradual lighting change (sunrise/sunset), shadow movement

---

## Story 1.4: Frame Sampling and Processing Pipeline

**As a** developer,
**I want** to implement configurable frame sampling to process every Nth frame,
**so that** I can optimize performance by reducing the frame processing rate while maintaining adequate coverage.

**Acceptance Criteria:**

1. Frame sampling logic implemented in core/pipeline.py with FrameSampler class
2. frame_sampling_rate parameter from configuration determines sampling (e.g., 10 = process every 10th frame)
3. FrameSampler.should_process(frame_count) returns True/False based on sampling rate
4. frame_count is continuously incrementing counter of total frames captured (not just processed)
5. Sampling applies AFTER motion detection: Sample from motion-triggered frames, not all frames
6. Processing pipeline orchestration (ProcessingPipeline class) coordinates: frame capture → motion detection → sampling → (future: object detection)
7. Pipeline maintains metrics: total_frames_captured, frames_with_motion, frames_sampled, frames_processed
8. Metrics accessible via get_metrics() method returning dictionary
9. Pipeline runs continuously in main thread, reading from frame queue populated by RTSP thread
10. Ctrl+C (SIGINT) cleanly stops pipeline: stops RTSP thread, processes remaining queued frames, logs final metrics
11. Unit tests verify sampling logic: rate=1 processes all frames, rate=10 processes every 10th, rate=100 processes every 100th
12. Integration test: Run pipeline with test video, verify metrics match expected values based on known motion events

---

## Story 1.5: Basic Logging Framework and Console Output

**As a** developer,
**I want** structured logging with configurable verbosity levels,
**so that** I can debug issues during development and monitor the system in production.

**Acceptance Criteria:**

1. Python logging configured in core/logging_config.py with setup_logging(config) function
2. Logging level configurable via YAML: DEBUG, INFO, WARNING, ERROR
3. Console handler outputs to stdout with formatted messages: "[TIMESTAMP] [LEVEL] [MODULE] Message"
4. Timestamp format: ISO 8601 with timezone (2025-11-08T14:32:15-08:00)
5. Module name included in log output for easy debugging (e.g., [rtsp], [motion], [pipeline])
6. Structured logging metadata available for future JSON output (not yet implemented, but architecture supports it)
7. Key events logged at INFO level: RTSP connected, motion detected, frame processed, metrics summary
8. Errors logged at ERROR level with full exception stack traces
9. DEBUG level logs frame-by-frame processing details (frame number, motion confidence, sampling decision)
10. Logging performance overhead measured: <2% CPU impact at INFO level, <5% at DEBUG level (verified via profiling)
11. Unit tests verify correct log level filtering (DEBUG messages don't appear when level=INFO)
12. Manual test: Run system with different log levels, verify appropriate messages appear/disappear

---

## Story 1.6: Startup Health Check and System Status Display

**As a** developer,
**I want** a startup health check that validates all dependencies and displays system status,
**so that** I can quickly identify configuration or connectivity issues before processing begins.

**Acceptance Criteria:**

1. Health check module (core/health_check.py) implements HealthChecker class with run_checks() method
2. Startup sequence performs checks in order: config validation → RTSP connection → initial status display
3. Each check displays status: "✓ Configuration loaded: config.yaml" or "✗ RTSP connection failed: [error details]"
4. Health check summary displayed before processing starts:
   ```
   ===== System Health Check =====
   ✓ Configuration loaded: config.yaml
   ✓ RTSP stream: Connected (front_door)
   ✓ Motion detector: Initialized
   ✓ Frame queue: Ready (0/100)
   ===== System Ready =====
   ```
5. If any check fails, system exits with non-zero exit code and clear error message explaining what failed and how to fix
6. Runtime status display every 60 seconds (configurable) showing metrics:
   ```
   [INFO] Runtime Status (60s interval)
     Frames Captured: 1,847 (30.8 fps)
     Motion Detected: 127 (6.9% hit rate)
     Frames Sampled: 13 (sampling rate: 1/10)
     Queue Size: 3/100
   ```
7. Status display uses human-readable formatting: comma separators for large numbers, percentage with 1 decimal
8. status_interval configurable in YAML (default: 60 seconds, 0 = disabled)
9. Unit tests verify health check logic: all pass scenario, single failure scenario, multiple failure scenario
10. Integration test: Start system with invalid config, verify clear error message and non-zero exit code

---

## Story 1.7: Basic CLI Entry Point and Execution

**As a** developer,
**I want** a command-line entry point that initializes the system and runs the processing pipeline,
**so that** I can start the video recognition system with a simple command.

**Acceptance Criteria:**

1. CLI entry point in main.py with main() function as execution starting point
2. Command-line argument: config file path (positional argument, required)
   ```bash
   python main.py config.yaml
   ```
3. If no config file provided, display usage message and exit:
   ```
   Usage: python main.py <config-file>
   Example: python main.py config.yaml
   ```
4. main() orchestrates full startup sequence:
   - Load configuration from specified file
   - Setup logging based on config
   - Run health checks
   - Initialize RTSP connection
   - Initialize motion detector
   - Start processing pipeline
   - Run until interrupted (Ctrl+C)
5. Graceful shutdown on SIGINT (Ctrl+C): Stop RTSP thread → flush frame queue → log final metrics → exit with code 0
6. Uncaught exceptions logged with full stack trace and exit with code 1
7. Main execution wrapped in `if __name__ == "__main__":` for proper module import behavior
8. requirements.txt updated with all dependencies used: opencv-python, pyyaml, pydantic, numpy
9. README updated with "Quick Start" section showing how to run the system
10. Integration test: Full end-to-end execution with test RTSP stream, verify system starts, processes frames, and stops cleanly on Ctrl+C

---

## Story 1.8: Unit Testing Framework and Initial Test Coverage

**As a** developer,
**I want** a pytest-based testing framework with initial unit tests for core logic,
**so that** I can verify functionality and prevent regressions as I add features.

**Acceptance Criteria:**

1. pytest installed and added to requirements-test.txt (separate from runtime requirements)
2. Test directory structure created: tests/unit/, tests/integration/, tests/conftest.py
3. conftest.py contains shared fixtures: sample_config, mock_rtsp_camera, sample_frame
4. Unit tests for configuration validation (tests/unit/test_config.py): valid config loads, invalid config raises error, missing fields detected, type validation works
5. Unit tests for motion detection (tests/unit/test_motion.py): motion detected in test video, static scenes return False, threshold configuration works, performance <50ms per frame
6. Unit tests for frame sampling (tests/unit/test_sampling.py): sampling rates verified, metrics tracking accurate
7. Unit tests for RTSP client (tests/unit/test_rtsp.py): connection logic, error handling, reconnection backoff (using mocks)
8. Test coverage measurement configured: `pytest --cov=core --cov=integrations --cov-report=term`
9. Coverage target for Epic 1: ≥60% (will increase to 70% by Epic 4 per NFR29)
10. All tests pass: `pytest tests/unit -v` returns zero failures
11. README updated with "Running Tests" section showing pytest commands
12. CI/CD placeholder: .github/workflows/tests.yml created (runs on pull request, executes pytest)

---

**Epic 1 Summary:**
- **8 Stories** delivering foundation, RTSP connection, motion detection, and basic CLI
- **Vertical slices:** Each story delivers complete, testable functionality
- **Progressive complexity:** Starts with setup, builds to full pipeline
- **Test coverage:** Unit tests throughout, integration tests for key flows
- **Deployable:** After Epic 1, system can monitor camera for motion events and log to console

---

## Rationale for Story Breakdown:

**Why 8 stories:**
- Each story is focused (single responsibility)
- Sized for AI agent execution (2-4 hours estimated)
- Delivers testable functionality
- Logical build-up from foundation to working pipeline

**Story sequencing:**
- 1.1 (Setup) must come first - foundation for everything
- 1.2 (RTSP) before 1.3 (Motion) - need frames to detect motion in
- 1.3 (Motion) before 1.4 (Sampling) - sampling applies to motion-triggered frames
- 1.4 (Pipeline) integrates 1.2+1.3 - natural progression
- 1.5 (Logging) could be earlier but needed throughout, added when we have meaningful events to log
- 1.6 (Health Check) uses prior components - logical placement
- 1.7 (CLI) ties everything together - entry point comes after components exist
- 1.8 (Testing) throughout development - added as final story to formalize framework

**Cross-cutting concerns handled:**
- Testing: Integrated into each story's acceptance criteria + dedicated Story 1.8 for framework
- Logging: Story 1.5 establishes framework, used in all subsequent stories
- Configuration: Story 1.1 establishes pattern, used throughout
- Error handling: Built into each story's acceptance criteria

---

---
