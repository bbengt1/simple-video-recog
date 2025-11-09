# Brainstorming Session Results

**Session Date:** 2025-11-08
**Facilitator:** Business Analyst Mary 📊
**Participant:** Brent Bengtson

---

## Executive Summary

**Topic:** RTSP Video Recognition System with Local LLM (Ollama) for M-Series macOS

**Session Goals:**
- Build a learning project to understand ML/computer vision in practice
- Create awareness of what happens in monitored spaces when not watching
- Develop an actionable alert system for specific events
- Establish foundation for future feature-rich enhancements

**Techniques Used:**
1. SCAMPER Method (35 minutes)
2. What If Scenarios (25 minutes)
3. Morphological Analysis (30 minutes)
4. First Principles Thinking (25 minutes)

**Total Ideas Generated:** 75+ architectural decisions, features, and insights

### Key Themes Identified:
- **Performance-First Design:** Every architectural decision optimized for M1 efficiency (ANE, motion-triggered processing, frame sampling)
- **API-First Architecture:** Decouple core engine from UI/consumers for maximum extensibility
- **Graceful Degradation:** Comprehensive failure handling with user control and clear communication
- **Future-Proof Flexibility:** Swappable models, configurable parameters, multi-platform potential
- **Privacy by Design:** 100% local processing, no cloud dependencies, edge firewall isolation
- **Learning-Oriented:** Solo developer maintainable, well-documented, open source

---

## Technique Sessions

### SCAMPER Method - 35 minutes

**Description:** Systematic technique for adapting and improving existing solutions by exploring: Substitute, Combine, Adapt, Modify, Put to other uses, Eliminate, Reverse/Rearrange

#### Ideas Generated:

**S - SUBSTITUTE:**
1. Sample every 10th frame instead of processing all frames (10x performance improvement)
2. Use buffered processing instead of pure real-time streaming
3. Single LLM model approach (simpler architecture, easier maintenance)

**C - COMBINE:**
4. Combine multiple data sources (video + metadata/timestamps/location)
5. Hybrid Traditional CV + LLM approach (fast filtering then intelligent analysis)
6. Logs AND visualizations (developer-friendly + user-friendly outputs)
7. Selectable camera combining (flexible single/multi-camera analysis streams)

**A - ADAPT:**
8. Security camera software patterns (reliable multi-camera handling, recording triggers)
9. Game engine frame processing techniques (optimized render pipelines, efficient buffers)
10. Energy optimization strategies (critical for MacBook Pro battery life)
11. Home automation hooks (Home Assistant + Apple HomeKit integration points)

**M - MODIFY/MAGNIFY/MINIFY:**
12. API-first design (modifications/configuration via API)
13. External system callable (decouple processing engine from interface)
14. Future UI ready (web dashboard, mobile app, CLI can all plug in later)

**P - PUT TO OTHER USES:**
15. Wildlife monitoring in backyard
16. Package delivery detection
17. Pet behavior tracking
18. Time-lapse generation of interesting events
19. Training data collection for future ML projects
20. Home security alert system

**E - ELIMINATE:**
21. No cloud dependencies (100% local processing)
22. No raw video storage (save only events/logs/metadata - massive disk savings)

**R - REVERSE/REARRANGE:**
23. Detect → Decide if worth processing → Log (smart filtering before expensive LLM processing)

#### Insights Discovered:
- **Hybrid processing pipeline** (cheap motion detection → expensive LLM only on interesting frames) is the key to M1 performance
- **API-first architecture** enables multiple future use cases without redesigning the core
- **Game engine techniques** solve similar real-time processing problems and are directly applicable
- **Elimination of raw video** transforms storage requirements from terabytes to gigabytes

#### Notable Connections:
- Motion-triggered processing connects to energy optimization AND performance constraints
- Home automation hooks unlock entirely new use case categories (security, convenience)
- Multiple alternative uses validate the extensible architecture approach

---

### What If Scenarios - 25 minutes

**Description:** Exploring edge cases, failure modes, and future possibilities through provocative "what if" questions

#### Ideas Generated:

