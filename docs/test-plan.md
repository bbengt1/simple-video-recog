# Test Plan: Local Video Recognition System

**Version:** 1.0
**Date:** 2025-11-08
**PRD Version:** 1.0
**Status:** Draft

---

## 1. Overview

### 1.1 Purpose

This test plan defines the verification strategy for all Non-Functional Requirements (NFRs) specified in the Local Video Recognition System PRD. It establishes measurable criteria, test methods, tools, and automation strategies to validate that the MVP meets all performance, reliability, security, and quality standards.

### 1.2 Scope

**In Scope:**
- Verification of all 29 Non-Functional Requirements (NFR1-NFR29)
- Performance testing (inference speed, throughput, resource usage)
- Reliability testing (uptime, data integrity, graceful shutdown)
- Security testing (network isolation, dependency licensing)
- Documentation and code quality validation
- Platform compatibility and portability verification
- Concurrency and thread safety testing

**Out of Scope:**
- Functional requirements testing (covered by unit/integration tests)
- User acceptance testing (solo developer, no formal UAT)
- Load testing beyond single camera (multi-camera is Phase 2)
- Cross-platform testing (MVP is macOS M1 only)

### 1.3 Test Objectives

1. **Validate Performance:** Ensure all performance NFRs (NFR2-4, NFR8-9, NFR11, NFR18-20, NFR22) meet specified thresholds
2. **Verify Resource Constraints:** Confirm system operates within memory, CPU, storage, and queue limits (NFR5-6, NFR10, NFR27)
3. **Prove Reliability:** Demonstrate 24hr uptime, graceful shutdown, and data integrity (NFR7, NFR21, NFR23)
4. **Confirm Platform Compatibility:** Validate macOS M1 requirement and dependency versions (NFR1, NFR17, NFR24-25)
5. **Ensure Privacy:** Verify 100% local processing with no external calls (NFR12-14)
6. **Assess Quality:** Measure documentation and test coverage (NFR15-16, NFR28-29)
7. **Test Concurrency:** Stress test signal handling for thread safety (NFR26)

---

## 2. Test Environment

### 2.1 Hardware Requirements

**Primary Test Platform:**
- MacBook Pro 16" (2021)
- Apple M1 Pro chip
- 16GB Unified Memory
- 256GB SSD (test storage constraints)
- macOS 13.0 (Ventura) or later

**Test Camera:**
- RTSP-compatible IP camera (1080p @ 15fps minimum)
- Stable network connection
- Test scenarios: indoor, outdoor, day/night

### 2.2 Software Requirements

**Base System:**
- Python 3.10+
- OpenCV 4.8+
- coremltools 7.0+
- Ollama 0.1.0+ with LLaVA or Moondream model

**Test Tools:**
- pytest 7.0+
- pytest-cov (code coverage)
- interrogate (documentation coverage)
- psutil (system monitoring)
- tcpdump / Wireshark (network analysis)
- pip-licenses (dependency licensing)
- powermetrics (macOS thermal monitoring)

### 2.3 Test Data

**Sample RTSP Streams:**
- Indoor camera: low motion (office/home)
- Outdoor camera: high motion (street/driveway)
- Test videos: known event sequences for validation

**Test Configurations:**
- Baseline config (recommended defaults)
- High-sensitivity config (low motion threshold)
- Performance config (aggressive frame sampling)
- Stress config (maximum processing load)

---

## 3. Test Strategy by Category

### 3.1 Performance Testing (10 NFRs)

**Approach:** Automated benchmarking with statistical analysis

| NFR | Test Method | Sample Size | Success Criteria |
|-----|-------------|-------------|------------------|
| NFR2 | CoreML inference timing | 100 frames | Average <100ms |
| NFR3 | LLM inference timing | 50 events | 95th percentile <5s |
| NFR4 | CPU monitoring (psutil) | 8,640 samples (24hr @ 10s) | Average <30% |
| NFR8 | Motion detection ratio | 10,000 frames | >90% filtered |
| NFR9 | Frame processing ratio | 24hr test | >95% processed |
| NFR11 | Thermal monitoring (powermetrics) | 24hr continuous | Max <70°C |
| NFR18 | Startup timing | 10 runs | All <10s |
| NFR19 | Dry-run timing | 10 runs | All <5s |
| NFR20 | Hot-reload timing | 20 reloads | All <2s, zero drops |
| NFR22 | Logging overhead comparison | 1hr with/without | <5% delta |

**Automation:** pytest performance test suite, nightly CI/CD execution

### 3.2 Resource Constraint Testing (4 NFRs)

**Approach:** Continuous monitoring with threshold alarms

| NFR | Test Method | Duration | Success Criteria |
|-----|-------------|----------|------------------|
| NFR5 | Memory profiling (psutil) | 24hr | Peak <8GB |
| NFR6 | Memory stress test | Until trigger | Graceful shutdown at >8GB |
| NFR10 | Storage simulation | 30-day event sim | Total <4GB |
| NFR27 | Queue size monitoring | Load spike test | Never exceeds 100 frames |

**Automation:** Resource monitoring daemon, alerting on threshold violations

### 3.3 Reliability Testing (3 NFRs)

**Approach:** Longevity testing with failure injection

| NFR | Test Method | Duration | Success Criteria |
|-----|-------------|----------|------------------|
| NFR7 | 24hr continuous run | 24hr+ | Zero crashes, memory leaks |
| NFR21 | Graceful shutdown timing | 100 shutdown tests | All <5s, logs intact |
| NFR23 | Data integrity on crash | Random SIGINT during write | Zero corrupted files |

**Automation:** Chaos engineering framework, nightly longevity tests

### 3.4 Platform & Compatibility Testing (4 NFRs)

**Approach:** Static analysis and version checks

| NFR | Test Method | Frequency | Success Criteria |
|-----|-------------|-----------|------------------|
| NFR1 | Platform detection test | Per-commit | Fails on non-macOS/non-M1 |
| NFR17 | Python version check | Per-commit | Fails on Python <3.10 |
| NFR24 | Dependency version audit | Per-PR | All dependencies ≥ minimums |
| NFR25 | Code portability analysis | Per-PR | ≥80% platform-independent |

**Automation:** Pre-commit hooks, CI/CD pipeline checks

### 3.5 Security & Privacy Testing (3 NFRs)

