# Project Brief: Local Video Recognition System

**Version:** 2.0
**Date:** 2025-11-08
**Status:** Draft

---

## Executive Summary

**Product Concept:** A privacy-first, M1-optimized video recognition system that uses local LLM (Ollama) to analyze RTSP camera feeds and provide semantic understanding of events in monitored spaces.

**Primary Problem:** Understanding what happens in monitored spaces when not actively watching, learning how ML/computer vision works in practice, and receiving actionable alerts for specific events—all without cloud dependencies or privacy compromises.

**Target Market:** Solo developers, privacy-conscious home automation enthusiasts, ML/CV learners, and individuals seeking local-first smart home security solutions.

**Key Value Proposition:** 100% local processing using cutting-edge vision language models (LLaVA, Moondream) running on Apple Silicon's Neural Engine, delivering semantic event understanding ("person carrying package") rather than basic object labels, with zero cloud dependencies and comprehensive output formats for learning, awareness, and alerting.

---

## Problem Statement

### Current State & Pain Points

1. **Awareness Gap:** Existing security cameras record continuously but provide no insight into what actually happened. Reviewing hours of footage is tedious and time-consuming.

2. **Learning Barrier:** ML and computer vision remain abstract concepts without hands-on implementation. Available tutorials focus on toy datasets, not real-world RTSP streams and production challenges.

3. **Privacy vs. Functionality Trade-off:** Cloud-based solutions (Nest, Ring, etc.) offer smart features but require uploading video to third parties. Local solutions lack semantic understanding beyond basic motion detection.

4. **Alert Noise:** Traditional motion detection generates excessive false positives (tree branches, shadows, pets) without context about what actually triggered the event.

### Impact of the Problem

- **Missed Events:** Important occurrences (package deliveries, unexpected visitors, unusual activity) go unnoticed until manual review
- **Skill Gap:** Understanding of ML/CV remains theoretical rather than practical, limiting career growth and project capabilities
- **Privacy Concerns:** Forced choice between smart features (cloud) or privacy (dumb local recording)
- **Alert Fatigue:** Constant false alarms reduce trust in the system and lead to ignored notifications

### Why Existing Solutions Fall Short

- **Cloud Services:** Require monthly subscriptions, upload private video data, depend on internet connectivity, and lock users into vendor ecosystems
- **Traditional CV:** Basic motion/object detection lacks semantic understanding and context (can detect "object" but not "person carrying package")
- **Open Source Options:** Complex multi-service architectures (Frigate, ZoneMinder) require significant setup, lack M1 optimization, and often still require separate cloud LLM APIs
- **Commercial NVR Systems:** Expensive, proprietary, limited customization, no access to underlying ML models or raw data for learning

### Urgency & Importance

- **Technology Maturity:** Vision language models (LLaVA, Moondream) are now lightweight enough to run locally on consumer hardware (M1/M2)
- **Apple Silicon Opportunity:** M1/M2 Neural Engine provides unprecedented local inference performance, making real-time processing feasible
- **Privacy Regulations:** Growing awareness of data privacy (GDPR, CCPA) increases demand for local-first solutions
- **Learning Investment:** Building this now develops immediately marketable skills in ML deployment, computer vision, and edge AI

---

## Proposed Solution

### Core Concept & Approach

A **motion-triggered, API-first video recognition system** that combines traditional computer vision (OpenCV motion detection, CoreML object detection) with modern vision language models (Ollama/LLaVA) to provide semantic understanding of events in RTSP camera feeds—optimized specifically for Apple Silicon's M1/M2 Neural Engine.

**Hybrid Processing Pipeline:**
```
RTSP Stream → Motion Detection (cheap) → Frame Sampling → CoreML Object Detection (fast, ANE-optimized) → LLM Analysis (expensive, semantic) → Multi-Format Output (logs, clips, images, dashboard)
```

### Key Differentiators

1. **Performance Through Intelligence:** Motion-triggered processing + frame sampling + CoreML pre-filtering means the expensive LLM analyzes <1% of frames, making real-time processing feasible on a laptop