24. **Resource Contention Handling:** Display message about resource contention + offer graceful shutdown (never crash)
25. **Multi-Camera Scaling:** Hard limit of 6 cameras maximum (realistic for M1 performance boundaries)
26. **Network Resilience:** Temporarily disable flaky cameras → auto-retry every 5 minutes → disable after 5 min until manual restart + alert message
27. **Storage Management:** Log/data rotation based on user-configurable max disk space (default 4GB)
28. **Security & Privacy:** Local username/password authentication + future OIDC integration option
29. **Open Source Evolution:** Full parameterization (GitHub-ready) + future multi-platform support (Linux ARM64, AMD64, Intel x64)

#### Insights Discovered:
- **Fault isolation** (one bad camera doesn't crash entire system) is critical for reliability
- **User control** is paramount - always offer choices, never force actions
- **Clear communication** during failures supports the learning goal
- **Future platform expansion** requires architecture decisions NOW (parameterization, portability)

#### Notable Connections:
- Network resilience strategy mirrors failure handling patterns from First Principles
- Storage rotation directly addresses 256GB disk constraint
- Security layers (basic → advanced) match the progressive enhancement philosophy

---

### Morphological Analysis - 30 minutes

**Description:** Systematic exploration of key technical parameters and their option combinations to identify optimal architecture

#### Component Matrix Generated:

**Parameter 1: LLM Model Choice (Ollama)**
30. LLaVA (full vision + language capability)
31. BakLLaVA (performance-optimized variant)
32. Moondream (lightweight/fast option)
33. Swappable model architecture (future-proof for new releases)

**Parameter 2: Object Detection Approach**
34. CoreML models (native M1 Neural Engine optimization)
35. Blacklist capability (filter unwanted object types)

**Parameter 3: Storage Location**
36. User-selectable (local disk OR external SSD via USB-C)
37. Configurable via YAML parameters

**Parameter 4: Output/Visualization Formats**
38. Logs: JSON, plaintext, CSV (multiple format support)
39. Visualizations: Annotated images with bounding boxes
40. Video clips of events
41. Dashboard graphs/analytics
42. Real-time displays: Live preview window
43. Terminal output (CLI monitoring)
44. Web dashboard (future UI hook via API)
45. Event summaries: Daily reports, timeline views

**Parameter 5: Configuration Management**
46. YAML config files (human-readable, git-friendly, Python-native)
47. Parameter-driven architecture
48. Schema validation on startup

**Parameter 6: M1 Neural Engine Optimization**
49. ANE (Apple Neural Engine) via coremltools
50. Direct Neural Engine optimization
51. Model conversion to CoreML format for ANE

#### Insights Discovered:
- **CoreML + ANE** combination provides maximum M1 performance with Python compatibility
- **Comprehensive output formats** serve all three fundamental goals (learning, awareness, alerts)
- **Swappable LLM models** allow performance vs. accuracy benchmarking on real hardware
- **YAML configuration** balances human editability with machine parseability

#### Notable Connections:
- CoreML detection → ANE optimization → game engine techniques form a cohesive performance strategy
- Multiple output formats → API consumers → future UI creates clear separation of concerns
- User-selectable storage → parameterization → GitHub-ready form a portability strategy

---

### First Principles Thinking - 25 minutes

**Description:** Breaking down to fundamental truths and building up from core requirements

#### Fundamental Questions Explored:

**Q1: What is the FUNDAMENTAL problem being solved?**
52. Understanding what happens in spaces when not watching (awareness/insight)
53. Learning how ML/computer vision works in practice (education/skill-building)
54. Getting alerts about specific events (actionable notifications)

**Q2: What are the MINIMUM components required?**
55. MVP: 1 RTSP camera + M1 processor + 4GB storage + web display (4K monitor support)

**Q3: What ASSUMPTIONS are being made?**
56. **LLM is essential:** Validated - need semantic understanding ("person carrying package") and natural language descriptions beyond CoreML's basic labels
57. **RTSP protocol:** Validated - matches camera infrastructure
58. **Audio processing:** Refined - configurable option (if camera has microphone), default video-only, future audio event detection
59. **Motion-triggered preprocessing:** Enhanced - cameras stream continuously, app uses motion detection to filter before expensive LLM invocation

**Q4: What are the CONSTRAINTS?**

*Technical:*
60. M1 MacBook Pro architecture (ANE optimization required)
61. 100% local processing (zero cloud dependencies)
62. Open source stack only (zero licensing costs)

*Resources:*
63. Solo developer (architecture must be maintainable by one person)
64. Zero budget (no paid services/tools)
65. Flexible timeline (learning-focused, not deadline-driven)

*Privacy/Security:*
66. Local network only
67. Edge firewall isolation (no external access)
68. All data stays on-premises

*Performance:*
69. 16GB RAM budget
70. 256GB disk (limited storage - rotation critical)
71. Must not tax M1 (energy efficient, no thermal throttling)

**Q5: What's the SIMPLEST architecture?**
72. **Core Pipeline:** RTSP Camera Input → Event-Triggered Processing (Motion Detection → Object Recognition) → Multi-Format Output (Logs + Video Clips + Annotated Frames)

**Q6: What COULD GO WRONG?**

*Failure Modes & Recovery:*
73. **RTSP Input Failure:** Graceful shutdown + notification in logs/display + auto-retry/disable pattern
74. **Motion Detection Failure:** Log + display message + offer restart option
75. **Object Recognition Failure:** Display failure location/details + option to shutdown or restart + log stack trace
76. **Output Generation Failure:** Display error message with root cause + option to shutdown/restart (e.g., disk full, permissions)

**Common Pattern:** Always inform → Always offer control → Always allow recovery

#### Insights Discovered:
- **Three-goal alignment** (awareness, learning, alerts) justifies comprehensive output strategy
- **Constraints are liberating** - eliminate entire complexity categories (cloud sync, multi-platform initially, team collaboration)
- **Linear pipeline** is maintainable for solo dev while remaining extensible
- **User control in failures** supports learning goal and prevents frustration

#### Notable Connections:
- Motion-triggered preprocessing (assumption #4) perfectly implements "detect → decide → log" reversal from SCAMPER
- Failure handling pattern (inform → control → recovery) consistent across all four failure modes
- MVP definition (Q2) validates that all complex features are truly enhancements, not requirements

---

## Idea Categorization

### Immediate Opportunities
*Ideas ready to implement now*

1. **Motion-Triggered Frame Processing Pipeline**
   - Description: Implement detect → decide → process → log pipeline with motion detection as preprocessing filter
   - Why immediate: Solves core performance challenge, well-defined scope, available libraries (OpenCV motion detection)
   - Resources needed: OpenCV, basic frame buffer, motion detection algorithm (background subtraction)

2. **YAML Configuration System**
   - Description: Parameter-driven configuration for all system settings (camera URLs, storage location, model selection, thresholds)
   - Why immediate: Foundation for everything else, prevents hardcoding, enables GitHub portability
   - Resources needed: PyYAML, pydantic for validation, example config file with comments

3. **CoreML Object Detection Integration**
   - Description: Integrate Apple's CoreML models for M1-optimized object detection with blacklist filtering
   - Why immediate: Native M1 performance, well-documented Apple APIs, directly leverages ANE
   - Resources needed: coremltools, pre-trained CoreML models, Python CoreML bindings

### Future Innovations
*Ideas requiring development/research*

4. **Multi-LLM Support (LLaVA, BakLLaVA, Moondream)**
   - Description: Swappable LLM architecture via Ollama for comparing performance vs. accuracy on M1 hardware
   - Development needed: Ollama Python API integration, model abstraction layer, prompt engineering for consistent output format
   - Timeline estimate: 2-3 weeks after core pipeline working

5. **Comprehensive Output System**
   - Description: Multiple output formats (JSON logs, CSV exports, annotated images, video clips, web dashboard, timeline views)
   - Development needed: Output abstraction layer, web server (FastAPI), frontend (simple HTML/JS), video clip extraction
   - Timeline estimate: 3-4 weeks, can be implemented incrementally per output type

6. **Home Automation Integration Hooks**
   - Description: Webhook/API endpoints for Home Assistant and Apple HomeKit integration to trigger automations on events
   - Development needed: Webhook system, event subscription model, HomeKit/Home Assistant protocol research
   - Timeline estimate: 2-3 weeks after API-first architecture established

7. **Audio Event Detection (Optional)**
   - Description: Configurable audio processing for cameras with microphones (glass breaking, barking, doorbell)
   - Development needed: Audio stream handling, audio ML models, audio event classification
   - Timeline estimate: 3-4 weeks, requires audio-capable cameras for testing

### Moonshots
*Ambitious, transformative concepts*

8. **Multi-Platform Distribution (Linux ARM64/AMD64/Intel x64)**
   - Description: Package system for cross-platform deployment with platform-specific optimizations (ANE for M1, CUDA for Linux)
   - Transformative potential: Opens project to entire home automation/security community, not just macOS users
   - Challenges to overcome: Platform-specific Neural Engine abstractions, testing infrastructure, packaging (Docker, native binaries)

9. **Autonomous Training Data Collection System**
   - Description: System automatically collects and labels interesting events to build custom datasets for fine-tuning models
   - Transformative potential: Self-improving system that gets better over time, enables custom model training for specific use cases
   - Challenges to overcome: Data labeling strategy, storage management for large datasets, model training pipeline, transfer learning approach

10. **AI-Powered Event Intelligence**
    - Description: System learns patterns over time ("mail usually arrives 2-3pm", "cat always on couch at night") and generates insights/anomaly detection
    - Transformative potential: Moves from reactive detection to proactive intelligence and predictions
    - Challenges to overcome: Time-series analysis, pattern recognition algorithms, anomaly detection models, sufficient historical data

### Insights & Learnings
*Key realizations from the session*

- **Performance through intelligence, not brute force:** Motion-triggered processing + frame sampling + CoreML filtering means LLM only analyzes <1% of frames, making real-time processing feasible on M1

- **API-first enables serendipity:** By decoupling core engine from UI, unexpected use cases (wildlife monitoring, pet tracking, time-lapses) become trivial to implement later

- **Constraints breed creativity:** Zero budget + solo dev + M1-only forced optimal architecture decisions (CoreML, ANE, motion-triggered, local-only) that are actually superior to cloud-based alternatives

- **Learning requires visibility:** Comprehensive failure handling and multiple output formats aren't "nice to have" - they're essential for understanding how the system works

- **Hybrid approaches win:** Traditional CV + LLM, local + external storage, motion + object detection - combining complementary techniques outperforms any single approach

- **Start simple, design for complex:** MVP is intentionally minimal (1 camera, basic detection), but architecture decisions (API-first, swappable models, parameterization) enable future complexity without refactoring

---

## Action Planning

### Top 3 Priority Ideas

#### #1 Priority: Motion-Triggered Frame Processing Pipeline

**Rationale:** This is the foundational architecture that makes everything else possible. Without efficient frame processing, the M1 will be overwhelmed and the project becomes infeasible. This implements the core insight: detect → decide → process → log.

**Next steps:**
1. Research and select motion detection algorithm (OpenCV background subtraction vs. frame differencing)
2. Implement basic RTSP stream capture with frame buffering
3. Add motion detection preprocessing layer
4. Create frame queue for "interesting" frames that pass motion threshold
5. Implement decision logic (skip, process, log) based on motion confidence
6. Performance testing with single camera at different frame rates

**Resources needed:**
- OpenCV Python bindings
- RTSP client library (opencv-python or ffmpeg-python)
- Basic understanding of computer vision motion detection techniques
- Profiling tools to measure M1 CPU/memory usage

**Timeline:** 1-2 weeks for functional prototype, another week for optimization

---

#### #2 Priority: YAML Configuration System

**Rationale:** Prevents hardcoding and enables the entire "parameterization first" philosophy. This makes the codebase GitHub-ready from day one and supports all future features (camera URLs, model selection, thresholds, storage location). Essential for solo developer maintainability.

**Next steps:**
1. Define configuration schema (camera settings, processing parameters, storage options, model selection, thresholds)
2. Create example config.yaml with extensive comments explaining each parameter
3. Implement config loading with pydantic validation
4. Add config validation errors with helpful messages
5. Document configuration options in README
6. Test with invalid configs to ensure validation catches errors

**Resources needed:**
- PyYAML library
- Pydantic for schema validation
- Config file documentation

**Timeline:** 3-5 days for complete implementation

---

#### #3 Priority: CoreML Object Detection Integration

**Rationale:** Delivers the core value proposition - actual object recognition - while leveraging M1 Neural Engine for optimal performance. This validates the entire technical approach and provides immediate visible results. Without this, the system is just motion detection.

**Next steps:**
1. Research available CoreML object detection models (MobileNet, YOLO variants converted to CoreML)
2. Download and test pre-trained CoreML models with sample images
3. Integrate CoreML model loading and inference into frame processing pipeline
4. Implement object blacklist filtering (user-configurable "ignore cats" etc.)
5. Extract bounding boxes and labels from CoreML output
6. Performance benchmark CoreML on M1 (inference time per frame)
7. Connect CoreML output to LLM input (pass detected objects + frame to Ollama)

**Resources needed:**
- coremltools library
- Pre-trained CoreML models (Apple's model gallery or converted models)
- Understanding of CoreML Python API
- Test images/videos for validation

**Timeline:** 1-2 weeks for integration, another week for optimization and blacklist feature

---

## Reflection & Follow-up

### What Worked Well
- **SCAMPER Method** effectively adapted existing solutions (security cameras, game engines) rather than reinventing wheels
- **Morphological Analysis** created clear technical decision matrix - now have definitive answers for "which model?" "which format?" etc.
- **What If Scenarios** uncovered critical edge cases (flaky cameras, resource contention) that would have caused issues in production
- **First Principles Thinking** validated core assumptions and confirmed LLM is essential (not just "nice to have")
- **Interactive technique flow** allowed deep exploration of each area before moving on
- **Building on previous ideas** - motion-triggered processing emerged in SCAMPER, was challenged in First Principles, and survived as core architecture

### Areas for Further Exploration
- **Specific LLM prompt engineering:** How to get consistent structured output from vision models for logging/alerting? Need to explore prompt templates
- **CoreML model comparison:** Which pre-trained models offer best speed/accuracy tradeoff on M1? Needs benchmarking session
- **Web dashboard architecture:** What frontend framework (React? Vue? Simple HTML/JS?) for 4K display output? Separate brainstorm session
- **Storage rotation implementation:** What's the algorithm for intelligent log rotation? FIFO? Priority-based retention? Separate technical design session
- **Home automation event schema:** What's the webhook payload format for Home Assistant/HomeKit? Need to research their APIs

### Recommended Follow-up Techniques
- **Technical Deep Dive Session:** Use "Five Whys" to explore CoreML model selection criteria - dig into performance characteristics
- **User Story Mapping:** When ready to build web dashboard, map out the user journey and UI flow
- **Assumption Testing:** Build quick prototypes to validate key assumptions (e.g., "can Ollama keep up with motion-triggered frame rate?")
- **Failure Mode Analysis (FMEA):** Before production use, systematically analyze all possible failures and design mitigations

### Questions That Emerged
- How much context should LLM receive? Single frame, or sequence of frames for temporal understanding?
- Should motion detection use ML models or traditional CV algorithms? Trade-off between accuracy and speed
- What's the optimal frame sampling rate? 10th frame was suggested, but needs validation based on camera FPS and scene dynamics
- How to handle overlapping events? (e.g., motion detected on camera 1 and 2 simultaneously)
- Should the system have a "learning mode" vs. "production mode" with different processing strategies?
- What's the update strategy for models? Auto-update from Ollama? Manual? Versioned?

### Next Session Planning

**Suggested topics:**
1. **Technical Architecture Deep Dive:** Create detailed system design document with component diagrams, data flow, API specifications
2. **CoreML Model Selection:** Benchmark different models on M1 hardware with real RTSP feeds
3. **Web Dashboard UX Design:** Plan the 4K display output - what information, what layout, what interactions?

**Recommended timeframe:**
- Technical architecture session: Before writing any code (1-2 days)
- Model benchmarking: After basic pipeline working (1-2 weeks)
- Dashboard UX: After API-first backend complete (3-4 weeks)

**Preparation needed:**
- Set up basic Python project structure with virtual environment
- Download sample RTSP streams or test videos for development
- Install Ollama and download initial models (LLaVA or Moondream)
- Review Apple's CoreML documentation and available pre-trained models
- Sketch initial system architecture diagram (boxes and arrows)

---

*Session facilitated using the BMAD-METHOD™ brainstorming framework*