**Approach:** Network traffic analysis and license auditing

| NFR | Test Method | Duration | Success Criteria |
|-----|-------------|----------|------------------|
| NFR12 | License scanner (pip-licenses) | Per-PR | All licenses OSS |
| NFR13 | Network packet capture (tcpdump) | 10min operation | Zero non-RTSP traffic |
| NFR14 | Connection analysis (lsof -i) | Runtime inspection | RTSP to camera IP only |

**Automation:** CI/CD security scan, runtime network monitoring

### 3.6 Documentation & Quality Testing (3 NFRs)

**Approach:** Static analysis and coverage measurement

| NFR | Test Method | Frequency | Success Criteria |
|-----|-------------|-----------|------------------|
| NFR15 | Fresh setup timing | Per-release | Complete <30min |
| NFR16 | README section validation | Per-PR | All required sections present |
| NFR28 | Documentation coverage (interrogate) | Per-PR | ≥80% coverage |
| NFR29 | Code coverage (pytest-cov) | Per-commit | ≥70% for core logic |

**Automation:** Documentation linter, coverage reporting in CI/CD

### 3.7 Concurrency Testing (1 NFR)

**Approach:** Stress testing with rapid signal delivery

| NFR | Test Method | Iterations | Success Criteria |
|-----|-------------|------------|------------------|
| NFR26 | Signal stress test | 100 rapid signals | Zero crashes, corruption |

**Automation:** Weekly chaos testing, manual verification

---

## 4. Detailed Test Cases

### 4.1 Performance Test Cases

#### TC-PERF-001: CoreML Inference Speed (NFR2)

**Objective:** Verify CoreML object detection completes in <100ms per frame on M1 Neural Engine

**Prerequisites:**
- CoreML model loaded and ANE-compatible verified
- Test frame dataset (100 frames, 1080p resolution)

**Test Steps:**
1. Load CoreML object detection model
2. Verify model is running on Apple Neural Engine (not CPU/GPU)
3. For each of 100 test frames:
   - Record start time (time.perf_counter())
   - Execute model.predict(frame)
   - Record end time
   - Calculate inference time
4. Calculate average, median, and 95th percentile inference times
5. Log all timing data for analysis

**Expected Results:**
- Average inference time <100ms
- 95th percentile inference time <120ms (some variance acceptable)
- All inferences complete successfully without errors

**Pass/Fail Criteria:** Average <100ms AND zero inference errors

**Automation:** pytest test_coreml_inference_speed()

---

#### TC-PERF-002: LLM Inference Speed (NFR3)

**Objective:** Verify LLM vision inference completes in <5s per event on M1

**Prerequisites:**
- Ollama service running with LLaVA or Moondream model
- Test event dataset (50 annotated frames with ground truth)

**Test Steps:**
1. Connect to Ollama service
2. Verify selected vision model is loaded
3. For each of 50 test frames:
   - Record start time
   - Send frame to LLM with standard prompt
   - Wait for structured JSON response
   - Record end time
   - Calculate inference time
4. Calculate average, median, 95th percentile times
5. Log all timing data and response quality

**Expected Results:**
- Average inference time <4s
- 95th percentile <5s
- All responses in valid JSON format
- Semantic descriptions are accurate (manual spot-check 10 samples)

**Pass/Fail Criteria:** 95th percentile <5s AND all responses valid JSON

**Automation:** pytest test_llm_inference_speed()

---

#### TC-PERF-003: CPU Usage During 24hr Operation (NFR4)

**Objective:** Verify average CPU usage <30% during continuous 24hr operation

**Prerequisites:**
- System configured with baseline config
- RTSP camera streaming at 1080p/15fps
- psutil library installed for monitoring

**Test Steps:**
1. Start system with baseline configuration
2. Begin CPU monitoring (psutil.cpu_percent(interval=10))
3. Sample CPU usage every 10 seconds for 24 hours (8,640 samples)
4. Store all samples with timestamps
5. After 24 hours, calculate:
   - Average CPU usage
   - Peak CPU usage
   - 95th percentile CPU usage
6. Generate CPU usage timeline graph

**Expected Results:**
- Average CPU usage <30%
- No sustained periods (>5 min) of CPU >50%
- System remains responsive throughout

**Pass/Fail Criteria:** Average CPU <30% over 24hr period

**Automation:** pytest test_cpu_usage_24hr() (nightly execution)

---

#### TC-PERF-004: Motion Detection Filter Rate (NFR8)

**Objective:** Verify motion detection filters >90% of static frames

**Prerequisites:**
- Test video with known motion characteristics:
  - 1,000 frames with zero motion (static scene)
  - 1,000 frames with slight motion (shadows, leaves)
  - 1,000 frames with significant motion (person walking)
- Motion detection configured with baseline threshold

**Test Steps:**
1. Process test video through motion detection
2. Count frames marked as:
   - Static (no motion detected)
   - Motion (motion detected above threshold)
3. Calculate filter rate: static_frames / total_frames
4. Verify accuracy:
   - >95% of truly static frames marked static
   - >90% of motion frames detected
5. Log false positive/negative rates

**Expected Results:**
- Filter rate >90% for static frames
- Motion detection accuracy >90%
- False positive rate <10%

**Pass/Fail Criteria:** Filter rate >90% AND false positives <10%

**Automation:** pytest test_motion_detection_filter_rate()

---

#### TC-PERF-005: Frame Processing Throughput (NFR9)

**Objective:** Verify >95% of motion-triggered frames are processed without drops

**Prerequisites:**
- System running with baseline config
- Test scenario: moderate motion activity (1 event per minute)
- 24hr test duration

**Test Steps:**
1. Start system with metrics collection enabled
2. Run for 24 hours
3. Track metrics:
   - Frames with motion detected
   - Frames queued for processing
   - Frames successfully processed
   - Frames dropped (queue overflow)
4. Calculate: processed_rate = processed / motion_detected
5. Log any queue overflow events

**Expected Results:**
- >95% of motion-triggered frames processed
- Queue overflow events <5% of total
- Zero lost events (all logged or processed)

**Pass/Fail Criteria:** Processed rate >95%

**Automation:** pytest test_frame_processing_throughput() (nightly)

---

#### TC-PERF-006: Thermal Management (NFR11)

**Objective:** Verify M1 processor temperature <70°C during sustained operation