2. **100% Local, 100% Private:** Zero cloud dependencies, all data stays on-premises, edge firewall isolated, no external API calls

3. **Semantic Understanding:** Vision LLMs provide natural language descriptions ("person in blue shirt carrying brown package to front door at 2:34pm") vs. basic labels ("person, box detected")

4. **API-First Architecture:** Decoupled processing engine from UI/consumers enables future extensibility (web dashboard, mobile app, home automation hooks) without core refactoring

5. **Learning-Oriented Design:** Comprehensive logging, multiple output formats, graceful failure handling with clear messages—optimized for understanding how the system works, not just using it

6. **Apple Silicon Native:** Leverages M1/M2 Neural Engine via CoreML for maximum efficiency, energy optimization, and thermal management

### Why This Solution Will Succeed

- **Constraint-Driven Optimization:** Zero budget + solo developer + local-only requirements forced superior architectural decisions (motion-triggered, hybrid CV+LLM, ANE optimization) that outperform cloud alternatives
- **Swappable Models:** Architecture supports multiple Ollama models (LLaVA, BakLLaVA, Moondream) for performance/accuracy benchmarking and future improvements
- **Proven Components:** RTSP (industry standard), OpenCV (mature), CoreML (Apple-supported), Ollama (active community)—standing on shoulders of giants
- **Real-World Testing:** Actual RTSP cameras in production environment from day one, not toy datasets or simulated scenarios

### High-Level Vision

A **developer-friendly, extensible platform** for local video intelligence that serves as both a functional home security/automation system and a comprehensive learning laboratory for ML/CV deployment on edge devices.

---

## Target Users

### Primary User Segment: Solo Developer / ML Learner

**Profile:**
- Software engineer or technical enthusiast with programming experience (Python familiarity)
- Interested in practical ML/computer vision experience beyond tutorials
- Values privacy and local-first computing
- Owns M1/M2 Mac (MacBook Pro or Mac Mini/Studio)
- Has 1-6 RTSP cameras (or willing to set up IP cameras)
- Comfortable with command line, YAML configuration, and Git/GitHub

**Current Behaviors & Workflows:**
- Follows ML/AI news and trends but hasn't deployed models in production
- Uses basic home security cameras with manual review of footage
- Experiments with side projects to learn new technologies
- Prefers open source solutions over commercial SaaS
- Active in developer communities (GitHub, Reddit, Discord)

**Specific Needs & Pain Points:**
- Bridge gap between ML theory (courses, tutorials) and practice (real deployment)
- Understand performance optimization for edge devices (not just cloud GPUs)
- Learn system design for real-time video processing pipelines
- Gain practical experience with modern vision models (LLaVA, etc.)
- Build portfolio project demonstrating ML engineering skills

**Goals:**
- Complete functional project demonstrating ML/CV competency for career growth
- Understand tradeoffs in model selection, performance optimization, and architecture
- Create reusable knowledge/code for future projects
- Potentially contribute to open source or share learnings with community

---

### Secondary User Segment: Privacy-Conscious Home Automation Enthusiast

**Profile:**
- Tech-savvy homeowner with existing smart home setup (Home Assistant, HomeKit)
- Strong privacy preferences (no Ring, Nest, or cloud cameras)
- Values data ownership and local control
- Willing to invest time in setup for long-term autonomy
- Budget-conscious, prefers one-time hardware costs over subscriptions

**Current Behaviors & Workflows:**
- Runs Home Assistant on local server or Raspberry Pi
- Uses open source tools (Frigate, ZoneMinder) but finds them complex or limited
- Maintains local network with edge firewall isolation
- Documents and shares configurations with self-hosting community

**Specific Needs & Pain Points:**
- Semantic event understanding without cloud uploads ("package delivered" not just "motion detected")
- Integration with existing home automation (trigger lights when person detected at night)
- Storage-efficient solution (event logs, not 24/7 raw footage)
- Reliable operation with graceful degradation when cameras disconnect

**Goals:**
- Enhance home security with intelligent alerts (reduce false positives)
- Enable automation triggers based on visual events
- Maintain complete data privacy and ownership
- Avoid subscription services and vendor lock-in

