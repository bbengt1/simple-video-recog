# Epic 4: CLI Interface & Production Readiness

**Epic Goal:** Deliver production-ready CLI application with professional command-line interface, robust signal handling, graceful error management, and operational features required for 24/7 deployment on Mac Mini/Studio.

## Story 4.1: Command-Line Argument Parsing and Entry Point

**As a** developer,
**I want** a professional CLI interface with standard arguments (--help, --config, --version, --dry-run),
**so that** the system is easy to use, configure, and validate before running in production.

**Acceptance Criteria:**

1. CLI entry point implemented as `main.py` with main() function
2. Argument parsing using argparse library with following options:
   - `--config PATH` or `-c PATH`: Path to YAML configuration file (default: config/config.yaml)
   - `--dry-run`: Validate configuration and connectivity without starting processing loop
   - `--version` or `-v`: Display version and build information
   - `--help` or `-h`: Display usage instructions and examples
   - `--log-level LEVEL`: Override logging level (DEBUG, INFO, WARNING, ERROR)
   - `--metrics-interval SECONDS`: Override metrics display interval (default: 60)
3. Help text includes:
   - Usage: `python main.py [OPTIONS]`
   - Description: "Local Video Recognition System - Motion detection with CoreML object detection and Ollama LLM semantic understanding"
   - Examples: `python main.py --config cameras/front-door.yaml --dry-run`
   - Exit codes: 0=success, 1=error, 2=config invalid, 3=storage full
4. Version output format: `video-recog v1.0.0 (build 2025-11-08) - Python 3.10.12 - macOS 14.2`
5. Config file validation: If --config path doesn't exist, exit with error code 2 and message
6. Argument validation: Invalid --log-level value shows error and available options
7. Entry point callable via: `python main.py` or `python -m video_recog` (package mode)
8. Shebang support: `#!/usr/bin/env python3` allows direct execution (`./main.py`)
9. Exit code consistency: All exit paths use defined exit codes (documented in README)
10. Unit tests verify: argument parsing, default values, validation logic, help text generation
11. Integration test: Launch with each argument combination, verify expected behavior
12. Manual test: Run --help and verify output is clear and accurate

---

## Story 4.2: Startup Health Check and System Validation

**As a** developer,
**I want** comprehensive startup health checks that validate all dependencies before processing begins,
**so that** configuration errors are caught early with clear error messages (NFR23, NFR28).

**Acceptance Criteria:**

1. Health check module (core/health_check.py) implements HealthChecker class with check_all() method
2. Health checks performed in sequence during startup (before processing loop):
   - **Config validation**: YAML syntax, required fields, data types (via Pydantic schema)
   - **Platform check**: Verify macOS platform, Apple Silicon architecture (M1/M2/M3)
   - **Python version**: Verify Python >=3.10 (exit if <3.10)
   - **Dependencies**: Verify OpenCV, CoreML, Ollama client versions match requirements.txt
   - **CoreML model**: Load model file, verify Neural Engine availability
   - **Ollama service**: Check Ollama running (HTTP health check), verify model available (ollama list)
   - **RTSP connectivity**: Connect to camera URL, capture test frame, verify resolution
   - **File permissions**: Verify write access to data/, logs/, config/ directories
   - **Storage availability**: Verify <4GB storage used, warn if >80%
3. Health check results displayed in console output:
   ```
   [STARTUP] Video Recognition System v1.0.0
   [CONFIG] ✓ Configuration loaded: config/config.yaml
   [PLATFORM] ✓ macOS 14.2 on Apple M1 (arm64)
   [PYTHON] ✓ Python 3.10.12
   [MODELS] ✓ CoreML model loaded: models/yolov3.mlmodel (Neural Engine enabled)
   [OLLAMA] ✓ Ollama service running, model available: llava:latest
   [CAMERA] ✓ RTSP connected: rtsp://192.168.1.100:554/stream (1920x1080 @ 30fps)
   [STORAGE] ✓ Storage: 1.2GB / 4GB (30%)
   [READY] All health checks passed. Starting processing...
   ```