**Prerequisites:**
- macOS powermetrics tool available (sudo access required)
- System running with high processing load configuration
- Ambient temperature 20-25°C

**Test Steps:**
1. Start temperature monitoring: `sudo powermetrics --samplers smc -i 5000`
2. Start system with high-load config (low motion threshold, every frame)
3. Monitor CPU package temperature every 5 seconds for 24 hours
4. Track:
   - Peak temperature
   - Average temperature
   - Time spent >65°C
5. Check for thermal throttling events in system logs

**Expected Results:**
- Peak temperature <70°C
- Average temperature <60°C
- Zero thermal throttling events
- Fan speed remains reasonable (not constant max)

**Pass/Fail Criteria:** Peak temperature <70°C AND zero throttling events

**Automation:** pytest test_thermal_management() with sudo privileges (nightly)

---

#### TC-PERF-007: Startup Time (NFR18)

**Objective:** Verify system starts and displays health check within 10s

**Prerequisites:**
- All dependencies installed
- Ollama service pre-started
- CoreML model already downloaded
- RTSP camera online

**Test Steps:**
1. For each of 10 test runs:
   - Record start time
   - Execute: `python main.py config.yaml`
   - Wait for "System ready" message in stdout
   - Record end time (excluding RTSP connection establishment)
   - Calculate startup time
2. Calculate average and maximum startup times
3. Identify slowest component (model loading, Ollama check, config validation)

**Expected Results:**
- All 10 runs complete <10s
- Average startup time <8s
- Startup time variance <2s (consistent performance)

**Pass/Fail Criteria:** All 10 runs <10s

**Automation:** pytest test_startup_time()

---

#### TC-PERF-008: Dry-Run Mode Performance (NFR19)

**Objective:** Verify dry-run validation completes within 5s

**Prerequisites:**
- Valid configuration file
- All dependencies installed
- Ollama service running

**Test Steps:**
1. For each of 10 test runs:
   - Record start time
   - Execute: `python main.py --dry-run config.yaml`
   - Wait for exit (success or failure)
   - Record end time
2. Verify dry-run validates:
   - Configuration schema
   - CoreML model compatibility
   - Ollama connectivity
   - RTSP camera reachability
3. Calculate average execution time

**Expected Results:**
- All 10 runs complete <5s
- All validation checks execute
- Exit code 0 for valid config, non-zero for invalid

**Pass/Fail Criteria:** All runs <5s AND all checks execute

**Automation:** pytest test_dry_run_performance()

---

#### TC-PERF-009: Configuration Hot-Reload (NFR20)

**Objective:** Verify hot-reload applies changes within 2s without dropping frames

**Prerequisites:**
- System running and processing frames
- Baseline configuration loaded
- Frame processing metrics enabled

**Test Steps:**
1. Start system with baseline config
2. Wait for steady-state operation (5 minutes)
3. For each of 20 reload tests:
   - Modify config parameter (e.g., motion_threshold, logging_level)
   - Record frame processing count before reload
   - Send SIGHUP signal
   - Record time until config applied (check via logs)
   - Record frame processing count after reload
   - Verify no frames dropped during reload
4. Calculate average reload time
5. Verify all config changes took effect

**Expected Results:**
- All 20 reloads complete <2s
- Zero frames dropped during any reload
- All configuration changes applied correctly
- System continues processing without interruption

**Pass/Fail Criteria:** All reloads <2s AND zero dropped frames

**Automation:** pytest test_hot_reload_performance()

---

#### TC-PERF-010: Logging Overhead (NFR22)

**Objective:** Verify logging/metrics collection adds <5% CPU overhead

**Prerequisites:**
- Two identical test configurations (with/without logging)
- 1hr test duration for each

**Test Steps:**
1. **Test A: Full logging enabled**
   - Set logging level: DEBUG
   - Enable all metrics collection
   - Run for 1 hour
   - Record average CPU usage
2. **Test B: Minimal logging**
   - Set logging level: ERROR
   - Disable metrics collection
   - Run for 1 hour with same RTSP stream
   - Record average CPU usage
3. Calculate overhead: (CPU_A - CPU_B) / CPU_B * 100
4. Verify log file I/O doesn't cause processing delays

**Expected Results:**
- CPU overhead <5%
- No correlation between log writes and processing latency
- Logging doesn't cause frame drops

**Pass/Fail Criteria:** CPU overhead <5%

**Automation:** pytest test_logging_overhead()

---

### 4.2 Resource Constraint Test Cases

#### TC-RESOURCE-001: Memory Usage Limit (NFR5)

**Objective:** Verify system consumes <8GB RAM during normal 24hr operation

**Prerequisites:**
- Fresh system start (no memory leaks from previous runs)
- Baseline configuration
- psutil for memory monitoring

**Test Steps:**
1. Start system with memory tracking enabled
2. Sample memory usage every 30 seconds for 24 hours
3. Track:
   - RSS (Resident Set Size)
   - VMS (Virtual Memory Size)
   - Peak memory usage
   - Memory growth rate
4. Generate memory timeline graph
5. Check for memory leaks (linear growth over time)

**Expected Results:**
- Peak RSS <8GB
- No continuous memory growth (leaks)
- Memory usage stabilizes after initial startup
- Garbage collection runs periodically

**Pass/Fail Criteria:** Peak RSS <8GB over 24hr

**Automation:** pytest test_memory_usage_limit() (nightly)

---

#### TC-RESOURCE-002: Memory Limit Shutdown Trigger (NFR6)

**Objective:** Verify system detects >8GB memory usage and triggers graceful shutdown

**Prerequisites:**
- Modified configuration that forces high memory usage
- Memory stress injection capability

**Test Steps:**
1. Start system with memory monitoring
2. Inject memory stress:
   - Gradually allocate large numpy arrays
   - Force frame queue growth
   - Simulate memory leak
3. Monitor system behavior as memory approaches 8GB threshold
4. Verify system:
   - Detects memory threshold exceeded
   - Logs clear error message
   - Initiates graceful shutdown
   - Flushes all logs before exit
5. Verify exit code indicates memory limit error

**Expected Results:**
- System detects memory >8GB
- Clear error message: "Memory limit exceeded (8.2GB > 8GB), shutting down gracefully"
- All logs flushed before exit
- No corrupted files
- Exit code indicates memory error (distinct from other errors)