---

## Goals & Success Metrics

### Business Objectives

- **Learning Outcome:** Successfully deploy and operate a production ML/CV system on local hardware, gaining practical experience with vision models, Apple Neural Engine optimization, and real-time video processing pipelines _(Measured by: Completion of functional MVP with documentation of learnings and challenges)_

- **Functional Value:** Create awareness of events in monitored spaces through automated semantic analysis and alerts _(Measured by: Daily event summaries accurately capturing significant occurrences without manual video review)_

- **Portfolio Development:** Produce a comprehensive, well-documented open source project demonstrating ML engineering competency _(Measured by: GitHub repository with >80% code coverage in documentation, architecture diagrams, and setup instructions)_

- **Privacy Achievement:** Maintain 100% local processing with zero cloud dependencies or data uploads _(Measured by: Network monitoring confirms zero external API calls during operation)_

### User Success Metrics

- **Event Detection Accuracy:** System correctly identifies and classifies events with semantic descriptions _(Target: >85% accuracy on real-world events like package delivery, person detection, vehicle arrival)_

- **Performance Efficiency:** Processing runs continuously without thermal throttling or system slowdowns _(Target: <30% average CPU usage, <8GB RAM, <70°C sustained temperature on M1 MacBook Pro)_

- **Storage Efficiency:** Event logs and clips fit within disk constraints through intelligent rotation _(Target: <4GB total storage for 30 days of event data)_

- **Alert Relevance:** Notifications contain only actionable events, not false positives _(Target: <5% false positive rate based on user feedback)_

- **System Reliability:** Graceful handling of failures with automatic recovery _(Target: >99% uptime with flaky camera disconnects handled transparently)_

### Key Performance Indicators (KPIs)

- **Processing Latency:** Time from motion detection to LLM analysis completion _(Target: <5 seconds for 95th percentile events)_

- **Frame Processing Rate:** Percentage of motion-triggered frames successfully analyzed _(Target: >95% of interesting frames processed without queue overflow)_

- **Model Inference Speed:** CoreML object detection + LLM vision analysis time _(Target: CoreML <100ms, LLM <3s on M1)_

- **Camera Capacity:** Number of simultaneous RTSP streams supported _(Target: 6 cameras at 1080p/15fps with motion-triggered processing)_

- **Developer Experience:** Time from git clone to first detection _(Target: <30 minutes with clear documentation and example configs)_

- **Documentation Coverage:** Percentage of code with inline comments and README explanations _(Target: >80% coverage, all public APIs documented)_

---

## MVP Scope

### Core Features (Must Have)

- **Single RTSP Camera Support:** Connect to one RTSP camera stream with configurable URL, authentication, and connection parameters in YAML config
  - _Rationale: Validates entire pipeline with minimal complexity; additional cameras are scaling, not architectural changes_

- **Motion-Triggered Frame Processing:** OpenCV-based motion detection preprocessing to filter out static scenes before expensive LLM processing
  - _Rationale: Core performance optimization that makes M1 real-time processing feasible; without this, system is unusable_

- **CoreML Object Detection:** M1 Neural Engine-optimized object detection using pre-trained CoreML models with configurable object blacklist (e.g., "ignore cats")
  - _Rationale: Fast pre-filtering before LLM + validates ANE integration + provides immediate visible results_

- **Ollama LLM Integration:** Vision language model (LLaVA or Moondream) for semantic event description via local Ollama instance
  - _Rationale: Delivers unique value proposition (semantic understanding) that differentiates from traditional CV_

- **YAML Configuration System:** Human-readable, validated configuration for all system parameters (camera settings, model selection, thresholds, storage location)
  - _Rationale: Prevents hardcoding, enables GitHub portability, essential for solo developer maintainability_

- **Multi-Format Logging:** Event logs in JSON and plaintext formats with timestamps, detected objects, confidence scores, and LLM descriptions
  - _Rationale: Supports all three goals (learning=detailed logs, awareness=readable summaries, alerts=structured data)_

