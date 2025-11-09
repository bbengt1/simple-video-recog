# Environment Configuration

## Required Environment Variables

```bash
# Frontend (.env.local) - Not needed for Phase 1
# Phase 2 only, for web dashboard development
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws/events

# Backend (.env)
# Camera Configuration
CAMERA_RTSP_URL=rtsp://username:password@camera-ip:554/stream1
CAMERA_ID=front_door

# Motion Detection
MOTION_THRESHOLD=0.5
FRAME_SAMPLE_RATE=5

# Object Detection
COREML_MODEL_PATH=models/yolov8n.mlmodel
BLACKLIST_OBJECTS=bird,cat
MIN_OBJECT_CONFIDENCE=0.5

# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llava:7b
LLM_TIMEOUT=10

# Storage
DB_PATH=data/events.db
MAX_STORAGE_GB=4.0
MIN_RETENTION_DAYS=7

# Logging
LOG_LEVEL=INFO
METRICS_INTERVAL=60

# Shared (Backend + Frontend)
# None for Phase 1/2 - all config is backend-only
# Future: Phase 3 may introduce shared API keys, feature flags, etc.
```

**Environment Variable Loading:**
- Backend: Loaded via Pydantic Settings (`core/config.py`)
- Frontend: Not used in Phase 1; Phase 2 uses browser environment (no env vars)
- Precedence: `.env` file < environment variables < command-line arguments

**Validation:**
- Missing required variables: Application exits with clear error message
- Invalid values: Pydantic raises ValidationError with field-specific details
- Example error: `ValidationError: 1 validation error for SystemConfig\nmotion_threshold\n  ensure this value is between 0.0 and 1.0 (type=value_error.number.not_in_range)`

---