**Pass/Fail Criteria:** Graceful shutdown triggered at >8GB with clear error

**Automation:** pytest test_memory_limit_shutdown()

---

#### TC-RESOURCE-003: 30-Day Storage Constraint (NFR10)

**Objective:** Verify 30 days of event data consumes <4GB storage

**Prerequisites:**
- Baseline event frequency assumptions:
  - 10 events per day (moderate activity)
  - Each event generates: JSON log (~2KB) + annotated image (~500KB)
- Storage calculation: 10 events/day * 30 days * 502KB = ~150MB

**Test Steps:**
1. Simulate 30 days of events:
   - Generate 300 test events (10/day * 30 days)
   - Each event creates JSON log + annotated image
2. Store all events in data/events directory
3. Calculate total storage: `du -sh data/events`
4. Verify storage breakdown:
   - JSON logs total size
   - Annotated images total size
   - Any additional metadata
5. Extrapolate for high-activity scenario (50 events/day)

**Expected Results:**
- Baseline scenario (10 events/day): <1GB
- High-activity scenario (50 events/day): <4GB
- JSON logs are efficiently formatted (no bloat)
- Images are compressed appropriately

**Pass/Fail Criteria:** 50 events/day * 30 days <4GB

**Automation:** pytest test_storage_30days()

---

#### TC-RESOURCE-004: Frame Queue Size Limit (NFR27)

**Objective:** Verify frame processing queue never exceeds 100 frames

**Prerequisites:**
- Queue size monitoring enabled
- Stress test configuration (low motion threshold, high frame rate)

**Test Steps:**
1. Start system with queue monitoring
2. Simulate processing spike:
   - Temporarily slow down CoreML inference (artificial delay)
   - Increase motion detection sensitivity (more frames queued)
   - Monitor queue size in real-time
3. Track:
   - Peak queue size
   - Queue size distribution over time
   - Frames dropped when queue full
4. Verify queue limit enforcement:
   - New frames rejected when queue = 100
   - Dropped frames logged appropriately
5. Remove artificial delay and verify queue drains

**Expected Results:**
- Queue size never exceeds 100 frames
- Frames dropped when queue full (logged)
- Queue drains when processing catches up
- No memory leaks from queue management

**Pass/Fail Criteria:** Max queue size = 100 frames

**Automation:** pytest test_frame_queue_limit()

---

### 4.3 Reliability Test Cases

#### TC-RELIABILITY-001: 24hr Continuous Uptime (NFR7)

**Objective:** Verify system operates continuously for 24+ hours without crashes or memory leaks

**Prerequisites:**
- Fresh system start
- Baseline configuration
- RTSP camera with stable connection
- Monitoring dashboard for real-time status

**Test Steps:**
1. Start system with full monitoring enabled
2. Run for minimum 24 hours
3. Monitor every hour:
   - Process is running (ps aux | grep main.py)
   - Memory usage (check for growth)
   - CPU usage (check for spikes)
   - Event detection rate (verify processing continues)
   - Log file growth (verify logging works)
4. After 24 hours:
   - Verify process is still running
   - Check logs for errors or warnings
   - Analyze memory timeline for leaks
   - Review all processed events for quality

**Expected Results:**
- Process runs for 24+ hours without exit
- No memory leaks (stable memory usage)
- Continuous event processing throughout
- No error spikes or anomalies
- System remains responsive

**Pass/Fail Criteria:** Process running after 24hr AND no memory growth >10%

**Automation:** pytest test_24hr_uptime() (scheduled nightly)

---

#### TC-RELIABILITY-002: Graceful Shutdown Timing (NFR21)

**Objective:** Verify graceful shutdown completes within 5s with all logs flushed

**Prerequisites:**
- System running and processing events
- Multiple in-flight events (frame processing, LLM inference)
- Log files open for writing

**Test Steps:**
1. Start system and let it process events for 5 minutes
2. For each of 100 shutdown tests:
   - Send SIGINT signal
   - Start timer
   - Monitor shutdown process:
     - Frame processing stops
     - LLM requests complete or abort
     - Logs flushed to disk
     - Resources released
     - Process exits
   - Stop timer
   - Record shutdown time
3. After each test:
   - Verify all log files valid (no truncation)
   - Verify all event images complete
   - Check for resource leaks (temp files, open connections)
4. Calculate average shutdown time and variance

**Expected Results:**
- All 100 tests complete <5s
- Average shutdown time <3s
- All logs intact and readable
- All event data saved
- No orphaned resources

**Pass/Fail Criteria:** All 100 tests <5s AND zero data loss

**Automation:** pytest test_graceful_shutdown_timing()

---

#### TC-RELIABILITY-003: Data Integrity on Shutdown (NFR23)

**Objective:** Verify no corrupted files when shutdown occurs during active writes

**Prerequisites:**
- System actively processing and logging events
- Ability to send SIGINT at random times
- File integrity validation tools

**Test Steps:**
1. Start system with event processing
2. For each of 50 chaos tests:
   - Wait random time (1-60 seconds)
   - Send SIGINT during active processing
   - Wait for shutdown to complete
   - Verify data integrity:
     - All JSON files are valid (json.load() succeeds)
     - All image files are complete (PIL.Image.open() succeeds)
     - No .tmp or partial files left behind
     - Log files are complete (no mid-line truncation)
3. Attempt to parse every JSON file
4. Attempt to load every image file
5. Verify event counts match log entries

**Expected Results:**
- Zero corrupted JSON files
- Zero corrupted image files
- All logs are complete
- No orphaned temporary files
- Event counts are consistent

**Pass/Fail Criteria:** Zero corrupted files in all 50 tests

**Automation:** pytest test_shutdown_data_integrity()

---

### 4.4 Platform & Compatibility Test Cases

#### TC-PLATFORM-001: Platform Detection (NFR1)

**Objective:** Verify system only runs on macOS 12+ with Apple Silicon

**Prerequisites:**
- Test environments:
  - macOS 13 on M1 (should pass)
  - macOS 11 on M1 (should fail - version too old)
  - macOS 13 on Intel (should fail - wrong architecture)
  - Linux (should fail - wrong OS)

**Test Steps:**
1. Implement platform detection in main.py startup
2. Test on macOS 13 M1:
   - System should start normally
   - No platform warnings