4. Health check failures exit immediately with clear error messages:
   - "ERROR: CoreML model not found: models/yolov3.mlmodel - Run setup script to download models"
   - "ERROR: Ollama service not running - Start Ollama with: ollama serve"
   - "ERROR: RTSP connection failed: Authentication required - Check credentials in config.yaml"
5. Dry-run mode: Perform all health checks, display results, exit with code 0 if all pass
6. Health check timeout: Each check has 10s timeout (configurable), prevents hanging on network issues
7. Detailed logging: Each check logs result at INFO level, failures at ERROR level
8. Health check results stored in HealthCheckResult object: all_passed, failed_checks, warnings
9. Startup time: All health checks complete in <30 seconds (NFR18)
10. Unit tests verify: each individual check, failure handling, timeout behavior
11. Integration test: Test each failure scenario, verify error messages and exit codes
12. Manual test: Intentionally break each dependency, verify clear error message displayed

---

## Story 4.3: Version and Build Information Display

**As a** developer,
**I want** to display version, build date, and dependency versions,
**so that** I can identify which version is running and troubleshoot compatibility issues.

**Acceptance Criteria:**

1. Version module (core/version.py) implements get_version_info() function
2. Version information stored in version.py:
   - VERSION = "1.0.0" (semantic versioning)
   - BUILD_DATE = "2025-11-08" (ISO format, set during build)
   - GIT_COMMIT = "abc123f" (short commit hash, set during build)
3. get_version_info() returns VersionInfo object containing:
   - version: Application version (VERSION)
   - build_date: Build timestamp (BUILD_DATE)
   - git_commit: Git commit hash (GIT_COMMIT)
   - python_version: Runtime Python version (sys.version)
   - platform: OS and architecture (platform.platform())
   - opencv_version: OpenCV version (cv2.__version__)
   - coreml_version: CoreML Tools version (coremltools.__version__)
   - ollama_version: Ollama client version (ollama.__version__)
4. `--version` flag displays version information in human-readable format:
   ```
   Video Recognition System v1.0.0
   Build: 2025-11-08 (commit abc123f)
   Python: 3.10.12
   Platform: macOS-14.2-arm64
   Dependencies:
     - OpenCV: 4.8.1
     - CoreML Tools: 7.0.0
     - Ollama: 0.1.0
   ```
5. Version info logged at startup (INFO level) before health checks
6. Version info included in metrics.json for correlation with performance data
7. Version info accessible via runtime command (future): Type 'v' during execution to display version
8. Build process: CI/CD pipeline sets BUILD_DATE and GIT_COMMIT during build (GitHub Actions)
9. Development mode: If GIT_COMMIT not set, use "dev" placeholder
10. Unit tests verify: version string format, all fields populated correctly
11. Integration test: Launch with --version, verify output format matches expected
12. Manual test: Review version output, confirm all information is accurate and helpful

---

## Story 4.4: Dry-Run Mode and Configuration Validation

**As a** developer,
**I want** to validate configuration without starting the processing loop,
**so that** I can test config changes safely before deploying to production.

**Acceptance Criteria:**

1. `--dry-run` flag triggers validation-only mode (no frame processing)
2. Dry-run mode performs all startup health checks (Story 4.2)
3. Additional validation in dry-run mode:
   - **Config validation**: Display all parsed configuration values with types
   - **Model validation**: Load CoreML model, display input/output shapes
   - **Ollama model test**: Send test image to Ollama, verify response format
   - **RTSP test capture**: Capture 10 frames, display frame rate and resolution
   - **Motion detection test**: Capture 10 frames, run motion detection, display sensitivity
   - **Storage calculation**: Display current storage usage breakdown (DB, logs, images)
