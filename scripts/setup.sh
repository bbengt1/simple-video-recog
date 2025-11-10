#!/bin/bash
# Setup script for Local Video Recognition System
# Automates initial setup and dependency installation

set -e  # Exit on error

echo "================================================"
echo "Local Video Recognition System - Setup"
echo "================================================"
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "  $1"
}

# Check if running on macOS
echo "[1/8] Checking platform compatibility..."
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This system requires macOS. Detected: $OSTYPE"
    exit 1
fi

# Check for Apple Silicon
ARCH=$(uname -m)
if [[ "$ARCH" != "arm64" ]]; then
    print_error "This system requires Apple Silicon (M1/M2/M3). Detected: $ARCH"
    print_info "Intel Macs are not supported (no Neural Engine)"
    exit 1
fi

print_success "Platform: macOS on Apple Silicon ($ARCH)"

# Check Python version
echo ""
echo "[2/8] Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found. Please install Python 3.10 or later:"
    print_info "brew install python@3.10"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 10 ]]; then
    print_error "Python 3.10+ required. Detected: Python $PYTHON_VERSION"
    print_info "Upgrade with: brew install python@3.10"
    exit 1
fi

print_success "Python version: $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "[3/8] Creating virtual environment..."
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists (venv/)"
    read -p "  Recreate it? This will delete existing venv. [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        print_success "Virtual environment recreated"
    else
        print_info "Using existing virtual environment"
    fi
else
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "[4/8] Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Install dependencies
echo ""
echo "[5/8] Installing Python dependencies..."
print_info "This may take a few minutes..."
if pip install -r requirements.txt > /dev/null 2>&1; then
    print_success "Runtime dependencies installed"
else
    print_error "Failed to install dependencies"
    print_info "Try running manually: pip install -r requirements.txt"
    exit 1
fi

# Install development dependencies if available
if [ -f "requirements-dev.txt" ]; then
    print_info "Installing development dependencies..."
    if pip install -r requirements-dev.txt > /dev/null 2>&1; then
        print_success "Development dependencies installed"
    else
        print_warning "Failed to install dev dependencies (optional)"
    fi
fi

# Create required directories
echo ""
echo "[6/8] Creating required directories..."
mkdir -p data/events
mkdir -p logs
mkdir -p config
mkdir -p models

print_success "Directories created: data/, logs/, config/, models/"

# Copy example configuration
echo ""
echo "[7/8] Setting up configuration..."
if [ -f "config/config.yaml" ]; then
    print_warning "config/config.yaml already exists"
    read -p "  Overwrite with example config? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp config/config.example.yaml config/config.yaml
        print_success "Configuration file created from example"
    else
        print_info "Keeping existing config/config.yaml"
    fi
else
    cp config/config.example.yaml config/config.yaml
    print_success "Configuration file created: config/config.yaml"
fi

# Check for Ollama
echo ""
echo "[8/8] Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    print_success "Ollama is installed"

    # Check if Ollama service is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "Ollama service is running"

        # Check for vision models
        MODELS=$(curl -s http://localhost:11434/api/tags | grep -o '"llava\|moondream' | head -1 || echo "")
        if [ -z "$MODELS" ]; then
            print_warning "No vision models found. You'll need to download one:"
            print_info "ollama pull llava:7b"
            print_info "  OR"
            print_info "ollama pull moondream:latest"
        else
            print_success "Vision model available"
        fi
    else
        print_warning "Ollama service not running. Start it with:"
        print_info "ollama serve"
    fi
else
    print_warning "Ollama not installed. Install with:"
    print_info "brew install ollama"
    print_info ""
    print_info "After installing, run:"
    print_info "  ollama serve"
    print_info "  ollama pull llava:7b"
fi

# Final instructions
echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Next Steps:"
echo ""
echo "1. Configure your camera settings:"
echo "   nano config/config.yaml"
echo ""
echo "2. Download a CoreML model for object detection:"
echo "   - See README.md section 'Download CoreML Models'"
echo "   - Place model file in models/ directory"
echo ""
echo "3. Ensure Ollama service is running:"
echo "   ollama serve"
echo "   ollama pull llava:7b"
echo ""
echo "4. Run system validation (dry-run mode):"
echo "   python main.py --dry-run"
echo ""
echo "5. Start the system:"
echo "   python main.py"
echo ""
echo "For more information, see README.md"
echo ""