3. Test on macOS 11 M1:
   - System should exit with clear error
   - Error: "macOS 12+ required, detected: 11.x"
4. Test on macOS 13 Intel:
   - System should exit with clear error
   - Error: "Apple Silicon (M1/M2/M3) required, detected: x86_64"
5. Test on Linux:
   - System should exit with clear error
   - Error: "macOS required, detected: Linux"

**Expected Results:**
- Passes only on macOS 12+ with arm64 architecture
- Clear error messages for incompatible platforms
- Exit code indicates platform incompatibility

**Pass/Fail Criteria:** Runs only on macOS 12+ M1/M2/M3

**Automation:** pytest test_platform_detection() (CI/CD with matrix)

---

#### TC-PLATFORM-002: Python Version Check (NFR17)

**Objective:** Verify system requires Python 3.10+

**Prerequisites:**
- Test environments with Python 3.9, 3.10, 3.11, 3.12

**Test Steps:**
1. Test with Python 3.9:
   - System should exit with error
   - Error: "Python 3.10+ required, detected: 3.9.x"
2. Test with Python 3.10:
   - System should start normally
3. Test with Python 3.11 and 3.12:
   - System should start normally
   - Verify all features work

**Expected Results:**
- Fails on Python <3.10
- Passes on Python ≥3.10
- Clear error message for version mismatch

**Pass/Fail Criteria:** Runs only on Python 3.10+

**Automation:** pytest test_python_version() with tox multi-version

---

#### TC-PLATFORM-003: Dependency Version Audit (NFR24)

**Objective:** Verify all dependencies meet minimum version requirements

**Prerequisites:**
- requirements.txt with minimum versions specified
- Dependency audit tools (pip list, pkg_resources)

**Test Steps:**
1. Parse requirements.txt for minimum versions:
   - OpenCV >= 4.8.0
   - Python >= 3.10
   - coremltools >= 7.0.0
   - ollama >= 0.1.0
2. Check installed versions:
   ```python
   import cv2, coremltools, ollama
   assert cv2.__version__ >= '4.8.0'
   assert coremltools.__version__ >= '7.0.0'
   assert ollama.__version__ >= '0.1.0'
   ```
3. Test with older versions:
   - Install OpenCV 4.7 → should fail with clear error
   - Install coremltools 6.x → should fail
4. Generate dependency report

**Expected Results:**
- All dependencies meet minimum versions
- Clear error if any dependency is too old
- requirements.txt accurately reflects minimums

**Pass/Fail Criteria:** All dependencies meet specified minimums

**Automation:** pytest test_dependency_versions() (CI/CD)

---

#### TC-PLATFORM-004: Code Portability Analysis (NFR25)

**Objective:** Verify ≥80% of core logic is platform-independent

**Prerequisites:**
- Code analysis tools (sloccount, radon)
- Clear directory structure (core/, platform/, utils/)

**Test Steps:**
1. Count total lines of code:
   - Core logic: `sloccount core/`
   - Platform-specific: `sloccount platform/`
   - Utils: `sloccount utils/`
2. Identify platform-specific imports:
   - Search for: `import coremltools`, `platform.mac_ver()`, macOS-specific APIs
3. Verify platform-specific code is isolated:
   - All CoreML code in platform/coreml_detector.py
   - All macOS-specific code in platform/ directory
   - Core logic uses abstract interfaces
4. Calculate portability ratio:
   - platform_independent = (total - platform_specific) / total
5. Verify ratio ≥ 80%

**Expected Results:**
- Platform-specific code isolated in platform/ directory
- Core logic uses dependency injection for platform components
- ≥80% of codebase is portable
- Clear abstraction layers (e.g., ObjectDetector interface)

**Pass/Fail Criteria:** ≥80% of code is platform-independent

**Automation:** pytest test_code_portability() with code analysis

---

### 4.5 Security & Privacy Test Cases

#### TC-SECURITY-001: Open Source License Compliance (NFR12)

**Objective:** Verify all dependencies use open source licenses

**Prerequisites:**
- pip-licenses tool installed
- List of acceptable licenses (MIT, Apache, BSD, GPL, LGPL)

**Test Steps:**
1. Run license scanner:
   ```bash
   pip-licenses --format=json --with-urls > licenses.json
   ```
2. Parse licenses.json
3. For each dependency:
   - Verify license is in approved list
   - Flag any proprietary or unknown licenses
4. Generate license compliance report
5. Verify no commercial dependencies

**Expected Results:**
- All dependencies have OSS licenses
- No proprietary or commercial licenses
- No "UNKNOWN" licenses
- License report available for audit

**Pass/Fail Criteria:** All dependencies have approved OSS licenses

**Automation:** pytest test_license_compliance() (CI/CD, PR check)

---

#### TC-SECURITY-002: Network Isolation - Zero External Calls (NFR13)

**Objective:** Verify 100% local processing with zero external API calls

**Prerequisites:**
- tcpdump or Wireshark for packet capture
- System running with real camera feed
- Internet connectivity available (to detect if system tries to use it)

**Test Steps:**
1. Start network capture:
   ```bash
   sudo tcpdump -i any -w test_capture.pcap
   ```
2. Start system and run for 10 minutes
3. Process events and generate logs
4. Stop network capture
5. Analyze captured packets:
   - Filter for non-local traffic (destination not 127.0.0.1, 192.168.x.x)
   - Identify all destination IPs and ports
   - Verify only RTSP traffic to camera IP
6. Check for:
   - No DNS queries (except initial Ollama localhost resolution)
   - No HTTP/HTTPS requests
   - No cloud API calls
   - No telemetry or analytics

**Expected Results:**
- Only RTSP traffic to camera IP address
- Localhost communication (Ollama on 127.0.0.1:11434)
- Zero external network calls
- No DNS queries for external domains

**Pass/Fail Criteria:** Zero non-local network traffic (except RTSP)

**Automation:** pytest test_network_isolation() with packet analysis

---

#### TC-SECURITY-003: RTSP-Only Network Traffic (NFR14)

**Objective:** Verify network traffic is limited to RTSP stream from camera

**Prerequisites:**
- Network monitoring tools (lsof, netstat, tcpdump)
- RTSP camera on known IP (e.g., 192.168.1.100)

