# Local Video Recognition System

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/platform-macOS%20(Apple%20Silicon)-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)

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
- **Ollama:** Local LLM service for semantic event descriptions

### Ollama Setup

**1. Install Ollama:**
```bash
brew install ollama
```

**2. Start Ollama Service:**
```bash
ollama serve
```

**3. Download Vision Model:**
```bash
# Pull LLaVA model (recommended for vision tasks)
ollama pull llava:7b

# Alternative: Pull MoonDream model
ollama pull moondream:latest
```

**4. Verify Installation:**
```bash
# Check available models
ollama list

# Expected output includes your downloaded model:
# NAME                    ID      SIZE    MODIFIED
# llava:7b                8dd30f6b0cb1    4.7 GB  2 minutes ago
```

## Setup Instructions

### 1. Clone Repository

```bash
git clone <repository-url>
cd video-recognition
```

### 2. Create Conda Environment (Recommended for CoreML)

```bash
# Install Miniconda (if not already installed)
# Download from: https://docs.conda.io/en/latest/miniconda.html

# Create conda environment
conda create -n video-recog python=3.12 -y

# Activate conda environment
conda activate video-recog
```

**Note:** Use conda instead of venv for CoreML support on Apple Silicon. Virtual environments cannot access the system CoreML framework.

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

### 5. Download CoreML Models

The system uses CoreML models optimized for Apple's Neural Engine to perform fast, on-device object detection.

#### Recommended Models

**YOLOv3-Tiny (Recommended for MVP):**
- **Performance:** ~30-50ms inference on M1/M2
- **Accuracy:** Good balance of speed and detection quality
- **Size:** ~34MB
- **Objects:** Detects 80 COCO classes (person, car, dog, etc.)

**YOLOv8n (Alternative):**
- **Performance:** ~20-40ms inference on M1/M2
- **Accuracy:** Better detection quality than YOLOv3-Tiny
- **Size:** ~22MB
- **Objects:** Detects 80 COCO classes

#### Obtaining CoreML Models

