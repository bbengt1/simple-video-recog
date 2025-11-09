# CoreML Object Detector

**Responsibility:** Runs CoreML model on Apple Neural Engine to detect objects in frames, extracts bounding boxes and confidence scores, filters by blacklist and minimum confidence.

**Key Interfaces:**
- `detect_objects(frame: np.ndarray) -> list[DetectedObject]`: Run inference, return detected objects
- `load_model(model_path: str) -> None`: Load CoreML model from file
- `is_model_loaded() -> bool`: Check if model is ready for inference

**Dependencies:**
- CoreML Tools (coremltools.models.MLModel)
- Pydantic DetectedObject model
- SystemConfig (for model path, blacklist, min confidence)

**Technology Stack:**
- Python 3.10+, CoreML Tools 7.0+, Vision framework (via coremltools)
- Module path: `platform/coreml_detector.py`
- Class: `CoreMLObjectDetector`

**Implementation Notes:**
- Validates model runs on Apple Neural Engine (ANE) at startup
- Converts frame from BGR (OpenCV) to RGB (CoreML) before inference
- Filters objects by: (1) confidence >= min_object_confidence, (2) label not in blacklist
- Inference target: <100ms per frame (NFR requirement)
- Logs WARNING if inference exceeds 100ms threshold

---