**Test Steps:**
1. Start system
2. Monitor active connections:
   ```bash
   lsof -i -P -n | grep python
   ```
3. Verify only connections are:
   - RTSP to camera (192.168.1.100:554)
   - Localhost Ollama (127.0.0.1:11434)
4. Capture detailed packet analysis:
   - Protocol: RTSP (port 554)
   - Destination: Camera IP only
   - No unexpected ports or protocols
5. Verify no internet requirement:
   - Disconnect internet (keep local network)
   - System continues operating normally

**Expected Results:**
- Only 2 connections: RTSP + localhost Ollama
- RTSP traffic to camera IP:554
- System works without internet connectivity
- No unexpected network activity

**Pass/Fail Criteria:** Only RTSP to camera + localhost Ollama

**Automation:** pytest test_rtsp_only_traffic()

---

### 4.6 Documentation & Quality Test Cases

#### TC-QUALITY-001: Setup Time from Git Clone (NFR15)

**Objective:** Verify developer can run system in <30 minutes from git clone

**Prerequisites:**
- Fresh macOS M1 machine (or VM reset)
- Internet connectivity
- Git, Python 3.10+ pre-installed
- Test user following only README instructions

**Test Steps:**
1. Start timer
2. Clone repository:
   ```bash
   git clone https://github.com/user/video-recognition.git
   cd video-recognition
   ```
3. Follow README setup instructions only (no external help)
4. Complete all steps:
   - Install dependencies
   - Download/install Ollama
   - Download CoreML models
   - Configure config.yaml with camera
   - Run dry-run mode
   - Start system
   - Verify first event detection
5. Stop timer
6. Record any issues or unclear instructions

**Expected Results:**
- Complete setup <30 minutes
- README instructions are clear and complete
- All dependencies install without errors
- First detection successful
- No need for external documentation

**Pass/Fail Criteria:** Complete setup <30 minutes following README only

**Automation:** Manual test per release, documented in QA checklist

---

#### TC-QUALITY-002: README Completeness (NFR16)

**Objective:** Verify README contains all required sections with minimum content

**Prerequisites:**
- README.md in repository root
- Section validation script

**Test Steps:**
1. Verify README contains required sections:
   - **Setup:** Installation steps present
   - **Configuration:** Parameter reference table present
   - **Architecture:** Component diagram + data flow present
   - **Troubleshooting:** FAQ with ≥5 common issues
2. For each section, verify minimum content:
   - Setup: Step-by-step installation commands
   - Configuration: Table with parameter, type, description, default
   - Architecture: Diagram (ASCII or image) + explanation
   - Troubleshooting: At least 5 Q&A entries
3. Check for clarity and completeness:
   - Code examples are syntax-highlighted
   - Links are valid (no 404s)
   - Screenshots/diagrams are clear

**Expected Results:**
- All 4 required sections present
- Each section meets minimum content requirements
- Troubleshooting has ≥5 FAQ items
- All links are valid
- Code examples are accurate

**Pass/Fail Criteria:** All sections present with required content

**Automation:** pytest test_readme_completeness() (CI/CD, PR check)

---

#### TC-QUALITY-003: Documentation Coverage (NFR28)

**Objective:** Verify ≥80% of public functions/classes are documented

**Prerequisites:**
- interrogate tool installed
- Code follows docstring conventions (Google or NumPy style)

**Test Steps:**
1. Run documentation coverage analysis:
   ```bash
   interrogate -v -i --fail-under=80 .
   ```
2. Generate detailed report:
   - Total functions/classes
   - Documented count
   - Undocumented count
   - Coverage percentage
3. Identify undocumented functions:
   ```bash
   interrogate --generate-badge badges -vv
   ```
4. Review undocumented items:
   - Are they private (underscore prefix)? Exclude from count
   - Are they trivial (getters/setters)? Still need brief docstring
5. Verify docstring quality (sample review):
   - Includes purpose/description
   - Documents parameters and return values
   - Includes usage examples where helpful

**Expected Results:**
- Overall coverage ≥80%
- All public functions documented
- Docstrings include params and returns
- Quality spot-check passes (clear, accurate)

**Pass/Fail Criteria:** interrogate reports ≥80% coverage

**Automation:** pytest test_documentation_coverage() (CI/CD, PR check)

---

#### TC-QUALITY-004: Code Test Coverage (NFR29)

**Objective:** Verify ≥70% test coverage for core processing logic

**Prerequisites:**
- pytest-cov installed
- Comprehensive unit test suite
- Core logic identified: core/ directory

**Test Steps:**
1. Run test suite with coverage:
   ```bash
   pytest --cov=core --cov-report=html --cov-report=term-missing
   ```
2. Analyze coverage report:
   - Overall core/ coverage percentage
   - Per-file coverage breakdown
   - Identify uncovered lines
3. Review uncovered code:
   - Is it error handling (hard to test)? Document why untested
   - Is it platform-specific (requires M1)? Note in report
   - Is it trivial (simple getters)? Still aim to cover
4. Verify critical paths are covered:
   - Motion detection logic: 100% coverage
   - Event de-duplication: 100% coverage
   - Configuration validation: 100% coverage
5. Generate coverage badge for README

**Expected Results:**
- Core logic coverage ≥70%
- Critical paths covered 100%
- Coverage report generated (HTML)
- Uncovered lines documented with reason

**Pass/Fail Criteria:** pytest-cov reports ≥70% for core/

**Automation:** pytest test_code_coverage() (CI/CD, PR check)

---

### 4.7 Concurrency Test Cases

#### TC-CONCURRENCY-001: Signal Handling Stress Test (NFR26)

**Objective:** Verify thread-safe signal handling with 100 rapid signals

**Prerequisites:**
- System running and processing events
- Signal stress test script
- Concurrent event processing active

**Test Steps:**
1. Start system with active processing
2. Wait for steady state (5 minutes)
3. Launch signal stress test:
   ```python
   import signal, random, time, os

   for i in range(100):
       sig = random.choice([signal.SIGHUP, signal.SIGINT, signal.SIGTERM])
       os.kill(process_pid, sig)
       time.sleep(random.uniform(0.01, 0.1))  # Rapid firing
   ```
4. Monitor system behavior:
   - Process remains running or exits cleanly
   - No segmentation faults
   - No race condition errors in logs
