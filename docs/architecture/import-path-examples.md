# Import Path Examples

**Core module importing another core module:**
```python
# core/event_manager.py
from core.database import DatabaseManager
from core.json_logger import JSONEventLogger
```

**Platform module importing core:**
```python
# platform/coreml_detector.py
from core.config import SystemConfig
```

**Integration importing core:**
```python
# integrations/ollama_client.py
from core.config import SystemConfig
```

**Main entry point:**
```python
# main.py
from core.processing_pipeline import ProcessingPipeline
from core.config import load_config
```

**API server importing core:**
```python
# api/server.py
from core.database import DatabaseManager
from core.metrics import MetricsCollector
from core.config import load_config
```

**Test importing module under test:**
```python
# tests/unit/test_motion_detector.py
from core.motion_detector import MotionDetector
```

---