- **Annotated Image Outputs:** Save frames with bounding boxes and labels for detected objects
  - _Rationale: Visual validation of detection quality, debugging aid, learning tool to understand model behavior_

- **Basic Failure Handling:** Graceful shutdown with error logging for RTSP connection failures, processing errors, and disk full conditions
  - _Rationale: Prevents crashes, supports learning goal (understand what went wrong), demonstrates production-ready thinking_

### Out of Scope for MVP

- Multiple camera support (limit to 1 camera initially)
- Web dashboard UI (logs and images only for MVP)
- Home automation webhooks/integrations
- Audio processing from camera microphones
- Video clip extraction (annotated frames only, not full clips)
- Automatic log rotation (manual cleanup for MVP)
- Real-time preview window (processing only, no live display)
- Advanced alerting (email, SMS, push notifications)
- User authentication (local development only)
- Custom model training or fine-tuning

### MVP Success Criteria

**The MVP is successful when:**

1. System processes RTSP stream from one camera continuously for 24+ hours without crashes or memory leaks
2. Motion detection correctly filters out static scenes (>90% reduction in frames sent to LLM)
3. CoreML object detection runs on M1 Neural Engine with <100ms inference time
4. LLM provides accurate semantic descriptions for common events (person detected, vehicle detected, package visible)
5. All events are logged in both JSON and plaintext formats with complete metadata
6. Annotated images show bounding boxes and labels matching LLM descriptions
7. System gracefully handles camera disconnection and disk full scenarios with clear error messages
8. Configuration changes in YAML take effect without code modifications
9. Documentation allows another developer to run the system in <30 minutes
10. M1 MacBook Pro runs system with <30% CPU usage and no thermal throttling

---

## Post-MVP Vision

### Phase 2 Features

**Multi-Camera Support (2-6 cameras):**
- Parallel processing pipeline with resource allocation per camera
- Unified event timeline across all cameras
- Camera health monitoring and auto-retry for flaky connections
- Estimated timeline: 2-3 weeks after MVP

**Web Dashboard:**
- Real-time event feed with annotated images
- Camera health status and performance metrics
- Event search and filtering (by camera, object type, time range)
- 4K display optimized for large monitor
- Estimated timeline: 3-4 weeks after MVP

**Video Clip Extraction:**
- Automatic short clip generation (5-10s) around interesting events
- Storage-efficient clip management with rotation
- Estimated timeline: 1-2 weeks after dashboard complete

**Advanced Alerting:**
- Configurable alert rules (if person detected + time is night → notify)
- Multiple notification channels (webhook, email, terminal)
- Alert suppression and scheduling
- Estimated timeline: 2 weeks after multi-camera support

### Long-term Vision (6-12 months)

**Intelligent Event Understanding:**
- Pattern recognition ("mail usually arrives 2-3pm")
- Anomaly detection ("unusual activity at night")
- Event correlation across cameras
- Temporal understanding (sequence of frames, not just snapshots)

**Home Automation Ecosystem:**
- Home Assistant integration via webhooks
- Apple HomeKit integration for automation triggers
- MQTT publishing for IoT ecosystem integration
- Standardized event schema for third-party consumers

**Swappable Model Architecture:**
- Support for multiple Ollama models with performance benchmarking
- Custom model fine-tuning on collected event data
- Model comparison dashboard (accuracy vs. speed tradeoffs)

**Privacy-Preserving Features:**
- Configurable face blurring for guest privacy
- Zone-based processing (analyze driveway, ignore bedroom windows)
- Scheduled processing windows (disable during family hours)

### Expansion Opportunities

**Multi-Platform Distribution:**
- Linux ARM64 support (Raspberry Pi, Jetson Nano)
- Linux AMD64/Intel x64 with CUDA/OpenVINO optimization
- Docker containerization for easy deployment
- Pre-built binaries and installation packages

**Alternative Use Cases:**
- Wildlife monitoring in backyard with species identification
- Pet behavior tracking and health insights
- Time-lapse generation of interesting events
- Training data collection for custom ML projects
- Commercial/retail analytics (foot traffic, dwell time—with privacy controls)

