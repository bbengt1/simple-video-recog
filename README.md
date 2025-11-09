# Local Video Recognition System

A privacy-first, local-only video recognition system optimized for Apple Silicon that processes RTSP camera streams using motion detection, CoreML object detection, and local LLM semantic understanding.

## Overview

This system monitors RTSP camera streams, detects motion, identifies objects using on-device CoreML models running on Apple's Neural Engine, and generates semantic descriptions using locally-hosted Ollama LLM models. All processing happens on-device with zero cloud dependencies, ensuring complete privacy and eliminating cloud service costs.

**Key Features:**
- **Privacy-First:** 100% local processing, no cloud services
- **Apple Silicon Optimized:** CoreML models leverage Neural Engine for <100ms inference
- **Motion-Triggered:** Intelligent frame sampling reduces processing overhead
- **Semantic Understanding:** Local LLM generates natural language event descriptions
- **Event Storage:** SQLite database with configurable retention and storage limits
- **Comprehensive Logging:** JSON and plaintext event logs with metrics collection

## Prerequisites

- **Python:** 3.10 or higher
- **Operating System:** macOS 13+ (Ventura or later)
- **Hardware:** Apple Silicon (M1, M2, or M3 processor)
- **Camera:** RTSP-compatible IP camera
- **Ollama:** Local LLM service (installation instructions below)

## Setup Instructions

### 1. Clone Repository

```bash
git clone <repository-url>
cd video-recognition
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment (macOS)
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install runtime dependencies
pip install -r requirements.txt

# Install development dependencies (optional, for testing)
pip install -r requirements-dev.txt
```

### 4. Install Ollama

```bash
# Install Ollama using Homebrew
brew install ollama

# Start Ollama service
ollama serve

# Pull LLM model (in a new terminal)
ollama pull llava:7b
```

### 5. Download CoreML Model

```bash
# Download YOLO CoreML model (placeholder - actual script in Story 4.9)
# scripts/download_models.sh
```

### 6. Configure System

```bash
# Copy example configuration
cp config/config.example.yaml config/config.yaml

# Edit configuration with your camera details and preferences
nano config/config.yaml
```

**Important:** Update the `camera_rtsp_url` field with your actual RTSP camera URL and credentials.

## Quick Start

Once you've completed the setup steps above, you can start the video recognition system:

```bash
# Activate virtual environment
source venv/bin/activate

# Start the system
python main.py config/config.yaml
```

The system will:
1. Load and validate your configuration
2. Perform startup health checks
3. Connect to your RTSP camera
4. Begin monitoring for motion events
5. Log detected events to console

**To stop the system:** Press `Ctrl+C` for graceful shutdown.

**Expected output:**
```
[INFO] Starting video recognition system...
[INFO] Configuration loaded successfully
[INFO] Connected to RTSP stream: front_door
[INFO] Motion detector initialized
[INFO] System initialization complete. Starting processing pipeline...
[INFO] Starting video processing pipeline
[INFO] Motion detected: frame=1, confidence=0.234
...
```

## Configuration Guide

The `config/config.yaml` file contains all system settings. Key parameters:

### Camera Configuration
- `camera_rtsp_url`: RTSP stream URL with authentication (format: `rtsp://username:password@ip:port/stream`)
- `camera_id`: Identifier for this camera (useful for multi-camera setups in future)

### Motion Detection
- `motion_threshold`: Sensitivity (0.0-1.0, lower = more sensitive)
- `frame_sample_rate`: Frames per second to process during motion events (1-30)

### Object Detection
- `coreml_model_path`: Path to CoreML model file
- `blacklist_objects`: Object labels to filter out (e.g., `["bird", "cat"]`)
- `min_object_confidence`: Minimum confidence score to include detections (0.0-1.0)

### LLM Configuration
- `ollama_base_url`: Ollama API endpoint (default: `http://localhost:11434`)
- `ollama_model`: LLM model name (`llava:7b` or `moondream:latest`)
- `llm_timeout`: Request timeout in seconds (1-60)

### Storage
- `db_path`: SQLite database file path
- `max_storage_gb`: Maximum storage limit in GB
- `min_retention_days`: Minimum days to retain events before cleanup