5. After test:
   - Verify all event data integrity
   - Check for corrupted logs or images
   - Verify no resource leaks (orphaned threads, file descriptors)
6. Review logs for signal handling trace:
   - Each signal logged
   - Appropriate action taken (reload, shutdown, etc.)
   - No concurrent signal handling (serialized)

**Expected Results:**
- Zero crashes or segfaults
- No data corruption
- All signals handled appropriately
- Signal handling is serialized (no race conditions)
- System remains stable throughout

**Pass/Fail Criteria:** Zero crashes AND zero corrupted files

**Automation:** pytest test_signal_stress() (weekly chaos test)

---

## 5. Test Tools and Automation

### 5.1 Test Execution Framework

**Primary Framework:** pytest 7.0+

**Test Organization:**
```
tests/
├── performance/
│   ├── test_inference_speed.py
│   ├── test_cpu_memory.py
│   └── test_throughput.py
├── reliability/
│   ├── test_uptime.py
│   └── test_shutdown.py
├── security/
│   ├── test_network_isolation.py
│   └── test_licenses.py
├── quality/
│   ├── test_coverage.py
│   └── test_documentation.py
├── platform/
│   └── test_compatibility.py
└── conftest.py  # Shared fixtures
```

**Key pytest Plugins:**
- pytest-cov: Code coverage measurement
- pytest-timeout: Test timeout enforcement
- pytest-xdist: Parallel test execution
- pytest-benchmark: Performance benchmarking

### 5.2 Monitoring and Instrumentation

**System Monitoring:**
- **psutil:** CPU, memory, disk, network monitoring
- **powermetrics:** Thermal and power monitoring (macOS)
- **py-spy:** Performance profiling (sampling profiler)

**Network Analysis:**
- **tcpdump:** Packet capture and analysis
- **Wireshark:** Network traffic visualization
- **lsof:** Open file and network connection tracking

**Code Quality:**
- **interrogate:** Documentation coverage
- **coverage.py / pytest-cov:** Code coverage
- **radon:** Code complexity analysis
- **sloccount:** Lines of code counting

**Dependency Auditing:**
- **pip-licenses:** License compliance checking
- **safety:** Security vulnerability scanning

### 5.3 CI/CD Integration

**GitHub Actions Workflow:**

```yaml
name: NFR Test Suite

on: [push, pull_request]

jobs:
  quick-tests:
    runs-on: macos-13-m1
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Python 3.10
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Platform compatibility tests
        run: pytest tests/platform/ -v

      - name: Security tests
        run: pytest tests/security/ -v

      - name: Code quality tests
        run: |
          pytest tests/quality/test_coverage.py
          pytest tests/quality/test_documentation.py

  performance-tests:
    runs-on: macos-13-m1
    needs: quick-tests
    steps:
      - name: Setup test environment
        run: |
          # Install Ollama
          # Download CoreML models
          # Setup test RTSP stream

      - name: Performance tests
        run: pytest tests/performance/ -v --timeout=3600

  nightly-longevity:
    runs-on: macos-13-m1
    schedule:
      - cron: '0 0 * * *'  # Nightly at midnight
    steps:
      - name: 24hr uptime test
        run: pytest tests/reliability/test_uptime.py -v --timeout=90000
```

### 5.4 Test Data Management

**Test Datasets:**

1. **Sample RTSP Streams:**
   - `tests/data/indoor_low_motion.mp4` (office scene, minimal movement)
   - `tests/data/outdoor_high_motion.mp4` (street scene, cars/people)
   - `tests/data/edge_cases.mp4` (shadows, lighting changes, weather)

2. **Ground Truth Annotations:**
   - `tests/data/annotations/events.json` (expected detections with timestamps)
   - Used for accuracy validation

3. **Configuration Templates:**
   - `tests/configs/baseline.yaml` (recommended defaults)
   - `tests/configs/high_sensitivity.yaml` (low thresholds)
   - `tests/configs/stress_test.yaml` (maximum load)

**Data Storage:**
- Small test files (<10MB): Committed to Git
- Large test files (>10MB): Git LFS or external hosting
- Generated test data: Created during test setup, cleaned after

---

## 6. Test Schedule and Execution

### 6.1 Test Execution Cadence

| Test Category | Frequency | Duration | Trigger |
|---------------|-----------|----------|---------|
| Platform/Security | Every commit | <5 min | Pre-commit hook |
| Code Quality | Every PR | <10 min | CI/CD |
| Performance (quick) | Every PR | <30 min | CI/CD |
| Performance (24hr) | Nightly | 24hr | Scheduled |
| Reliability (uptime) | Nightly | 24hr | Scheduled |
| Concurrency/Chaos | Weekly | 1hr | Scheduled |
| Full Regression | Pre-release | 48hr | Manual |

### 6.2 Pre-Commit Hooks

**Automated Checks Before Commit:**
```bash
# .git/hooks/pre-commit
#!/bin/bash

# Platform compatibility
pytest tests/platform/ --quiet || exit 1

# License compliance
pytest tests/security/test_licenses.py --quiet || exit 1

# Code coverage
pytest --cov=core --cov-fail-under=70 || exit 1

# Documentation coverage
interrogate --fail-under=80 . || exit 1
```

### 6.3 CI/CD Pipeline

**Pull Request Checks:**
1. Platform compatibility (NFR1, NFR17, NFR24)
2. Security tests (NFR12-14)
3. Code quality (NFR28-29)
4. Quick performance tests (NFR18-19)
5. Dry-run mode test (NFR19)

**Merge to Main:**
1. All PR checks pass
2. 1hr performance test subset
3. Manual approval for release candidates

**Nightly Builds:**
1. Full 24hr uptime test (NFR7)
2. 24hr CPU/memory monitoring (NFR4-5)
3. Thermal stress test (NFR11)
4. Storage simulation (NFR10)

**Weekly Tests:**
1. Signal handling stress test (NFR26)
2. Chaos engineering (random failures)
3. Network isolation verification (NFR13-14)

### 6.4 Release Testing

**Pre-Release Checklist:**
- [ ] All NFRs pass automated tests
- [ ] 48hr longevity test completed
- [ ] Manual setup test (<30min) completed
- [ ] README walkthrough successful
- [ ] Security audit passed (licenses, network isolation)
- [ ] Performance benchmarks meet targets
- [ ] Test coverage ≥70% for core logic
- [ ] Documentation coverage ≥80%