**Community & Ecosystem:**
- Open source repository with contribution guidelines
- Model zoo for domain-specific fine-tuned models
- Configuration templates for common scenarios
- Plugin system for custom processors and outputs

---

## Technical Considerations

### Platform Requirements

- **Target Platforms:** macOS 12+ (Monterey or newer) with Apple Silicon (M1/M2/M3)
- **Browser/OS Support:** Web dashboard (Phase 2) will support modern browsers (Chrome 100+, Safari 15+, Firefox 100+) with 4K display optimization
- **Performance Requirements:**
  - CoreML inference: <100ms per frame on M1 Neural Engine
  - LLM inference: <5s per event (Ollama/LLaVA on M1)
  - Continuous operation: <30% average CPU, <8GB RAM, no thermal throttling
  - Storage: <4GB for 30 days of event data (logs + annotated images)

### Technology Preferences

**Frontend (Phase 2):**
- Simple HTML/CSS/JavaScript (no framework) for initial dashboard
- Future consideration: Vue.js or React if complexity increases
- WebSocket or SSE for real-time event updates
- TailwindCSS or similar for rapid styling

**Backend:**
- **Core Processing:** Python 3.10+ (native M1 support, rich ML ecosystem)
- **API Server (Phase 2):** FastAPI (async support, auto-generated docs, WebSocket support)
- **LLM Interface:** Ollama Python client
- **Computer Vision:** OpenCV (motion detection, frame manipulation), coremltools (Neural Engine)

**Database:**
- **Event Storage:** SQLite (zero-config, file-based, sufficient for local usage)
- **Configuration:** YAML files (human-readable, git-friendly)
- **Logs:** Structured JSON + plaintext (no database required for MVP)

**Hosting/Infrastructure:**
- **Local Development:** Run directly on M1 MacBook Pro
- **Production Deployment:** Mac Mini or Mac Studio (24/7 operation)
- **Future:** Docker container for Linux deployment

### Architecture Considerations

**Repository Structure:**
- Monorepo approach (single repository for processing engine + web dashboard)
- Clear separation: `core/` (processing), `api/` (FastAPI server), `web/` (dashboard), `config/` (YAML schemas)
- Shared utilities in `common/` (logging, validation, helpers)

**Service Architecture:**
- **MVP:** Single Python process with threaded RTSP capture + sequential processing
- **Phase 2:** Core processing service + separate API server (communicate via filesystem or IPC)
- **Future:** Microservices with message queue (RabbitMQ or Redis) for multi-camera scaling

**Integration Requirements:**
- RTSP protocol support (OpenCV VideoCapture or ffmpeg-python)
- Ollama API client (HTTP REST API, localhost:11434 default)
- CoreML Python bindings (coremltools)
- Home automation webhooks (Phase 2): HTTP POST to configurable URLs

**Security/Compliance:**
- **MVP:** No authentication (localhost development only)
- **Phase 2:** HTTP Basic Auth for web dashboard (username/password in config)
- **Future:** OpenID Connect (OIDC) integration option for multi-user access
- **Network:** Edge firewall isolation, local network only, no external access
- **Data Privacy:** 100% local processing, no cloud uploads, all data stays on-premises

---

## Constraints & Assumptions

### Constraints

**Budget:**
- Zero budget for services, APIs, or software licenses
- Hardware: Already owned M1 MacBook Pro + RTSP cameras
- All dependencies must be open source and free

**Timeline:**
- No hard deadline (learning-focused project)
- Target MVP completion: 4-6 weeks of part-time development
- Flexible pacing based on learning curve and experimentation

**Resources:**
- Solo developer (Brent Bengtson)
- Part-time availability (evenings/weekends)
- No team support or code review (self-directed learning)

**Technical:**
- M1 MacBook Pro 16GB RAM (memory management critical)
- 256GB SSD (storage rotation essential)
- Local network only (no internet required for operation)
- Existing RTSP camera infrastructure (no control over camera firmware or features)

### Key Assumptions

1. **Ollama performance assumption:** M1 can process vision model inference (LLaVA/Moondream) fast enough for motion-triggered workload (<5s per event). _Validation: Benchmark needed with real RTSP feed._