**Option 1: Apple's Model Gallery (Recommended)**
Visit Apple's CoreML model gallery and download pre-converted models:
- [Apple CoreML Models](https://developer.apple.com/machine-learning/models/)
- Search for "YOLO" or "Object Detection"
- Download the .mlmodel file and place in `models/` directory

**Option 2: Convert from PyTorch/TensorFlow**
If you have custom-trained models, convert them using coremltools:

```bash
# Install coremltools (already included in requirements.txt)
pip install coremltools

# Convert YOLOv5 PyTorch model (example)
import coremltools as ct
import torch

# Load your PyTorch model
model = torch.load('yolov5s.pt')['model']

# Convert to CoreML
mlmodel = ct.convert(model, inputs=[ct.ImageType()])
mlmodel.save('models/yolov5s.mlmodel')
```

**Option 3: Download Pre-converted Models**
Community-converted models are available on GitHub:
- [YOLOv3-Tiny CoreML](https://github.com/hollance/YOLO-CoreML-MPSNNGraph)
- [YOLOv8 CoreML](https://github.com/john-rocky/CoreML-Models)

#### Model Requirements

- **Format:** .mlmodel file (CoreML format)
- **Compatibility:** Must support Apple's Neural Engine for optimal performance
- **Input:** Single image input (typically 416x416 or 640x640)
- **Output:** Object detection results (bounding boxes, classes, confidence scores)
- **Optimization:** Use models with `compute_unit = "ALL"` for Neural Engine support

#### Model Validation

After downloading a model, the system will automatically validate:
- ✅ Neural Engine compatibility
- ⚠️  CPU/GPU fallback warning (if not ANE-compatible)
- 📊 Warm-up inference timing (<100ms target)

**Example successful load:**
```
[INFO] ✓ CoreML model loaded: YOLOv3-Tiny (ANE-compatible)
[INFO] Model input shape: (1, 416, 416, 3)
[INFO] Model warm-up completed in 0.034s
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
# Activate conda environment
conda activate video-recog

# Start the system
python main.py --config config/config.yaml
```

The system will:
1. Load and validate your configuration
2. Perform startup health checks
3. Connect to your RTSP camera
4. Begin monitoring for motion events
5. Log detected events to console

**To stop the system:** Press `Ctrl+C` for graceful shutdown with session summary.

**Signal Handling:**
- `Ctrl+C` (SIGINT) or `kill -TERM <pid>` (SIGTERM): Graceful shutdown with cleanup
- `kill -HUP <pid>` (SIGHUP): Hot reload configuration without restarting
- All signals trigger proper resource cleanup and session statistics logging

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
- **Signal Not Handled:** Ensure process is running in foreground (not background)
- **Hot Reload Fails:** Check configuration file syntax and permissions
- **Shutdown Hangs:** Check for stuck RTSP connections or database locks

## Signal Handling and Hot Reload

The system supports comprehensive signal handling for production deployment and maintenance operations.

### Shutdown Signals

**Graceful Shutdown (SIGINT/SIGTERM):**
- `Ctrl+C` (SIGINT) or `kill -TERM <pid>` (SIGTERM)
- Triggers complete cleanup sequence:
  - Stops frame processing pipeline
  - Flushes pending events to database
  - Closes RTSP camera connection
  - Saves final metrics snapshot
  - Logs session summary with statistics
- 10-second timeout with force exit if cleanup hangs

**Session Summary Output:**
```
[INFO] Shutdown signal received, stopping processing...
[INFO] Processing pipeline stopped gracefully
[INFO] Session Summary:
  Runtime: 1h 23m 45s
  Total frames: 67,890
  Events detected: 23
  Average FPS: 14.2
  Storage used: 2.3 GB
```

### Hot Reload (SIGHUP)

**Configuration Reload:**
- `kill -HUP <pid>` triggers live configuration reload
- Re-reads `config/config.yaml` without restarting
- Supports dynamic updates for:
  - Camera RTSP URL changes (reconnects automatically)
  - CoreML model path changes (reloads model)
  - Ollama model changes (reconnects client)
  - Motion detection thresholds
  - Frame sampling rates

**Reload Process:**
1. Signal received → pause processing
2. Load new configuration
3. Validate new settings
4. Reconnect external services (RTSP, Ollama)
5. Reload CoreML model if path changed
6. Resume processing with new configuration

**Reload Failure Handling:**
- Falls back to previous configuration if reload fails
- Logs detailed error information
- Continues processing without interruption

### Production Usage

**Systemd Service Example:**
```bash
# Send shutdown signal
sudo systemctl stop video-recognition

# Trigger hot reload
sudo kill -HUP $(pgrep -f "python main.py")
```

**Docker Container:**
```bash
# Graceful shutdown
docker stop video-recognition

# Hot reload (if running in foreground)
docker kill -s HUP video-recognition
```

## Web Dashboard

The system includes a FastAPI-based web server that provides a dashboard for viewing events and system status without requiring direct database access.

### Starting the Web Server

**1. Ensure the main application has been run first:**
```bash
python main.py --config config/config.yaml
# Let it run for a few minutes to create the database
# Press Ctrl+C to stop
```

**2. Start the web server:**
```bash
python web_server.py
```

**3. Access the dashboard:**
- **Dashboard:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/health

### Web Server Features

- **Event Dashboard:** View recent events with images and descriptions
- **System Health:** Real-time health monitoring and uptime tracking
- **API Access:** RESTful endpoints for programmatic event access
- **Static File Serving:** CSS, JavaScript, and event images
- **Auto-generated Documentation:** Interactive API docs via Swagger/ReDoc

### Configuration

**Environment Variables:**
- `WEB_PORT`: Server port (default: 8000)
- `DEV_MODE`: Enable development mode with auto-reload (default: disabled)

**Security Notes:**
- Server binds to `127.0.0.1` (localhost only)
- Database connections are read-only
- No authentication required for local access

### API Endpoints

**Health Check:**
```bash
GET /api/health
```
Returns system status, database connectivity, and uptime information.

**Event Access (Future - Story 5.2):**
```bash
GET /api/events
GET /api/events/{event_id}
```

## Development

*Placeholder - will be filled in Story 1.7*

## Deployment

*Placeholder - will be filled in Epic 4*

## Project Structure

```
video-recognition/
├── api/                 # FastAPI web server and REST API
├── core/                # Platform-independent business logic
├── apple_platform/      # Apple Silicon-specific implementations
├── integrations/        # External service clients (Ollama, RTSP)
├── web/                 # Static web assets (HTML, CSS, JS)
├── config/              # Configuration files
├── tests/               # Test organization (unit/, integration/, performance/)
├── docs/                # Documentation (PRD, architecture, stories)
├── data/                # Runtime data (gitignored)
├── logs/                # Application logs (gitignored)
├── models/              # CoreML models (gitignored)
├── migrations/          # SQL migration scripts
└── scripts/             # Setup and maintenance scripts
```

## Troubleshooting

### Health Check Validation

The system includes comprehensive startup health checks that validate all dependencies before processing begins. Use the `--dry-run` flag to validate your configuration without starting the processing pipeline:

```bash
# Validate configuration and dependencies
python main.py --dry-run --config config/config.yaml

# Expected successful output:
[STARTUP] Video Recognition System v1.0.0
[CONFIG] ✓ Configuration loaded: camera_name
[PLATFORM] ✓ Platform validated: macOS 14.2 on arm64
[PYTHON] ✓ Python version: 3.12.0
[DEPENDENCIES] ✓ Dependencies: All required packages installed
[MODELS] ✓ CoreML: model loaded
[OLLAMA] ✓ Ollama service running, model 'llava:7b' ready
[CAMERA] ✓ RTSP connected: 1920x1080 @ 30fps (H264)
[STORAGE] ✓ Storage: 2.1GB / 4GB (52%)
[READY] ✓ All health checks passed

# Exit code 0 = success, 2 = validation failed
```

### Common Issues and Solutions

#### ❌ Configuration File Not Found
```
Error: Configuration file not found: config/config.yaml
Please create a config file by copying config.example.yaml:
  cp config/config.example.yaml config/config.yaml
```

**Solution:**
```bash
# Copy the example configuration
cp config/config.example.yaml config/config.yaml

# Edit the configuration with your camera details
nano config/config.yaml
```

#### ❌ Configuration Validation Error
```
Configuration Validation Error in config/config.yaml:
1 validation error for SystemConfig
camera_rtsp_url
  Field required [type=missing, input_value={...}, input_type=dict]
```

**Solution:** Check your YAML syntax and ensure all required fields are present. Required fields include:
- `camera_rtsp_url`: RTSP stream URL
- `camera_id`: Unique camera identifier
- `ollama_model`: LLM model name

#### ❌ Platform Not Supported
```
[PLATFORM] ✗ Platform: unsupported
```

**Solution:** This system requires:
- macOS 13+ (Ventura or later)
- Apple Silicon processor (M1, M2, or M3)

#### ❌ Python Version Too Old
```
[PYTHON] ✗ Python error: Python 3.10+ required, detected 3.9.7
```

**Solution:** Upgrade Python to version 3.10 or higher:
```bash
# Install Python 3.12 via Homebrew
brew install python@3.12

# Create new virtual environment with Python 3.12
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### ❌ Dependency Errors
```
[DEPENDENCIES] ✗ Dependency errors: OpenCV 4.12.0 < 4.8.1
```

**Solution:** Update dependencies:
```bash
# Upgrade all packages
pip install --upgrade -r requirements.txt

# Or upgrade specific package
pip install --upgrade opencv-python
```

#### ❌ CoreML Model Not Found
```
[MODELS] ✗ CoreML model not found: models/yolov8n.mlmodel
```

**Solution:** Download and place CoreML models:
```bash
# Create models directory
mkdir -p models

# Download YOLOv8n CoreML model
# Visit: https://github.com/ultralytics/yolov8/releases
# Download: yolov8n.mlmodel and place in models/ directory
```

#### ❌ Ollama Service Not Running
```
[OLLAMA] ✗ Ollama service check failed: Connection refused
```

**Solution:** Start Ollama service:
```bash
# Start Ollama in background
ollama serve

# In another terminal, verify service is running
curl http://localhost:11434/api/tags

# Pull required vision model
ollama pull llava:7b
```

#### ❌ RTSP Connection Failed
```
[CAMERA] ✗ RTSP connection timeout: Unable to connect within 10s
```

**Solutions:**
1. **Check camera URL:** Verify RTSP URL format and credentials
2. **Network connectivity:** Ensure camera is accessible from your Mac
3. **Firewall settings:** Check if RTSP port (usually 554) is blocked
4. **Camera compatibility:** Ensure camera supports RTSP streaming

**Test RTSP connection:**
```bash
# Test with VLC or ffplay
ffplay rtsp://username:password@camera_ip:554/stream

# Or use OpenCV test
python -c "
import cv2
cap = cv2.VideoCapture('rtsp://username:password@camera_ip:554/stream')
print('Connected:', cap.isOpened())
cap.release()
"
```

#### ❌ Storage Limit Exceeded
```
[STORAGE] ✗ Storage limit exceeded: 615.8GB used, limit is 4.0GB
```

**Solutions:**
1. **Increase storage limit** in config:
   ```yaml
   max_storage_gb: 10.0  # Increase from default 4.0
   ```

2. **Clean up old data:**
   ```bash
   # Remove old event data
   rm -rf data/events/*

   # Remove old logs
   rm -f logs/*.log
   ```

3. **Move data directory** to larger storage:
   ```yaml
   db_path: /Volumes/ExternalDrive/data/events.db
   ```

#### ❌ File Permission Denied
```
[PERMISSIONS] ✗ Write permissions denied for directory: data
```

**Solution:** Fix directory permissions:
```bash
# Fix permissions for required directories
chmod 755 data/
chmod 755 logs/
chmod 755 config/

# Or change ownership if needed
sudo chown -R $USER data/ logs/ config/
```

### Getting Help

If you encounter issues not covered here:

1. **Run dry-run validation:** `python main.py --dry-run --config config/config.yaml`
2. **Check logs:** Review `logs/` directory for detailed error information
3. **Verify environment:** Ensure all prerequisites are installed and configured
4. **Test components individually:** Use the health checks to isolate which component is failing

### Performance Issues

- **High CPU usage:** Reduce `frame_sample_rate` in config (default: 10)
- **Slow inference:** Ensure CoreML model is compatible with Neural Engine
- **Storage filling quickly:** Increase `max_storage_gb` or reduce retention period
- **RTSP lag:** Check network connection and camera settings

## License

*Placeholder*

## Contributing

*Placeholder*
