# Environments

| Environment | Frontend URL | Backend URL | Purpose |
|-------------|-------------|-------------|---------|
| **Development** | http://localhost:3000 | http://localhost:8000 | Local development on MacBook Pro, uses test RTSP stream or recorded video file |
| **Production** | http://[mac-mini-ip]:3000 | http://[mac-mini-ip]:8000 | 24/7 operation on Mac Mini/Studio with live RTSP camera, accessible on local network only |

**Environment Differences:**

**Development Environment:**
- **Hardware:** M1 MacBook Pro (developer machine)
- **Camera Source:** Test RTSP stream or recorded video file (`data/test-video.mp4`)
- **Ollama Model:** Smaller model (moondream:latest) for faster iteration
- **Storage Limit:** 1GB (lower limit for faster testing)
- **Log Level:** DEBUG (verbose logging for troubleshooting)
- **Startup:** Manual start via `python main.py` or `pytest`

**Production Environment:**
- **Hardware:** Mac Mini or Mac Studio (dedicated 24/7 machine)
- **Camera Source:** Live RTSP camera stream (192.168.1.100)
- **Ollama Model:** Full model (llava:7b) for better accuracy
- **Storage Limit:** 4GB (full limit per NFR)
- **Log Level:** INFO (minimal logging, only warnings/errors)
- **Startup:** Automatic via launchd, restarts on crash

**No Staging Environment:**
- Not needed for personal learning project
- Development → Production is sufficient
- Manual testing on production machine before switching to live camera

**Environment Configuration:**

Development (`.env`):
```bash
CAMERA_RTSP_URL=rtsp://demo:demo@192.168.1.200:554/test
LOG_LEVEL=DEBUG
OLLAMA_MODEL=moondream:latest
MAX_STORAGE_GB=1.0
```

Production (`.env` on Mac Mini):
```bash
CAMERA_RTSP_URL=rtsp://admin:SecurePassword@192.168.1.100:554/stream1
LOG_LEVEL=INFO
OLLAMA_MODEL=llava:7b
MAX_STORAGE_GB=4.0
```

---