2. **Motion detection effectiveness:** OpenCV motion detection will reduce frame processing by >90%, making real-time LLM analysis feasible. _Validation: Test with actual camera feeds in different lighting/weather conditions._

3. **CoreML availability:** Pre-trained object detection models in CoreML format are available and performant on M1 ANE. _Validation: Research Apple's ML model gallery and community conversions._

4. **RTSP reliability:** Cameras will maintain stable RTSP connections with occasional disconnects (not constant failures). _Validation: Monitor camera uptime over 1-2 weeks before development._

5. **Storage sufficiency:** Event-only logging (no raw video) will fit within 4GB for 30 days of typical activity. _Validation: Calculate based on estimated events per day × image size × log size._

6. **Python performance:** Python (not C++/Rust) is sufficient for real-time processing when expensive operations are handled by CoreML/Ollama. _Validation: Profile Python overhead vs. actual inference time._

7. **Single developer maintainability:** Architecture complexity can be managed by solo developer without external help. _Validation: Continuous documentation and code organization discipline._

---

## Risks & Open Questions

### Key Risks

- **Performance Bottleneck:** M1 may not handle LLM inference fast enough even with motion-triggered filtering, causing queue overflow and dropped events. _Impact: System becomes unusable for real-time monitoring. Mitigation: Aggressive frame sampling (every 10th frame), model selection (Moondream over LLaVA), frame resolution reduction._

- **LLM Accuracy Issues:** Vision models may produce inaccurate or inconsistent semantic descriptions, reducing trust in alerts. _Impact: False positives/negatives make system unreliable. Mitigation: Prompt engineering, model comparison testing, hybrid approach (CoreML labels + LLM verification)._

- **Storage Management Complexity:** Log rotation and clip management may be more complex than anticipated, leading to disk full failures. _Impact: System crashes or stops processing. Mitigation: Simple FIFO rotation in MVP, configurable max storage limit with hard stops._

- **RTSP Connection Instability:** Frequent camera disconnections may overwhelm retry logic or create alert noise. _Impact: Constant error messages, missed events during reconnection gaps. Mitigation: Exponential backoff, auto-disable after threshold, clear health status in logs._

- **Scope Creep:** Feature additions (web dashboard, multi-camera, home automation) may delay MVP or increase complexity beyond solo developer maintainability. _Impact: Never reach functional system, project abandonment. Mitigation: Strict MVP definition, Phase 2 gating, resist urge to "just add one more thing."_

- **Apple Neural Engine Compatibility:** CoreML models may not run on ANE (fall back to CPU/GPU), negating performance advantages. _Impact: Slower inference, higher CPU usage, thermal throttling. Mitigation: Verify ANE execution in testing, select ANE-compatible models, profile inference._

### Open Questions

- **LLM Context Window:** Should the LLM receive a single frame or a sequence of frames for temporal understanding? What's the optimal context length?

- **Frame Sampling Rate:** Is every 10th frame sufficient, or will scene dynamics require higher sampling? How does this vary by camera location (busy street vs. quiet backyard)?

- **Overlapping Events:** How to handle simultaneous motion detection on multiple cameras (Phase 2)? Process sequentially, parallel threads, or queue with prioritization?

- **Motion Detection Algorithm:** Should MVP use traditional CV (background subtraction) or ML-based motion detection? What's the accuracy/speed tradeoff?

- **Model Update Strategy:** How should users update Ollama models? Auto-update, manual CLI commands, or version pinning for reproducibility?

- **Alert De-duplication:** How to avoid multiple alerts for the same continuous event (person walking across multiple frames)? Time-based suppression, event ID tracking?

- **Configuration Validation:** What happens when user provides invalid YAML (malformed, missing required fields)? Fail fast with clear error, or use defaults with warnings?

### Areas Needing Further Research

- **CoreML Model Benchmarking:** Compare available object detection models (MobileNet, YOLO variants) on M1 for speed/accuracy tradeoffs with real RTSP feeds

