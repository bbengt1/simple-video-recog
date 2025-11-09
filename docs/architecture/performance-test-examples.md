# Performance Test Examples

```python
# tests/performance/test_coreml_performance.py
"""Performance tests for CoreML inference (NFR validation)."""
import pytest
import numpy as np
import time
from platform.coreml_detector import CoreMLObjectDetector


@pytest.mark.performance
def test_coreml_inference_speed():
    """Validate CoreML inference meets <100ms NFR target."""
    detector = CoreMLObjectDetector("models/yolov8n.mlmodel")
    assert detector.is_model_loaded()

    # Create test frame (640x640 RGB)
    test_frame = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

    # Warm-up inference (first run is slower)
    detector.detect_objects(test_frame)

    # Measure inference time over 100 runs
    inference_times = []
    for _ in range(100):
        start = time.perf_counter()
        objects = detector.detect_objects(test_frame)
        end = time.perf_counter()
        inference_times.append((end - start) * 1000)  # Convert to ms

    # Calculate percentiles
    p50 = np.percentile(inference_times, 50)
    p95 = np.percentile(inference_times, 95)
    p99 = np.percentile(inference_times, 99)

    print(f"\nCoreML Inference Times:")
    print(f"  p50: {p50:.2f}ms")
    print(f"  p95: {p95:.2f}ms")
    print(f"  p99: {p99:.2f}ms")

    # Validate NFR: p95 should be <100ms
    assert p95 < 100.0, f"CoreML p95 inference time {p95:.2f}ms exceeds 100ms target"


@pytest.mark.performance
@pytest.mark.skipif(not ollama_available(), reason="Ollama service not running")
def test_llm_inference_speed():
    """Validate Ollama LLM inference meets <3s NFR target."""
    from integrations.ollama_client import OllamaLLMProcessor

    llm = OllamaLLMProcessor("http://localhost:11434", "llava:7b")
    assert llm.health_check()

    # Create test image and objects
    test_frame = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    test_objects = [
        DetectedObject(label="person", confidence=0.9, bbox=BoundingBox(x=0, y=0, width=100, height=200))
    ]

    # Measure LLM inference time over 10 runs
    inference_times = []
    for _ in range(10):
        start = time.perf_counter()
        description = llm.generate_description(test_frame, test_objects)
        end = time.perf_counter()
        inference_times.append(end - start)

    # Calculate percentiles
    p50 = np.percentile(inference_times, 50)
    p95 = np.percentile(inference_times, 95)

    print(f"\nLLM Inference Times:")
    print(f"  p50: {p50:.2f}s")
    print(f"  p95: {p95:.2f}s")

    # Validate NFR: p95 should be <3s
    assert p95 < 3.0, f"LLM p95 inference time {p95:.2f}s exceeds 3s target"
```

---