4. Dry-run output format:
   ```
   [DRY-RUN] Configuration Validation

   Camera Configuration:
     RTSP URL: rtsp://192.168.1.100:554/stream
     Resolution: 1920x1080 @ 30fps
     Motion threshold: 25
     Frame sampling rate: 10fps

   Model Configuration:
     CoreML model: models/yolov3.mlmodel
       Input shape: (1, 3, 416, 416)
       Output: 80 object classes
     Ollama model: llava:latest
       Context length: 2048 tokens

   Processing Configuration:
     Object blacklist: ["cat", "tree"]
     Event suppression window: 30 seconds

   Storage Configuration:
     Current usage: 1.2GB / 4GB (30%)
     Database: 450MB (15,234 events)
     Logs: 680MB
     Images: 92MB

   [TEST] Capturing test frames from camera...
   [TEST] ✓ Captured 10 frames successfully (avg 33ms/frame)
   [TEST] Running motion detection test...
   [TEST] ✓ Motion detected in 3/10 frames (30% sensitivity)
   [TEST] Running CoreML inference test...
   [TEST] ✓ Object detection completed in 87ms (Neural Engine)
   [TEST] Running Ollama LLM test...
   [TEST] ✓ LLM inference completed in 1.2s

   [DRY-RUN] ✓ All validations passed. System ready for production.
   [DRY-RUN] Remove --dry-run flag to start processing.
   ```
5. Dry-run exits with code 0 if all validations pass, code 2 if any fail
6. Dry-run mode completes in <60 seconds (includes test inferences)
7. No events persisted during dry-run (database/logs not modified)
8. No annotated images saved during dry-run
9. Dry-run results logged to dry_run_results.json for automated validation in CI/CD
10. Unit tests verify: dry-run flag parsing, validation steps executed, no side effects
11. Integration test: Run dry-run mode end-to-end, verify no data persisted
12. Manual test: Run dry-run before production deployment, verify all checks pass

---

## Story 4.5: Signal Handling and Graceful Shutdown

**As a** developer,
**I want** robust signal handling (SIGINT, SIGTERM, SIGHUP) with graceful shutdown,
**so that** the system can be stopped safely without data loss or corrupted state (NFR7, FR28-31).

**Acceptance Criteria:**

1. Signal handler module (core/signals.py) implements SignalHandler class with register_handlers() method
2. Signals handled:
   - **SIGINT (Ctrl+C)**: Trigger graceful shutdown
   - **SIGTERM (kill)**: Trigger graceful shutdown
   - **SIGHUP**: Reload configuration without restart (hot-reload)
3. Signal handler registration during startup (after health checks, before processing loop)
4. Graceful shutdown sequence (triggered by SIGINT/SIGTERM):
   - Stop accepting new frames (close RTSP connection)
   - Finish processing current frame (if any in progress)
   - Flush all log buffers (JSON, plaintext, metrics)
   - Close database connection with final transaction commit
   - Save final metrics snapshot to metrics.json
   - Log shutdown statistics: total_runtime, frames_processed, events_created
   - Exit with code 0
5. Shutdown timeout: If shutdown doesn't complete in 10 seconds, force exit (prevents hanging)
6. Shutdown message format:
   ```
   [SIGNAL] Received SIGINT, initiating graceful shutdown...
   [SHUTDOWN] Stopping frame capture...
   [SHUTDOWN] Processing final frame...
   [SHUTDOWN] Flushing log buffers...
   [SHUTDOWN] Closing database connection...
   [SHUTDOWN] Saving final metrics...
   [SHUTDOWN] Shutdown complete.

   Session Summary:
     Runtime: 2h 34m 12s
     Frames processed: 15,234
     Motion detected: 1,823 frames (12%)
     Events created: 342
     Events suppressed: 78 (de-duplication)
     Avg CoreML inference: 89ms
     Avg LLM inference: 1.3s
     Storage used: 2.1GB / 4GB

   [EXIT] Video Recognition System stopped gracefully.
   ```
