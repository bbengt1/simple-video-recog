# Requirements

## Functional Requirements

### Input & Camera Management

**FR1:** The system SHALL connect to a single RTSP camera stream using configurable URL, username, password, and connection parameters defined in YAML configuration

**FR2:** The system SHALL capture video frames from the RTSP stream continuously without requiring manual intervention

### Motion Detection & Frame Processing

**FR3:** The system SHALL implement motion detection using OpenCV background subtraction to identify frames with significant changes from baseline

**FR4:** The system SHALL filter out static frames where motion detection confidence is below a configurable threshold

**FR5:** The system SHALL support configurable frame sampling rate (e.g., "process every Nth frame") to optimize performance vs. coverage tradeoff

### Object Detection (CoreML)

**FR6:** The system SHALL perform object detection on motion-triggered frames using CoreML models optimized for Apple Neural Engine

**FR7:** The system SHALL support configurable object blacklisting to exclude specific object types from processing (e.g., "cats", "trees")

### LLM Integration (Ollama)

**FR8:** The system SHALL integrate with local Ollama instance to perform vision language model inference on filtered frames

**FR9:** The system SHALL support configurable LLM model selection (LLaVA, Moondream, or other Ollama vision models) via YAML configuration

**FR10:** The system SHALL generate semantic event descriptions in structured JSON format containing: timestamp, detected objects (with labels and confidence scores), action description in natural language, and event location/context

### Logging & Output

**FR11:** The system SHALL log all detected events in JSON format with complete structured data for programmatic access

**FR12:** The system SHALL log all detected events in human-readable plaintext format for easy manual review

**FR13:** The system SHALL save annotated image frames with bounding boxes and labels for all detected objects

**FR14:** The system SHALL support configurable logging levels (DEBUG, INFO, WARNING, ERROR) via YAML configuration to control verbosity of console and file output

### Configuration Management

**FR15:** The system SHALL load all configuration parameters from a YAML file at startup, including camera settings, model selection, thresholds, frame sampling rate, and storage location

**FR16:** The system SHALL validate YAML configuration against a schema and provide clear error messages for invalid or missing required fields

**FR17:** The system SHALL validate YAML configuration schema at startup and exit with descriptive error messages indicating the specific field, expected format, and provided value for any validation failures

**FR18:** The system SHALL output configuration validation results in structured format showing: each parameter name, expected type/format, actual value provided, validation status (✓ valid / ✗ invalid with reason)

**FR19:** The system SHALL include an example YAML configuration file (config.example.yaml) with extensive inline comments documenting all available parameters, expected formats, and recommended default values

**FR20:** The system SHALL support hot-reload of configuration file on SIGHUP signal, reloading configurable parameters (thresholds, sampling rate, logging level, de-duplication window) without restarting the process or reconnecting to camera stream

### Startup & Initialization

**FR21:** The system SHALL load and initialize CoreML models at startup with validation that the model is compatible with Apple Neural Engine

**FR22:** The system SHALL verify Ollama service availability and selected vision model accessibility at startup before beginning stream processing

**FR23:** The system SHALL display version and build information at startup including: application version, Python version, OpenCV version, CoreML version, and Ollama client version

**FR24:** The system SHALL display a startup health check summary showing: configuration loaded successfully, CoreML model loaded and ANE-compatible, Ollama service reachable, selected vision model available, RTSP connection established, and system ready status

### Runtime Operations & Monitoring

**FR25:** The system SHALL implement event de-duplication logic to prevent multiple alerts for the same continuous event using time-based suppression windows (configurable threshold)

**FR26:** The system SHALL collect and log performance metrics including: frame processing rate, motion detection hit rate, CoreML inference time, LLM inference time, memory usage, and CPU utilization

**FR27:** The system SHALL display runtime performance metrics to console at configurable intervals (e.g., every 60 seconds) including: frames processed, events detected, average inference times, and current resource usage

### Failure Handling & Shutdown

**FR28:** The system SHALL gracefully handle RTSP connection failures with error logging and controlled shutdown

**FR29:** The system SHALL detect disk full conditions and perform graceful shutdown with clear error message (hard stop, no recovery attempt)

**FR30:** The system SHALL detect processing failures (motion detection, object recognition, LLM inference) and log stack traces with clear error messages before graceful shutdown

**FR31:** The system SHALL handle graceful shutdown on SIGINT (Ctrl+C) and SIGTERM signals by stopping stream processing, flushing logs, and releasing resources

### Command Line Interface

**FR32:** The system SHALL provide command-line help information via --help or -h flag displaying: usage syntax, configuration file parameter, dry-run mode flag, version flag, and examples

**FR33:** The system SHALL provide version information via --version or -v flag displaying: application version, build date, Python version, and key dependency versions (OpenCV, CoreML, Ollama client)

**FR34:** The system SHALL support dry-run mode via --dry-run flag that validates configuration file, checks CoreML model compatibility, verifies Ollama connectivity, tests RTSP connection, and exits with success/failure status without starting stream processing

**FR35:** The system SHALL provide command-line startup with configuration file path as parameter

## Non-Functional Requirements

**NFR1:** The system SHALL run on macOS 12+ (Monterey or newer) with Apple Silicon (M1/M2/M3) processors

**NFR2:** CoreML object detection inference SHALL complete in <100ms per frame on M1 Neural Engine