---

## 7. Success Criteria

### 7.1 NFR Pass Criteria

**Overall Success:** All 29 NFRs must pass their defined test criteria

**Critical NFRs (Must Pass):**
- NFR2, NFR3: Inference speed (CoreML <100ms, LLM <5s)
- NFR4, NFR5: Resource limits (CPU <30%, RAM <8GB)
- NFR7: 24hr uptime without crashes
- NFR13: 100% local processing (zero external calls)
- NFR29: Test coverage ≥70%

**High Priority NFRs (Should Pass):**
- NFR8, NFR9: Processing efficiency (>90% filter, >95% throughput)
- NFR21, NFR23: Graceful shutdown and data integrity
- NFR28: Documentation coverage ≥80%

**Medium Priority NFRs (Nice to Have):**
- NFR10: Storage <4GB/30days (can optimize later)
- NFR18-20: Startup/reload times (user experience)
- NFR26: Signal handling stress (edge case)

### 7.2 Test Coverage Goals

**Minimum Coverage:**
- NFR test automation: 100% (all 29 NFRs have automated tests)
- Code coverage: ≥70% for core logic
- Documentation coverage: ≥80% for public APIs
- Critical paths: 100% (motion detection, de-duplication, config validation)

### 7.3 Defect Severity Classification

| Severity | Description | Example | Action |
|----------|-------------|---------|--------|
| **Critical** | NFR failure causing system unusable | CoreML >200ms, memory >16GB, crashes | Block release |
| **High** | NFR failure degrading key functionality | CPU >40%, filter <80%, shutdown >10s | Fix before release |
| **Medium** | NFR failure affecting user experience | Startup >15s, logging overhead >8% | Fix in next release |
| **Low** | NFR marginally outside target | Storage 4.2GB (target 4GB) | Document, monitor |

---

## 8. Risks and Mitigations

### 8.1 Test Environment Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **M1 hardware availability** | Can't run tests | Medium | Use personal MacBook Pro, GitHub Actions M1 runners |
| **RTSP camera reliability** | Flaky tests | High | Use recorded video files as fallback, multiple cameras |
| **Ollama service instability** | Test failures | Medium | Mock Ollama responses for unit tests, use local Docker |
| **Network variability** | Inconsistent perf results | High | Use local loopback for tests, fixed test videos |

### 8.2 Test Execution Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **24hr tests timeout** | Incomplete validation | Medium | Split into 6x 4hr tests, use checkpointing |
| **Thermal throttling during tests** | Invalid perf data | High | Control ambient temp, monitor thermal state, exclude throttled runs |
| **Memory leaks in tests** | False failures | Low | Run tests in isolated processes, cleanup between tests |
| **Flaky concurrency tests** | False positives | High | Run multiple iterations, require 5/5 passes |

### 8.3 Automation Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **CI/CD runner costs** | Budget overrun | Low | Use free tier, optimize test duration, run selectively |
| **Test maintenance burden** | Outdated tests | Medium | Regular test review, refactor for maintainability |
| **False positives** | Ignored failures | Medium | Strict pass/fail criteria, manual review of edge cases |

---

## 9. Test Reporting

### 9.1 Test Reports

**Per-Test-Run Reports:**
- **Performance Report:** All timing metrics with statistical analysis (avg, median, p95)
- **Resource Report:** CPU/memory/storage usage timeline graphs
- **Reliability Report:** Uptime, crash count, data integrity results
- **Security Report:** Network traffic analysis, license audit
- **Quality Report:** Coverage metrics, documentation completeness

**Format:** HTML dashboard + JSON data for trending

### 9.2 Test Metrics Tracking

**Key Metrics to Track Over Time:**
1. NFR pass rate (% of NFRs passing)
2. Average CoreML inference time (trend)
3. Average LLM inference time (trend)
4. Peak memory usage (trend)
5. 24hr uptime success rate
6. Code coverage trend
7. Documentation coverage trend

**Visualization:** Grafana dashboard with historical trends

### 9.3 Defect Tracking

**Issue Template for NFR Failures:**
```markdown
## NFR Failure Report

**NFR:** NFR-XX (Description)
**Test Case:** TC-XXX
**Severity:** Critical/High/Medium/Low
**Environment:** macOS version, Python version, hardware

**Failure Details:**
- Expected: <target value>
- Actual: <measured value>
- Variance: <percentage>

**Reproduction Steps:**
1. ...

**Logs/Screenshots:**
- Attach relevant logs
- Performance graphs

**Root Cause:** (if known)

**Proposed Fix:**
```

---

## 10. Test Plan Approval

### 10.1 Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Manager | John | _________ | _____ |
| Developer | Brent Bengtson | _________ | _____ |
| QA Lead | (Solo dev - same) | _________ | _____ |

### 10.2 Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-08 | John (PM) | Initial test plan creation |

---

## Appendices

### Appendix A: Test Tool Installation

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-timeout pytest-xdist pytest-benchmark
pip install psutil interrogate radon sloccount
pip install pip-licenses safety

# Install monitoring tools (macOS)
# powermetrics - pre-installed on macOS
# tcpdump - pre-installed on macOS

# Setup Ollama for testing
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llava:latest
```

### Appendix B: Quick Test Execution Guide

```bash
# Run all platform/security tests (fast)
pytest tests/platform tests/security -v

# Run code quality checks
pytest tests/quality -v
interrogate -v --fail-under=80 .

# Run quick performance tests
pytest tests/performance/test_startup.py -v

# Run full test suite (long running)
pytest tests/ -v --timeout=90000

# Run specific NFR test
pytest tests/ -k "nfr2" -v

# Generate coverage report
pytest --cov=core --cov-report=html --cov-report=term
```

### Appendix C: CI/CD Environment Setup

```yaml
# GitHub Actions M1 runner configuration
- name: Setup test environment
  run: |
    # Install Python dependencies
    pip install -r requirements.txt
    pip install -r requirements-test.txt

    # Install Ollama
    curl -fsSL https://ollama.ai/install.sh | sh
    ollama serve &
    ollama pull llava:latest

    # Download CoreML models
    python scripts/download_models.py

    # Setup test RTSP stream (simulated)
    python tests/setup_test_stream.py
```

---

**End of Test Plan**