7. SIGHUP hot-reload sequence:
   - Log: "Received SIGHUP, reloading configuration..."
   - Reload config.yaml without stopping processing
   - Re-validate configuration (if invalid, keep old config and log error)
   - Apply new settings: motion_threshold, frame_sampling_rate, object_blacklist
   - Reconnect to RTSP if camera URL changed
   - Reload CoreML model if model path changed
   - Switch Ollama model if model name changed
   - Log: "Configuration reloaded successfully" or "Configuration reload failed: [reason]"
8. Signal safety: Signal handlers use thread-safe flags (threading.Event) to communicate with main loop
9. Idempotent shutdown: Multiple SIGINT signals don't cause errors (second signal logs "Shutdown already in progress...")
10. Unit tests verify: signal handler registration, shutdown sequence, hot-reload logic
11. Integration test: Send SIGINT during processing, verify graceful shutdown and data integrity
12. Manual test: Run for 1 hour, send SIGINT, verify clean shutdown and session summary

---

## Story 4.6: Runtime Performance Metrics Display

**As a** developer,
**I want** real-time performance metrics displayed during execution,
**so that** I can monitor system health and validate NFR performance targets in production (NFR21, FR25-26).

**Acceptance Criteria:**

1. Runtime metrics display implemented in core/runtime_display.py as MetricsDisplay class
2. Metrics displayed to console every 60 seconds (configurable via --metrics-interval)
3. Metrics display format:
   ```
   ┌─────────────────────────────────────────────────────────────────┐
   │ Runtime Metrics - 2025-11-08 14:32:15 (uptime: 2h 34m 12s)     │
   ├─────────────────────────────────────────────────────────────────┤
   │ Processing:                                                      │
   │   Frames processed:        15,234                               │
   │   Motion detected:         1,823 (12% hit rate)                 │
   │   Events created:          342                                  │
   │   Events suppressed:       78 (de-duplication)                  │
   │                                                                  │
   │ Performance:                                                     │
   │   Frame capture:           avg 33ms, max 45ms                   │
   │   Motion detection:        avg 12ms, max 18ms                   │
   │   CoreML inference:        avg 89ms, p95 102ms, max 134ms ✓     │
   │   LLM inference:           avg 1.3s, p95 1.8s, max 2.4s         │
   │   End-to-end latency:      avg 1.5s, p95 2.1s                   │
   │                                                                  │
   │ Resources:                                                       │
   │   CPU usage:               avg 45%, current 52%                 │
   │   Memory usage:            1.2GB / 8GB (15%)                    │
   │   Storage:                 2.1GB / 4GB (52%) ✓                  │
   │                                                                  │
   │ Availability:                                                    │
   │   System uptime:           99.8% (5 errors in 15,234 frames)    │
   │   RTSP connection:         Healthy (reconnects: 0)              │
   │   Database status:         Healthy (15,234 events)              │
   │                                                                  │
   │ [✓] = Meeting NFR target  [⚠] = Approaching limit  [✗] = Failed │
   └─────────────────────────────────────────────────────────────────┘
   ```
4. Performance indicators:
   - ✓ (green checkmark): Metric meets NFR target
   - ⚠ (yellow warning): Metric within 10% of NFR limit
   - ✗ (red X): Metric exceeds NFR limit (performance degraded)
5. NFR target annotations:
   - CoreML inference <100ms: Show ✓ if <100ms, ⚠ if 100-110ms, ✗ if >110ms
   - Storage <4GB: Show ✓ if <3.6GB, ⚠ if 3.6-4GB, ✗ if >4GB
