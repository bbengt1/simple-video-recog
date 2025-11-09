# Local Development Setup

## Prerequisites

```bash
# macOS with Apple Silicon (M1/M2/M3)
system_profiler SPHardwareDataType | grep "Chip:"

# Python 3.10 or higher
python3 --version

# Homebrew (for Ollama installation)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Node.js and npm (optional, only needed if using md-tree for PRD sharding)
node --version
npm --version
```

## Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd video-recognition/

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Ollama
brew install ollama

# Start Ollama service (in separate terminal)
ollama serve

# Download vision model (7B parameter model, ~4GB download)
ollama pull llava:7b
# Alternative: Faster but less accurate model
# ollama pull moondream:latest

# Create data and log directories
mkdir -p data/events logs models

# Download CoreML model
bash scripts/download_models.sh

# Copy environment template and configure
cp .env.example .env
nano .env  # Edit with your RTSP camera URL and credentials

# Initialize database
python main.py --dry-run  # Validates config and creates database schema

# Run tests to verify setup
pytest tests/unit -v
```

## Development Commands

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Start processing engine (Phase 1 CLI)
python main.py

# Start processing engine with debug logging
python main.py --log-level DEBUG

# Dry-run mode (validates config, tests connections, doesn't process)
python main.py --dry-run

# Phase 2: Start API server (separate terminal)
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000

# Phase 2: Serve web dashboard (separate terminal)
python -m http.server 3000 --directory web/

# Run all tests
pytest

# Run only unit tests (fast)
pytest tests/unit -v

# Run tests with coverage report
pytest --cov=core --cov=platform --cov=integrations --cov-report=html

# Run performance tests (validates NFRs)
pytest tests/performance -v --log-cli-level=INFO

# Code formatting
black core/ platform/ integrations/ api/ tests/

# Lint code
ruff check core/ platform/ integrations/ api/

# Type checking (optional, Phase 3)
# mypy core/ platform/ integrations/ api/

# Database backup
bash scripts/backup_database.sh

# View database content
sqlite3 data/events.db
# SQL> SELECT * FROM events ORDER BY timestamp DESC LIMIT 10;

# View logs in real-time
tail -f logs/app.log

# View metrics
cat logs/metrics.json | jq .  # Pretty-print JSON Lines
```
