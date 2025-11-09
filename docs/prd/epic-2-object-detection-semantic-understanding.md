# Epic 2: Object Detection & Semantic Understanding

**Epic Goal:** Integrate CoreML object detection and Ollama LLM to identify what objects are present in motion-triggered frames and generate semantic event descriptions, delivering the core differentiator from traditional motion detection systems.

## Story 2.1: CoreML Model Loading and Neural Engine Validation

**As a** developer,
**I want** to load CoreML object detection models and verify they run on Apple Neural Engine,
**so that** I can perform fast, M1-optimized object detection on video frames.

**Acceptance Criteria:**

1. CoreML detector module (platform/coreml_detector.py) implements CoreMLDetector class with load_model(model_path) method
2. model_path from configuration specifies CoreML model file (e.g., "models/yolov3.mlmodel")
3. Model loading uses coremltools.models.MLModel API to load .mlmodel file
4. ANE (Apple Neural Engine) compatibility check verifies model will run on Neural Engine, not CPU/GPU
5. If model is not ANE-compatible, log WARNING: "Model will run on CPU/GPU (slower), consider using ANE-optimized model"
6. Model metadata extracted and logged: input shape, output format, model type (e.g., "YOLOv3-Tiny 416x416")
7. load_model() raises CoreMLLoadError with clear message if model file not found, corrupted, or incompatible
8. Successful model load logs: "✓ CoreML model loaded: [model_name] (ANE-compatible)"
9. Model warm-up: Run inference on dummy frame during load to initialize ANE and measure baseline inference time
10. Unit tests with test .mlmodel file verify: successful load, ANE check, error handling for missing/invalid models
11. Integration test: Load YOLOv3-Tiny CoreML model, verify ANE compatibility, measure warm-up inference time <100ms
12. README updated with section on obtaining CoreML models (link to Apple's model gallery or conversion instructions)

---

## Story 2.2: Object Detection Inference and Bounding Box Extraction

**As a** developer,
**I want** to run object detection inference on frames and extract detected objects with bounding boxes,
**so that** I know what objects are present and where they are located in the frame.

**Acceptance Criteria:**

1. CoreMLDetector.detect(frame) method accepts numpy array frame (BGR format from OpenCV)
2. Frame preprocessing: Convert BGR → RGB, resize to model input size (e.g., 416x416), normalize pixel values
3. CoreML inference executed via model.predict() returning raw model output (bounding boxes, class probabilities, confidence scores)
4. Post-processing: Parse model output into list of detected objects, each containing:
   - label: str (e.g., "person", "car", "dog")
   - confidence: float (0.0 to 1.0)
   - bbox: tuple (x, y, width, height) in original frame coordinates
5. Confidence threshold filtering: Only return objects with confidence >= min_confidence (from config, default: 0.5)
6. Non-maximum suppression (NMS) applied to remove duplicate detections of same object
7. detect() returns DetectionResult object with fields: objects (list), inference_time (float in seconds), frame_shape
8. Performance requirement: Inference completes in <100ms on M1 Neural Engine (measured and logged)
9. If inference time exceeds 100ms, log WARNING with actual time
10. Unit tests verify: detection on test images with known objects, confidence filtering works, bbox coordinates are correct
11. Integration test: Run detection on sample video frames, verify objects detected match ground truth annotations
12. Performance test: Run 100 inferences, verify average time <100ms and 95th percentile <120ms

---

## Story 2.3: Object Blacklist Filtering

**As a** developer,
**I want** to filter out detected objects that match a configurable blacklist,
**so that** I can ignore irrelevant objects (like pets or trees) and reduce false positive events.

**Acceptance Criteria:**

1. object_blacklist configuration parameter accepts list of object labels to ignore (e.g., ["cat", "tree", "bird"])
2. Blacklist filtering applied in CoreMLDetector.detect() before returning results
3. Detected objects with labels matching blacklist (case-insensitive) are removed from results
4. Filtering logged at DEBUG level: "Filtered [N] blacklisted objects: [labels]"
5. If all detected objects are blacklisted, detect() returns empty DetectionResult with objects=[]
6. Empty detections do NOT trigger events (no further processing, no LLM call, no event logging)
7. Blacklist supports partial matching: "cat" matches "cat", "cats", but NOT "cattle" (exact word boundary matching)
8. Blacklist defaults to empty list if not specified in config (no filtering)
9. Unit tests verify: exact match filtering, case-insensitivity, partial match behavior, empty blacklist passes all objects
10. Integration test: Configure blacklist=["cat"], run detection on frame with cat+person, verify only person returned

---

## Story 2.4: Annotated Image Generation with Bounding Boxes

**As a** developer,
**I want** to generate annotated images with bounding boxes and labels for detected objects,
**so that** I can visually verify detection quality and provide useful output for users.

**Acceptance Criteria:**

1. Image annotation module (core/image_annotator.py) implements ImageAnnotator class with annotate(frame, detections) method
2. For each detected object, draw:
   - Bounding box rectangle in green (success color) with 2-pixel thickness
   - Label text with confidence: "[label] (XX%)" positioned above bounding box
   - Text background rectangle (semi-transparent black) for readability
3. OpenCV drawing functions used: cv2.rectangle(), cv2.putText(), cv2.getTextSize()
4. Font: cv2.FONT_HERSHEY_SIMPLEX with scale 0.6 for readability
5. Color coding by confidence: green (>0.8), yellow (0.5-0.8), red (<0.5)
6. annotate() returns annotated frame as numpy array (does not modify original frame)
7. If no detections, return original frame unmodified
8. Bounding boxes clipped to frame boundaries (no drawing outside frame)
9. Overlapping labels handled: Offset vertically if bboxes overlap to prevent text collision
10. Unit tests verify: single object annotation, multiple objects, no detections, edge cases (bbox at frame edge)
11. Integration test: Annotate frame with 5+ objects, visually inspect output (save to temp file for manual review)
12. Performance: Annotation completes in <20ms for typical frame with 10 objects

---

## Story 2.5: Ollama Service Integration and Model Verification

**As a** developer,
**I want** to connect to local Ollama service and verify the vision model is available,
**so that** I can use LLMs for semantic event description generation.

**Acceptance Criteria:**

1. Ollama client module (integrations/ollama.py) implements OllamaClient class with connect() and verify_model(model_name) methods
2. ollama_model configuration parameter specifies model (e.g., "llava:latest", "moondream")
3. Connection uses ollama Python client library to communicate with localhost:11434 (default Ollama port)
4. connect() verifies Ollama service is running by calling /api/tags endpoint
5. If Ollama service not reachable, raise OllamaConnectionError: "Ollama service not reachable at localhost:11434. Is Ollama running?"
6. verify_model() checks if specified vision model is downloaded/available via /api/show endpoint
7. If model not found, raise OllamaModelNotFoundError: "Vision model '[model]' not found. Run: ollama pull [model]"
8. Successful verification logs: "✓ Ollama service: Connected (localhost:11434)" and "✓ Vision model: [model] (available)"
9. List all available models on connect (logged at DEBUG level) for troubleshooting
10. Unit tests with mocked Ollama API verify: successful connection, service unreachable error, model not found error
11. Integration test: Connect to real Ollama instance, verify llava:latest model (assumes Ollama running locally)
12. README updated with "Prerequisites" section: Installing Ollama and downloading vision models

---

## Story 2.6: Vision LLM Inference and Semantic Description Generation

**As a** developer,
**I want** to send frames with detected objects to Ollama vision LLM for semantic description,
**so that** I can generate natural language event descriptions beyond basic object labels.

**Acceptance Criteria:**

1. OllamaClient.generate_description(frame, detections) method accepts frame and DetectionResult
2. Frame encoding: Convert numpy array to base64-encoded JPEG for Ollama API
3. Prompt engineering: Construct vision prompt with context:
   ```
   Describe what is happening in this image. Focus on: {detected_object_labels}.
   Provide a concise, natural description of the scene and any actions.
   ```
4. Ollama API call: POST to /api/generate with model, prompt, and base64 image
5. Response parsing: Extract generated text from Ollama JSON response
6. Timeout handling: 10-second timeout for LLM inference (configurable via llm_timeout in config)
7. If timeout exceeded, raise OllamaTimeoutError and log warning (do not crash processing pipeline)
8. Successful inference returns string description (e.g., "Person in blue shirt carrying brown package approaching front door")
9. Performance logged: LLM inference time measured and logged at INFO level
10. Target performance: <5 seconds for 95th percentile (verified in integration tests with multiple frames)
11. If inference exceeds 5s, log WARNING with actual time
12. Unit tests with mocked Ollama API verify: successful generation, timeout handling, prompt construction
13. Integration test: Generate description for 10 sample frames, verify descriptions are semantically accurate and relevant
14. Error handling: Ollama errors (model overload, OOM) logged but don't crash system

---

## Story 2.7: Structured Event JSON Output

**As a** developer,
**I want** to generate structured JSON output for each event with all metadata,
**so that** events can be programmatically processed and stored in the database (Epic 3).

**Acceptance Criteria:**

1. Event data model (core/events.py) defines Event dataclass with fields:
   - event_id: str (unique identifier, format: "evt_" + timestamp + random)
   - timestamp: datetime (ISO 8601 format with timezone)
   - camera_id: str (from config)
   - motion_confidence: float (from motion detection)
   - detected_objects: list[dict] (each with label, confidence, bbox)
   - llm_description: str (from Ollama)
   - image_path: str (relative path to annotated image file)
   - metadata: dict (inference times, frame number, etc.)
2. Event.to_json() method serializes to JSON string with proper formatting (indented, datetime ISO format)
3. JSON schema matches FR10 requirement: timestamp, detected objects with labels/confidence, action description, location/context
4. event_id generation ensures uniqueness using timestamp (milliseconds) + 4-character random suffix
5. camera_id defaults to "camera_1" for MVP (single camera), prepared for multi-camera in Phase 2
6. metadata includes: coreml_inference_time, llm_inference_time, frame_number, motion_threshold_used
7. Event.from_json() method deserializes JSON back to Event object (for testing and future database loading)
8. Pydantic validation ensures all required fields present and types correct
9. Unit tests verify: JSON serialization/deserialization, event_id uniqueness, datetime handling, schema compliance
10. Integration test: Create event from real detection + LLM output, serialize to JSON, verify structure matches specification

---

## Story 2.8: Event De-duplication Logic

**As a** developer,
**I want** to suppress duplicate events for the same continuous activity,
**so that** users don't receive multiple alerts for a person walking across multiple frames.

**Acceptance Criteria:**

1. Event de-duplication module (core/events.py) implements EventDeduplicator class with should_create_event() method
2. deduplication_window configuration parameter specifies time window in seconds (default: 30 seconds)
3. Deduplication strategy: Suppress events with same primary object (highest confidence) within time window
4. EventDeduplicator maintains cache of recent events: {object_label: last_event_timestamp}
5. should_create_event(detections) checks if primary object (highest confidence) appeared in last N seconds
6. If primary object in cache and time_since_last < deduplication_window, return False (suppress event)
7. If suppressed, log at DEBUG: "Event suppressed: [object] detected [X]s ago (within [N]s window)"
8. If not suppressed (new object or outside window), return True and update cache with current timestamp
9. Cache cleanup: Remove entries older than 2x deduplication_window to prevent unbounded memory growth
10. Edge case: Multiple objects detected - use highest confidence object as "primary" for deduplication key
11. Unit tests verify: duplicate suppression works, window expiry works, cache cleanup prevents memory leak
12. Integration test: Process video with person walking across frame for 10 seconds, verify only 1 event created (not 150+)
13. Deduplication metrics tracked: events_suppressed counter logged in runtime status

---

## Story 2.9: Processing Pipeline Integration - Object Detection + LLM

**As a** developer,
**I want** to integrate CoreML and Ollama into the processing pipeline,
**so that** motion-triggered frames flow through the complete intelligence stack end-to-end.

**Acceptance Criteria:**

1. ProcessingPipeline (core/pipeline.py) extended with new processing stages:
   - Stage 3: Object detection (CoreML)
   - Stage 4: Event de-duplication check
   - Stage 5: LLM semantic description (Ollama)
   - Stage 6: Event creation and output
2. Full pipeline flow: RTSP frame → motion detection → sampling → **object detection → de-duplication → LLM → event output**
3. For each sampled frame with motion:
   - Run CoreML detection
   - Check blacklist filter
   - If objects detected (non-empty), check de-duplication
   - If event should be created, run LLM inference
   - Generate Event object with all metadata
   - Save annotated image to disk (data/events/YYYY-MM-DD/evt_xxxxx.jpg)
   - Output Event JSON (logged to console for now, file output in Epic 3)
4. Error handling at each stage: Log error, skip frame, continue processing (don't crash)
5. Pipeline metrics extended: objects_detected, events_created, events_suppressed, coreml_time_avg, llm_time_avg
6. Metrics logged in runtime status display (every 60s)
7. Performance target: Process motion-triggered frame end-to-end in <6 seconds (motion + CoreML + LLM)
8. If processing exceeds 10 seconds, log WARNING and consider frame drop if queue backing up
9. Graceful degradation: If Ollama unavailable, log error and create event without LLM description (still save annotated image + detection data)
10. Unit tests verify: pipeline stages execute in order, error in one stage doesn't crash pipeline, metrics tracking accurate
11. Integration test: Full end-to-end execution with test RTSP stream for 5 minutes, verify events created, annotated images saved, metrics accurate
12. Manual test: Run system with real camera, trigger motion events (walk in front of camera), verify events created with semantic descriptions

---

**Epic 2 Summary:**
- **9 Stories** delivering CoreML object detection, Ollama LLM integration, and semantic event generation
- **Vertical slices:** Each story is complete, testable functionality building towards full intelligence capability
- **Core value delivered:** System now understands WHAT is happening, not just THAT something moved
- **Deployable:** After Epic 2, system generates annotated images + semantic event descriptions (outputs to files, database in Epic 3)

---

## Rationale for Story Breakdown:

**Why 9 stories:**
- CoreML integration (2.1-2.4): 4 stories cover model loading, inference, filtering, visualization
- Ollama integration (2.5-2.6): 2 stories for connection and LLM inference
- Event processing (2.7-2.9): 3 stories for structured data, de-duplication, full pipeline integration
- Each story focused and sized for AI agent execution (2-4 hours)

**Story sequencing:**
- 2.1-2.2 (CoreML) before 2.5-2.6 (Ollama) - detect objects before describing them
- 2.3 (Blacklist) after 2.2 - filtering builds on basic detection
- 2.4 (Annotation) parallel to 2.5 - visualization independent of LLM
- 2.7 (Event JSON) before 2.8 (De-dup) - need data model before filtering
- 2.9 (Integration) last - ties everything together after individual components work

**Cross-cutting concerns:**
- Testing: Unit tests in each story + integration tests for end-to-end flows
- Performance: Measured and validated in each story (CoreML <100ms, LLM <5s, total <6s)
- Error handling: Graceful degradation if Ollama unavailable, logging at each failure point
- Configuration: Blacklist, thresholds, model paths all configurable

---

---
