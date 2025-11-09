# Environment Variables

**`.env.example` (committed):**
```bash
# Camera Configuration
CAMERA_RTSP_URL="rtsp://admin:password@192.168.1.100:554/stream1"
CAMERA_ID="front_door"

# Ollama Configuration
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL="llava:7b"

# Database
DB_PATH="data/events.db"

# Storage
MAX_STORAGE_GB="4.0"

# Logging
LOG_LEVEL="INFO"
```

**`.env` (gitignored, created by developer):**
```bash
# Copy from .env.example and fill in actual credentials
CAMERA_RTSP_URL="rtsp://admin:MyRealPassword@192.168.1.100:554/stream1"
CAMERA_ID="garage_camera"
OLLAMA_MODEL="moondream:latest"
```

**Loading in Python:**
```python
# core/config.py
from pydantic_settings import BaseSettings

class SystemConfig(BaseSettings):
    camera_rtsp_url: str
    camera_id: str = "camera_1"
    # ... other fields

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

---