**NFR3:** LLM vision inference SHALL complete in <5 seconds per event on M1 hardware

**NFR4:** The system SHALL maintain <30% average CPU usage during continuous operation on M1 MacBook Pro

**NFR5:** The system SHALL consume <8GB RAM during normal operation with single camera stream

**NFR6:** The system SHALL detect when memory usage exceeds 8GB threshold and perform graceful shutdown with clear error message (hard stop)

**NFR7:** The system SHALL operate continuously for 24+ hours without memory leaks or crashes under normal conditions

**NFR8:** Motion detection SHALL filter out >90% of static frames to reduce LLM processing load

**NFR9:** The system SHALL process >95% of motion-triggered frames without queue overflow or dropped events

**NFR10:** Total storage for 30 days of event data (logs + annotated images) SHALL remain <4GB

**NFR11:** The system SHALL maintain M1 processor temperature <70°C during sustained operation (no thermal throttling)

**NFR12:** All dependencies SHALL be open source with zero licensing costs

**NFR13:** The system SHALL operate with 100% local processing and zero external API calls or cloud dependencies

**NFR14:** Network traffic SHALL be limited to RTSP stream from local camera (no internet connectivity required)

**NFR15:** Documentation SHALL enable a developer to run the system in <30 minutes from git clone

**NFR16:** README SHALL include the following sections with minimum content: Setup (installation steps), Configuration (parameter reference table), Architecture (component diagram + data flow), Troubleshooting (FAQ with ≥5 common issues)

**NFR17:** All code SHALL be Python 3.10+ for M1 compatibility and ML ecosystem support

**NFR18:** The system SHALL start and display health check summary within 10 seconds of launch (excluding RTSP connection time)

**NFR19:** Configuration validation in dry-run mode SHALL complete within 5 seconds

**NFR20:** Hot-reload of configuration (SIGHUP) SHALL apply changes within 2 seconds without dropping in-flight frames

**NFR21:** Graceful shutdown SHALL complete within 5 seconds, ensuring all logs are flushed and in-flight events are saved

**NFR22:** Logging and metrics collection overhead SHALL consume <5% of total CPU usage to avoid impacting processing performance

**NFR23:** The system SHALL ensure data integrity for all event logs and annotated images during graceful shutdown (no corrupted files)

**NFR24:** Minimum dependency versions SHALL be: OpenCV 4.8+, Python 3.10+, coremltools 7.0+, Ollama Python client 0.1.0+

**NFR25:** Platform-specific code (M1/CoreML/macOS APIs) SHALL be isolated in dedicated modules (e.g., platform/ directory) with abstract interfaces, enabling ≥80% of core logic to be platform-independent

**NFR26:** All signal handling (SIGINT, SIGTERM, SIGHUP) SHALL be thread-safe to prevent race conditions during shutdown or reload, verified by stress test sending 100 rapid signals with zero crashes or data corruption

**NFR27:** Frame processing queue SHALL have a maximum size of 100 frames to prevent unbounded memory growth during processing spikes

**NFR28:** Code documentation coverage SHALL be ≥80% for all public functions, classes, and modules

**NFR29:** The system SHALL include unit tests achieving ≥70% code coverage for core processing logic (motion detection, event de-duplication, configuration validation)

---

## NFR Verification & Testing

All 29 Non-Functional Requirements defined above are fully measurable and testable with clear pass/fail criteria. Comprehensive verification strategy, test cases, automation approach, and execution schedule are documented in:

**📄 [Test Plan: docs/test-plan.md](test-plan.md)**

**Test Plan Summary:**
- **27 Detailed Test Cases** covering all 29 NFRs
- **100% Automated** verification using pytest, psutil, tcpdump, and coverage tools
- **CI/CD Integration** with GitHub Actions for continuous validation
- **Test Schedule:** Per-commit (platform/security), per-PR (quality/performance), nightly (24hr longevity), weekly (chaos/stress)
- **Success Criteria:** All 29 NFRs must pass before release

**Key Test Categories:**
| Category | NFRs | Test Cases | Automation |
|----------|------|------------|------------|
| Performance | NFR2-4, 8-9, 11, 18-20, 22 | TC-PERF-001 to TC-PERF-010 | pytest benchmarks |
| Resources | NFR5-6, 10, 27 | TC-RESOURCE-001 to TC-RESOURCE-004 | Monitoring daemons |
| Reliability | NFR7, 21, 23 | TC-RELIABILITY-001 to TC-RELIABILITY-003 | Longevity tests |
| Platform | NFR1, 17, 24-25 | TC-PLATFORM-001 to TC-PLATFORM-004 | Version checks |
| Security | NFR12-14 | TC-SECURITY-001 to TC-SECURITY-003 | Network analysis |
| Quality | NFR15-16, 28-29 | TC-QUALITY-001 to TC-QUALITY-004 | Coverage tools |
| Concurrency | NFR26 | TC-CONCURRENCY-001 | Stress testing |

**Critical NFRs (Must Pass for Release):**
- NFR2, NFR3: Inference speed targets (CoreML <100ms, LLM <5s)
- NFR4, NFR5: Resource limits (CPU <30%, RAM <8GB)
- NFR7: 24hr uptime without crashes
- NFR13: 100% local processing verification
- NFR29: Test coverage ≥70%

See [test-plan.md](test-plan.md) for complete test case details, automation scripts, and CI/CD configuration.

---
