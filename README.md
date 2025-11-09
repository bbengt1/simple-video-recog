# Local Video Recognition System

A privacy-first, M1-optimized video recognition system that uses local LLM (Ollama) to analyze RTSP camera feeds and provide semantic understanding of events in monitored spaces.

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![macOS](https://img.shields.io/badge/platform-macOS%2012+-red.svg)](https://www.apple.com/macos/)
[![Apple Silicon](https://img.shields.io/badge/hardware-M1/M2/M3-green.svg)](https://www.apple.com/mac/)

## 🎯 What It Does

This system transforms basic security cameras into intelligent monitors that understand **what** is happening, not just **that** something moved. Using a hybrid pipeline of computer vision and vision language models, it provides natural language descriptions like:

> *"Person in blue shirt carrying brown package approaching front door at 2:34pm"*

Instead of basic alerts like *"Motion detected"* or *"Object: person (87% confidence)"*.

## 🚀 Key Features

- **100% Local Processing** - Zero cloud dependencies, all data stays on-premises
- **Apple Silicon Optimized** - Leverages M1/M2/M3 Neural Engine for fast inference
- **Motion-Triggered Intelligence** - Processes <1% of frames using smart filtering
- **Semantic Understanding** - Vision LLMs provide contextual event descriptions
- **Multi-Format Logging** - JSON for programmatic access, plaintext for human review
- **Annotated Images** - Visual verification with bounding boxes and labels
- **Event De-duplication** - Prevents alert fatigue from continuous motion
- **Production Ready** - Graceful shutdown, signal handling, comprehensive error messages

## 🏗️ Architecture

```
RTSP Stream → Motion Detection → Frame Sampling → CoreML Object Detection → LLM Analysis → Multi-Format Output
     ↓              ↓              ↓              ↓                      ↓              ↓
   Camera       OpenCV       Configurable    Apple Neural        Ollama/LLaVA    JSON + Plaintext
   Feed         Background    Rate (every    Engine (<100ms)      Vision Model    Logs + Images
                Subtraction   Nth frame)     Filtering            (<5s inference)
```

## 📋 Requirements

### Hardware
- **macOS 12+** (Monterey or newer)
- **Apple Silicon** (M1/M2/M3 processors)
- **256GB+ SSD** (for event logs and images)
- **RTSP-compatible IP camera** (1080p @ 15fps minimum)

### Software
- **Python 3.10+**
- **Ollama** (local LLM service)
- **Vision model** (LLaVA, Moondream, or similar)

## 🛠️ Quick Start

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/bbengt1/simple-video-recog.git
cd simple-video-recog

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Install and Setup Ollama

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# In another terminal, pull a vision model
ollama pull llava:latest
# or
ollama pull moondream
```

### 3. Configure Your Camera

```bash
# Copy example configuration
cp config/config.example.yaml config.yaml

# Edit configuration with your camera details
nano config.yaml
```

Example configuration:
```yaml
camera:
  rtsp_url: "rtsp://192.168.1.100:554/stream"
  username: "admin"
  password: "your_password"

processing:
  motion_threshold: 25
  frame_sampling_rate: 10
  object_blacklist: ["cat", "tree"]

models:
  coreml_model: "models/yolov3.mlmodel"
  ollama_model: "llava:latest"

storage:
  max_storage_gb: 4
```

### 4. Download CoreML Models

```bash
# Create models directory
mkdir -p models

# Download or convert CoreML object detection models
# See docs for model sources and conversion instructions
```

### 5. Test Configuration

```bash
# Validate setup without starting processing
python main.py --dry-run config.yaml
```

### 6. Start Processing

```bash
# Begin video recognition
python main.py config.yaml
```

## 📖 Usage

### Command Line Options

```bash
python main.py [OPTIONS] [CONFIG_FILE]

Options:
  -c, --config PATH        Path to YAML configuration file (default: config.yaml)
  -d, --dry-run           Validate configuration and connectivity without processing
  -v, --version           Show version information
  -h, --help              Show help message
  --log-level LEVEL       Override logging level (DEBUG, INFO, WARNING, ERROR)
  --metrics-interval SEC  Override metrics display interval in seconds (default: 60)
```

### Example Commands

```bash
# Basic usage with default config
python main.py

# Use specific config file
python main.py config/front-door.yaml

# Dry run to validate setup
python main.py --dry-run config.yaml

# Debug mode with verbose logging
python main.py --log-level DEBUG config.yaml

# Show version information
python main.py --version
```

## 📊 Output Formats

### JSON Logs
Structured data for programmatic access:
```json
{
  "timestamp": "2025-11-08T14:32:15Z",
  "event_id": "evt_12345",
  "camera": "front_door",
  "detected_objects": [
    {"label": "person", "confidence": 0.92, "bbox": [100, 150, 200, 400]},
    {"label": "package", "confidence": 0.87, "bbox": [180, 380, 250, 450]}
  ],
  "llm_description": "Person in blue shirt carrying brown package approaching front door",
  "image_path": "data/events/2025-11-08/evt_12345.jpg"
}
```

### Plaintext Logs
Human-readable summaries:
```
[2025-11-08 14:32:15] EVENT: Person detected at front door (confidence: 92%)
  - Objects: person (92%), package (87%)
  - Description: Person in blue shirt carrying brown package approaching front door
  - Image: data/events/2025-11-08/evt_12345.jpg
```

### Annotated Images
Visual verification with bounding boxes and labels saved as JPEG files.

## ⚙️ Configuration

### Core Settings

| Setting | Description | Default | Example |
|---------|-------------|---------|---------|
| `camera.rtsp_url` | RTSP stream URL | - | `"rtsp://192.168.1.100:554/stream"` |
| `camera.username` | Camera username | - | `"admin"` |
| `camera.password` | Camera password | - | `"password123"` |
| `processing.motion_threshold` | Motion sensitivity (0-255) | `25` | `15` (more sensitive) |
| `processing.frame_sampling_rate` | Process every Nth frame | `10` | `5` (more frequent) |
| `processing.object_blacklist` | Objects to ignore | `[]` | `["cat", "tree", "bird"]` |
| `models.coreml_model` | Path to CoreML model | - | `"models/yolov3.mlmodel"` |
| `models.ollama_model` | Ollama vision model | - | `"llava:latest"` |
| `storage.max_storage_gb` | Maximum storage limit | `4` | `8` |

### Advanced Configuration

```yaml
# Event de-duplication
processing:
  event_suppression_window: 30  # seconds

# Performance tuning
processing:
  confidence_threshold: 0.5     # Minimum object confidence
  llm_timeout: 10               # LLM inference timeout (seconds)

# Logging
logging:
  level: "INFO"                 # DEBUG, INFO, WARNING, ERROR
  console: true                 # Enable console output
  file: "logs/app.log"          # Optional file logging

# Storage management
storage:
  min_retention_days: 7         # Keep at least 7 days of data
  storage_check_interval: 100   # Check storage every N events
```

## 🔧 Troubleshooting

### Common Issues

**"Ollama service not running"**
```bash
# Start Ollama service
ollama serve

# In another terminal, verify it's running
curl http://localhost:11434/api/tags
```

**"CoreML model not found"**
```bash
# Check if model file exists
ls -la models/

# Download or convert a CoreML model
# See documentation for model sources
```

**"RTSP connection failed"**
- Verify camera IP address and port
- Check username/password credentials
- Ensure camera supports RTSP protocol
- Test connection with VLC: `vlc rtsp://username:password@ip:port/stream`

**"High CPU usage"**
- Increase `frame_sampling_rate` (process fewer frames)
- Raise `motion_threshold` (reduce motion sensitivity)
- Check for thermal throttling on M1

**"Storage limit exceeded"**
- Reduce `max_storage_gb` in configuration
- The system will automatically rotate old logs when limit is reached
- Manually clean old data: `rm -rf data/events/2025-10-*`

### Performance Tuning

**For better accuracy:**
- Lower `motion_threshold` (more sensitive motion detection)
- Decrease `frame_sampling_rate` (process more frames)
- Use higher confidence models in Ollama

**For better performance:**
- Increase `motion_threshold` (less sensitive, fewer triggers)
- Raise `frame_sampling_rate` (process fewer frames)
- Use faster Ollama models (Moondream vs LLaVA)

### Logs and Debugging

```bash
# Enable debug logging
python main.py --log-level DEBUG config.yaml

# Check recent logs
tail -f logs/app.log

# View system status
python main.py --dry-run config.yaml
```

## 📈 Performance

### Benchmarks (M1 MacBook Pro)
- **CoreML Inference:** <100ms per frame
- **LLM Inference:** <5 seconds per event
- **CPU Usage:** <30% average during operation
- **Memory Usage:** <8GB peak
- **Storage:** <4GB for 30 days of typical activity
- **Thermal:** <70°C sustained operation

### System Requirements
- **Motion Detection:** Reduces processing load by >90%
- **Frame Sampling:** Configurable rate (every 5-20 frames)
- **Event Rate:** ~10 events/day typical usage
- **Uptime:** 24/7 continuous operation supported

## 🧪 Testing

### Test Coverage
- **Unit Tests:** Core logic (motion detection, configuration, event processing)
- **Integration Tests:** End-to-end pipeline with test RTSP streams
- **Performance Tests:** NFR validation (inference speed, resource usage)
- **Reliability Tests:** 24hr uptime, graceful shutdown, data integrity

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov-report=html

# Run specific test categories
pytest tests/performance/    # Performance benchmarks
pytest tests/reliability/    # Uptime and stability
pytest tests/security/       # Privacy and isolation
```

## 🏛️ Architecture

### Core Components

- **`core/`** - Platform-independent processing logic
  - `motion.py` - OpenCV background subtraction
  - `pipeline.py` - Processing orchestration
  - `events.py` - Event de-duplication and logging

- **`platform/`** - Apple Silicon optimizations
  - `coreml_detector.py` - Neural Engine object detection
  - `thermal.py` - Temperature monitoring

- **`integrations/`** - External service clients
  - `rtsp.py` - Camera stream handling
  - `ollama.py` - LLM service integration

### Data Flow

1. **RTSP Capture** - Continuous frame streaming from camera
2. **Motion Detection** - OpenCV filters static scenes (>90% reduction)
3. **Frame Sampling** - Configurable rate optimization
4. **CoreML Inference** - Fast object detection on Neural Engine
5. **LLM Analysis** - Semantic understanding via Ollama
6. **Event Logging** - Multi-format output (JSON, plaintext, images)

### Storage Structure

```
data/
├── events/                    # Event data by date
│   ├── 2025-11-08/
│   │   ├── events.json       # JSON Lines format
│   │   ├── events.log        # Human-readable logs
│   │   └── evt_12345.jpg     # Annotated images
│   └── 2025-11-07/
├── events.db                 # SQLite database
└── config.yaml              # Configuration file
```

## 🤝 Contributing

### Development Setup

```bash
# Fork and clone
git clone https://github.com/yourusername/simple-video-recog.git
cd simple-video-recog

# Set up development environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest

# Start coding
```

### Code Standards

- **Python:** Type hints, Google-style docstrings, Black formatting
- **Testing:** pytest with ≥70% coverage
- **Documentation:** Inline comments, README updates
- **Commits:** Conventional commits, atomic changes

### Architecture Guidelines

- **Separation of Concerns:** Core logic platform-independent
- **Dependency Injection:** Abstract interfaces for testability
- **Configuration-Driven:** No hardcoded values
- **Error Handling:** Graceful degradation with clear messages

## 📚 Documentation

### User Guides
- [Setup Instructions](docs/setup.md) - Complete installation guide
- [Configuration Reference](docs/configuration.md) - All config parameters
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

### Technical Documentation
- [Architecture Overview](docs/architecture.md) - System design and components
- [API Reference](docs/api.md) - Internal APIs and interfaces
- [Performance Guide](docs/performance.md) - Optimization and benchmarking

### Development
- [Contributing Guide](docs/contributing.md) - Development workflow
- [Testing Strategy](docs/testing.md) - Test organization and execution
- [Release Process](docs/release.md) - Versioning and deployment

## 🔒 Security & Privacy

### Privacy-First Design

- **Zero External Calls:** All processing local, no cloud APIs
- **Data Ownership:** Complete control over video data and logs
- **Network Isolation:** RTSP traffic only, no internet connectivity required
- **Local Storage:** SQLite database and filesystem logs

### Security Measures

- **Input Validation:** YAML configuration schema validation
- **Error Handling:** No stack traces in production logs
- **Resource Limits:** Automatic shutdown on storage/CPU limits
- **Access Control:** Localhost-only operation (no remote access)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Apple** for CoreML and Neural Engine optimization
- **Ollama** for local LLM deployment
- **OpenCV** for computer vision foundation
- **Vision Language Models** community for LLaVA, Moondream, and similar models

## 📞 Support

### Getting Help

1. **Check Documentation:** Review [troubleshooting guide](docs/troubleshooting.md)
2. **Search Issues:** Check existing [GitHub issues](https://github.com/bbengt1/simple-video-recog/issues)
3. **Create Issue:** For bugs or feature requests
4. **Community:** Join discussions in [GitHub Discussions](https://github.com/bbengt1/simple-video-recog/discussions)

### Reporting Issues

When reporting bugs, please include:
- System information (macOS version, M1/M2/M3, Python version)
- Configuration file (with sensitive data redacted)
- Error messages and stack traces
- Steps to reproduce the issue

## 🚀 Roadmap

### MVP (Current)
- ✅ Single RTSP camera support
- ✅ Motion-triggered processing
- ✅ CoreML object detection
- ✅ Ollama LLM integration
- ✅ Multi-format event logging
- ✅ CLI interface with configuration

### Phase 2 (Web Dashboard)
- 🔄 Multi-camera support
- 🔄 Real-time web interface
- 🔄 Event search and filtering
- 🔄 Video clip extraction
- 🔄 Home automation webhooks

### Future Enhancements
- 🔄 Advanced analytics and patterns
- 🔄 Custom model fine-tuning
- 🔄 Mobile companion app
- 🔄 Multi-platform support (Linux ARM64)

---

**Built with ❤️ for privacy-conscious developers and ML learners**