- **Ollama Vision Model Performance:** Test LLaVA vs. BakLLaVA vs. Moondream inference speed and description quality on M1 hardware

- **Prompt Engineering:** Experiment with vision model prompts to get consistent structured output (JSON format with objects, actions, confidence scores)

- **Storage Estimation:** Collect sample event data to validate 4GB/30-day assumption and determine optimal rotation strategy

- **Home Automation APIs:** Research Home Assistant and HomeKit webhook/API formats for Phase 2 integration planning

- **OpenCV Motion Detection Tuning:** Test background subtraction parameters (sensitivity, blur, threshold) with different camera scenarios (indoor/outdoor, day/night, static/dynamic backgrounds)

---

## Appendices

### A. Research Summary

#### Brainstorming Session (2025-11-08)
Comprehensive 4-technique brainstorming session generated 75+ ideas and insights:

**Key Findings:**
- **Hybrid Processing Pipeline:** Motion detection → CoreML filtering → LLM analysis reduces processing by >99%, making M1 real-time operation feasible
- **API-First Architecture:** Decoupling core engine from consumers enables unexpected use cases (wildlife monitoring, pet tracking, time-lapses)
- **Constraint-Driven Optimization:** Zero budget + solo dev + M1-only forced superior architectural decisions over cloud alternatives
- **Performance Through Intelligence:** Frame sampling (every 10th frame) + motion-triggered processing + CoreML pre-filtering optimizes resource usage

**Priority Decisions:**
1. Motion-triggered frame processing pipeline (foundational architecture)
2. YAML configuration system (prevents hardcoding, enables portability)
3. CoreML object detection integration (validates ANE approach, immediate results)

**Techniques Used:** SCAMPER Method, What If Scenarios, Morphological Analysis, First Principles Thinking

Full session results: `docs/brainstorming-session-results.md`

### C. References

- [Ollama Documentation](https://ollama.ai/docs) - Local LLM deployment and API
- [Apple CoreML Models](https://developer.apple.com/machine-learning/models/) - Pre-trained models for M1 Neural Engine
- [OpenCV Motion Detection](https://docs.opencv.org/4.x/d1/dc5/tutorial_background_subtraction.html) - Background subtraction techniques
- [RTSP Protocol Specification](https://datatracker.ietf.org/doc/html/rfc2326) - Real-time streaming protocol
- [LLaVA Model](https://llava-vl.github.io/) - Large Language and Vision Assistant
- [Moondream Model](https://github.com/vikhyat/moondream) - Lightweight vision language model
- Brainstorming Session Results: `docs/brainstorming-session-results.md`

---

## Next Steps

### Immediate Actions

1. **Create System Architecture Document** - Design detailed component diagrams, data flow, API specifications, and processing pipeline before writing code (1-2 days)

2. **Set Up Development Environment** - Initialize Python project with virtual environment, install dependencies (OpenCV, coremltools, PyYAML, pydantic), download Ollama and test models (LLaVA or Moondream) (1 day)

3. **Validate Core Assumptions** - Benchmark Ollama vision model inference speed on M1, test RTSP stream capture with OpenCV, profile CoreML object detection on Neural Engine (2-3 days)

4. **Implement MVP Priority #1: Motion-Triggered Pipeline** - Build RTSP capture → motion detection → frame queue → processing logic (1-2 weeks)

5. **Implement MVP Priority #2: YAML Configuration** - Define schema, create example config, add validation with pydantic (3-5 days)

6. **Implement MVP Priority #3: CoreML Integration** - Load pre-trained models, integrate inference, extract bounding boxes and labels (1-2 weeks)

7. **Test End-to-End MVP** - Run system for 24+ hours, validate success criteria, document issues and learnings (1 week)

8. **Create Documentation** - Write comprehensive README with setup instructions, architecture overview, configuration guide, and troubleshooting (2-3 days)

### PM Handoff

This Project Brief provides the full context for **Local Video Recognition System**. Please start in 'PRD Generation Mode', review the brief thoroughly to work with the user to create the PRD section by section as the template indicates, asking for any necessary clarification or suggesting improvements.