6. Metrics display logging: Each display snapshot also logged to logs/metrics.json
7. Display refresh: Console output uses ANSI escape codes to update in place (doesn't scroll)
8. Minimal mode: If --metrics-interval=0, disable runtime display (only log to file)
9. Compact mode: First 5 minutes show full display, then switch to compact (one-line summary)
10. Metrics display overhead: <0.5% CPU (verified via profiling)
11. Unit tests verify: metric formatting, indicator logic, ANSI escape codes
12. Integration test: Run for 10 minutes, verify metrics display updates correctly
13. Manual test: Monitor display during 1-hour run, verify accuracy against metrics.json

---

## Story 4.7: Comprehensive Error Handling and User Feedback

**As a** developer,
**I want** clear error messages with actionable guidance for all failure scenarios,
**so that** users can quickly diagnose and fix issues without deep technical knowledge (NFR23, NFR28).

**Acceptance Criteria:**

1. Error handling strategy implemented across all modules with consistent format
2. Error categories and handling:
   - **Configuration errors**: Clear message + example of correct format
   - **Dependency errors**: Clear message + installation/setup instructions
   - **Runtime errors**: Clear message + suggested recovery action
   - **Network errors**: Clear message + connectivity troubleshooting steps
3. Error message format:
   ```
   [ERROR] Category: Brief description
   Details: Specific error details
   Solution: Step-by-step fix instructions
   Documentation: Link to relevant docs section
   ```
4. Example error messages:
   ```
   [ERROR] Configuration: Invalid motion_threshold value
   Details: motion_threshold must be between 0 and 255, got: 300
   Solution: Edit config.yaml and set motion_threshold to a value between 0-255
            Recommended values: 15 (high sensitivity) to 50 (low sensitivity)
   Documentation: See docs/configuration.md#motion-detection

   [ERROR] Dependency: Ollama service not running
   Details: Connection refused on http://localhost:11434
   Solution: 1. Install Ollama: brew install ollama
            2. Start service: ollama serve
            3. Verify running: curl http://localhost:11434
   Documentation: See docs/setup.md#ollama-setup

   [ERROR] Runtime: RTSP connection lost
   Details: Stream interrupted after 2h 15m (15,234 frames processed)
   Solution: System will attempt reconnection in 5 seconds...
            If connection fails 3 times, check camera status and network
   Documentation: See docs/troubleshooting.md#rtsp-connection-issues
   ```
5. Error logging: All errors logged at ERROR level with full stack trace in logs/error.log
6. User-facing errors: Console output shows simplified message (no stack trace)
7. Error recovery strategies:
   - **Transient errors**: Auto-retry with exponential backoff (RTSP reconnection)
   - **Configuration errors**: Exit immediately with error code 2
   - **Fatal errors**: Graceful shutdown with error code 1
   - **Storage errors**: Trigger log rotation, then retry
8. Error aggregation: Similar errors suppressed (log "RTSP reconnection failed (3 attempts)" instead of 3 separate messages)
9. Exit codes documented in README:
   - 0: Clean shutdown
   - 1: Fatal error (runtime failure)
   - 2: Configuration invalid
   - 3: Storage limit exceeded
   - 4: Dependency missing/incompatible
10. Unit tests verify: error message formatting, exit codes, recovery logic
11. Integration test: Trigger each error category, verify message quality and exit code
12. Manual test: Review all error messages for clarity and actionable guidance

---

## Story 4.8: Platform Compatibility Checks

**As a** developer,
**I want** explicit platform compatibility validation (macOS, Apple Silicon, Python version),
**so that** users get clear feedback if running on unsupported platforms (NFR1, NFR24-25).

**Acceptance Criteria:**

1. Platform check module (core/platform_check.py) implements PlatformValidator class
2. Platform validation during startup health check (before model loading):
   - **OS check**: Verify platform.system() == "Darwin" (macOS)
   - **Architecture check**: Verify platform.machine() == "arm64" (Apple Silicon)
   - **Chip check**: Detect M1/M2/M3 via sysctl hw.model
   - **Python version**: Verify sys.version_info >= (3, 10)
   - **macOS version**: Verify macOS >= 13.0 (Ventura) for CoreML Neural Engine support
3. Platform check results displayed during startup:
   ```
   [PLATFORM] ✓ macOS 14.2 (23C64)
   [PLATFORM] ✓ Apple M1 Pro (arm64)
   [PLATFORM] ✓ Python 3.10.12
   [PLATFORM] ✓ CoreML Neural Engine supported
   ```
4. Platform validation failures with specific error messages:
   ```
   [ERROR] Platform: Unsupported operating system
   Details: This system requires macOS 13.0 or later, detected: Linux
   Solution: This application is designed for Apple Silicon Macs (M1/M2/M3)
            For other platforms, see docs/alternative-platforms.md

   [ERROR] Platform: Unsupported architecture
   Details: Apple Silicon (M1/M2/M3) required, detected: x86_64
   Solution: This application requires Apple Neural Engine for CoreML inference
            Intel Macs are not supported (no Neural Engine)

   [ERROR] Platform: Python version too old
   Details: Python 3.10 or later required, detected: 3.9.7
   Solution: Upgrade Python: brew install python@3.10
            Then recreate virtual environment with Python 3.10
   ```
5. Warning for unsupported configurations (don't exit, but warn):
   - macOS <14.0: "Warning: macOS 13.x supported but macOS 14+ recommended for best performance"
   - Python 3.13+: "Warning: Tested on Python 3.10-3.12, Python 3.13 may have compatibility issues"
6. Neural Engine detection: Use coremltools to verify Neural Engine availability
7. Platform info logged at startup for diagnostics (chip model, RAM, CPU cores)
8. Partial support mode (future): If platform check fails, suggest alternative config (e.g., CPU inference instead of Neural Engine)
9. CI/CD integration: Platform check results included in automated test reports
10. Unit tests verify: platform detection logic, error messages for each unsupported platform
11. Integration test: Mock platform values, verify correct validation and error messages
12. Manual test: Attempt to run on Intel Mac, verify clear error message (if available for testing)

---

## Story 4.9: Documentation and Example Configuration

**As a** developer,
**I want** comprehensive README, example configuration, and troubleshooting guide,
**so that** new users can set up and run the system without external help (NFR15-16, NFR28).

**Acceptance Criteria:**

1. README.md created with following sections (NFR16):
   - **Overview**: 2-3 sentence description of what the system does
   - **Features**: Bullet list of key capabilities (motion detection, CoreML, Ollama, etc.)
   - **Requirements**: Platform requirements (macOS 13+, M1/M2/M3, Python 3.10+)
   - **Installation**: Step-by-step setup instructions (clone, venv, requirements, models)
   - **Quick Start**: Minimal steps to run for first time (config setup, dry-run, run)
   - **Configuration**: Table of all config parameters with descriptions and defaults
   - **Usage**: CLI options and examples (--dry-run, --config, --version)
   - **Architecture**: High-level diagram showing processing pipeline flow
   - **Performance**: NFR targets and expected metrics on reference hardware
   - **Troubleshooting**: ≥5 common issues with solutions (as per NFR16)
   - **FAQ**: ≥5 frequently asked questions (as per NFR16)
   - **Development**: How to run tests, contribute, code structure
   - **License**: MIT license
2. Example configuration file created: config/config.example.yaml
   ```yaml
   # Example configuration for Local Video Recognition System
   # Copy to config.yaml and customize for your setup

   camera:
     rtsp_url: "rtsp://192.168.1.100:554/stream"
     username: "admin"
     password: "password"
     # Optional: camera identifier for multi-camera setups
     camera_id: "front-door"

   processing:
     # Motion detection threshold (0-255, lower = more sensitive)
     motion_threshold: 25
     # Frame sampling rate (fps) for motion detection
     frame_sampling_rate: 10
     # Objects to ignore (won't trigger events)
     object_blacklist: ["cat", "tree", "car"]
     # Event de-duplication window (seconds)
     event_suppression_window: 30

   models:
     # Path to CoreML model file
     coreml_model: "models/yolov3.mlmodel"
     # Ollama model name (must be pulled first: ollama pull llava:latest)
     ollama_model: "llava:latest"
     # Minimum confidence for object detection (0.0-1.0)
     confidence_threshold: 0.5

   storage:
     # Maximum storage for events/logs/images (GB)
     max_storage_gb: 4
     # Minimum retention period (days)
     min_retention_days: 7
     # Check storage every N events
     storage_check_interval: 100

   logging:
     # Logging level (DEBUG, INFO, WARNING, ERROR)
     log_level: "INFO"
     # Metrics display interval (seconds, 0 to disable)
     metrics_interval: 60
   ```
3. Troubleshooting guide (docs/troubleshooting.md) with ≥10 common issues:
   - Ollama service not running
   - RTSP authentication failed
   - CoreML model not found
   - Neural Engine not available
   - Storage limit exceeded
   - High CPU usage
   - High latency (>3s)
   - Camera connection keeps dropping
   - Configuration validation errors
   - Permission denied errors
4. Architecture diagram (docs/architecture.md) showing:
   - RTSP camera input
   - Motion detection stage
   - CoreML object detection
   - Ollama LLM inference
   - SQLite persistence
   - File logging (JSON + plaintext)
   - Storage management
5. Configuration reference (docs/configuration.md) documenting all 20+ config parameters with:
   - Parameter name
   - Data type
   - Default value
   - Valid range/options
   - Description
   - Example usage
   - Related NFRs
6. Setup script (scripts/setup.sh) automating initial setup:
   ```bash
   #!/bin/bash
   # Setup script for Local Video Recognition System
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   mkdir -p data/events logs config models
   cp config/config.example.yaml config/config.yaml
   echo "Setup complete. Edit config/config.yaml and run: python main.py --dry-run"
   ```
7. Model download script (scripts/download_models.sh) for CoreML models
8. FAQ section includes:
   - What hardware do I need?
   - How much storage does it use?
   - Can I use multiple cameras?
   - What RTSP cameras are supported?
   - How do I improve detection accuracy?
   - Can I run this on Intel Mac? (No, requires Apple Silicon)
   - How do I update Ollama models?
9. README includes badges: Python version, license, platform support
10. Documentation tested: Follow README start-to-finish on fresh Mac, verify works
11. Unit tests verify: example config is valid (can be parsed)
12. Manual test: Ask colleague unfamiliar with project to set up using only README

---

**Epic 4 Summary:**
- **9 Stories** delivering production-ready CLI interface, robust signal handling, comprehensive error management, and complete documentation
- **Vertical slices:** Each story delivers complete operational capability
- **Core value delivered:** System is professional, user-friendly, and ready for 24/7 deployment
- **Deployable:** After Epic 4, complete MVP ready for production use on Mac Mini/Studio with full documentation

---

## Rationale for Story Breakdown:

**Why 9 stories:**
- CLI foundation (4.1): Entry point and argument parsing
- Validation (4.2-4.4): 3 stories for health checks, version info, dry-run mode
- Operations (4.5-4.6): 2 stories for signal handling and runtime metrics
- Quality (4.7-4.8): 2 stories for error handling and platform checks
- Documentation (4.9): 1 story for README and guides

**Story sequencing:**
- 4.1 (CLI) first - entry point needed before other features
- 4.2 (Health checks) before 4.4 (Dry-run) - dry-run uses health checks
- 4.5 (Signals) and 4.6 (Metrics) parallel - independent concerns
- 4.7 (Errors) and 4.8 (Platform) parallel - both improve reliability
- 4.9 (Docs) last - can document complete system

**Cross-cutting concerns:**
- User experience: Clear messages, helpful guidance, professional polish
- Reliability: Graceful shutdown, error recovery, platform validation
- Operations: Health checks, metrics, monitoring, troubleshooting
- Documentation: README requirements (NFR16), setup instructions, examples

---