### Logging
- `log_level`: Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- `metrics_interval`: Metrics collection interval in seconds (minimum: 10)

See `config/config.example.yaml` for detailed parameter descriptions and valid ranges.

## Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all unit tests
pytest tests/unit -v

# Run tests with coverage report (terminal output)
pytest --cov=core --cov=integrations --cov-report=term

# Generate HTML coverage report
pytest --cov=core --cov=integrations --cov-report=html
open htmlcov/index.html

# Run integration tests
pytest tests/integration -v

# Run all tests (unit + integration)
pytest -v

# Run tests with verbose output and coverage
pytest --cov=core --cov=integrations --cov-report=term -v
```

## Integration Testing

### RTSP Camera Connection Test

To verify RTSP camera connectivity and frame capture functionality:

**Prerequisites:**
- RTSP-compatible IP camera accessible on your network
- Camera credentials (username and password)

**Test Procedure:**

1. **Configure Real RTSP Camera:**

   Edit `config/config.yaml` with your camera details:
   ```yaml
   camera_rtsp_url: "rtsp://username:password@camera-ip:port/stream"
   camera_id: "test_camera"
   ```

2. **Example Camera URLs:**

   ```yaml
   # Hikvision
   camera_rtsp_url: "rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101"

   # Reolink
   camera_rtsp_url: "rtsp://admin:password@192.168.1.100:554/h264Preview_01_main"

   # Generic RTSP Camera
   camera_rtsp_url: "rtsp://username:password@192.168.1.100:554/stream1"
   ```

3. **Run Integration Test:**

   Create a simple test script (`test_rtsp_integration.py`):
   ```python
   from core.config import load_config
   from integrations.rtsp_client import RTSPCameraClient
   import time
   import logging

   logging.basicConfig(level=logging.INFO)

   # Load configuration
   config = load_config("config/config.yaml")

   # Create RTSP client
   client = RTSPCameraClient(config)

   # Connect to camera
   client.connect()

   # Start capture thread
   client.start_capture()

   # Capture frames for 60 seconds
   start_time = time.time()
   frame_count = 0

   while time.time() - start_time < 60:
       frame = client.get_latest_frame()
       if frame is not None:
           frame_count += 1
       time.sleep(0.1)

   # Stop capture
   client.stop_capture()
   client.disconnect()

   # Calculate and display results
   elapsed = time.time() - start_time
   fps = frame_count / elapsed

   print(f"\n=== Integration Test Results ===")
   print(f"Duration: {elapsed:.1f}s")
   print(f"Frames captured: {frame_count}")
   print(f"Average FPS: {fps:.1f}")
   print(f"Expected: ~15 fps (varies by camera)")
   ```

4. **Expected Results:**

   - **Connection Log:** Check logs for "Connected to RTSP stream: [camera_id]"
   - **Frame Capture Rate:** ~15 fps (actual rate varies by camera model and network)
   - **No Errors:** No RTSPConnectionError exceptions during 60-second test
   - **Graceful Shutdown:** Clean disconnect with "Disconnected from RTSP stream" log

5. **Verify Frame Capture:**

   - Monitor logs for successful frame capture
   - Queue size should remain below 100 frames
   - No "Frame queue full" warnings during normal operation

**Troubleshooting:**

- **Connection Fails:** Verify camera IP, port, and credentials
- **Authentication Error:** Check username/password in RTSP URL
- **Network Timeout:** Ensure camera is reachable (try `ping camera-ip`)
- **Low FPS:** Check network bandwidth and camera configuration

## Development

*Placeholder - will be filled in Story 1.7*

## Deployment

*Placeholder - will be filled in Epic 4*

## Project Structure

```
video-recognition/
├── core/                # Platform-independent business logic
├── platform/            # Apple Silicon-specific implementations
├── integrations/        # External service clients (Ollama, RTSP)
├── config/              # Configuration files
├── tests/               # Test organization (unit/, integration/, performance/)
├── docs/                # Documentation (PRD, architecture)
├── data/                # Runtime data (gitignored)
├── logs/                # Application logs (gitignored)
├── models/              # CoreML models (gitignored)
├── migrations/          # SQL migration scripts
└── scripts/             # Setup and maintenance scripts
```

## License

*Placeholder*

## Contributing

*Placeholder*
