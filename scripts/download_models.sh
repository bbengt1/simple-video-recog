#!/bin/bash
# CoreML Model Download Script
# Downloads and sets up CoreML object detection models for Apple Neural Engine

set -e  # Exit on error

echo "================================================"
echo "CoreML Model Download Utility"
echo "================================================"
echo ""

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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
    echo -e "${BLUE}ℹ${NC} $1"
}

print_step() {
    echo -e "  $1"
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script requires macOS"
    exit 1
fi

# Check for Apple Silicon
ARCH=$(uname -m)
if [[ "$ARCH" != "arm64" ]]; then
    print_warning "Running on $ARCH - Neural Engine acceleration requires Apple Silicon (M1/M2/M3)"
    read -p "  Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting..."
        exit 0
    fi
fi

# Create models directory
mkdir -p models
cd models

echo "Available CoreML Models for Object Detection:"
echo ""
echo "1) YOLOv8n (Recommended)"
echo "   - Performance: ~20-40ms on M1/M2"
echo "   - Accuracy: Excellent"
echo "   - Size: ~22MB"
echo "   - Objects: 80 COCO classes"
echo ""
echo "2) YOLOv8s (Better Accuracy)"
echo "   - Performance: ~40-60ms on M1/M2"
echo "   - Accuracy: Better than YOLOv8n"
echo "   - Size: ~44MB"
echo "   - Objects: 80 COCO classes"
echo ""
echo "3) YOLOv3-Tiny (Fastest)"
echo "   - Performance: ~30-50ms on M1/M2"
echo "   - Accuracy: Good"
echo "   - Size: ~34MB"
echo "   - Objects: 80 COCO classes"
echo ""
echo "4) Custom Model (Manual Download)"
echo "   - Provide your own CoreML model"
echo ""

read -p "Select model to download [1-4]: " MODEL_CHOICE

case $MODEL_CHOICE in
    1)
        echo ""
        print_info "Downloading YOLOv8n CoreML model..."

        MODEL_NAME="yolov8n.mlmodel"
        MODEL_URL="https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.mlmodel"

        if [ -f "$MODEL_NAME" ]; then
            print_warning "Model already exists: $MODEL_NAME"
            read -p "  Re-download? [y/N] " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_info "Using existing model"
            else
                rm "$MODEL_NAME"
                if command -v curl &> /dev/null; then
                    curl -L -o "$MODEL_NAME" "$MODEL_URL" || {
                        print_error "Download failed. Please download manually from:"
                        print_step "$MODEL_URL"
                        exit 1
                    }
                else
                    print_error "curl not found. Please download manually from:"
                    print_step "$MODEL_URL"
                    exit 1
                fi
            fi
        else
            if command -v curl &> /dev/null; then
                curl -L -o "$MODEL_NAME" "$MODEL_URL" || {
                    print_error "Download failed. Please download manually from:"
                    print_step "$MODEL_URL"
                    exit 1
                }
            else
                print_error "curl not found. Please download manually from:"
                print_step "$MODEL_URL"
                exit 1
            fi
        fi

        if [ -f "$MODEL_NAME" ]; then
            MODEL_SIZE=$(du -h "$MODEL_NAME" | cut -f1)
            print_success "Model downloaded: $MODEL_NAME ($MODEL_SIZE)"

            # Verify it's a valid CoreML model
            if file "$MODEL_NAME" | grep -q "CoreML"; then
                print_success "CoreML model format verified"
            else
                print_warning "Could not verify CoreML format (file command limitations)"
            fi
        else
            print_error "Download failed"
            exit 1
        fi
        ;;

    2)
        echo ""
        print_info "Downloading YOLOv8s CoreML model..."

        MODEL_NAME="yolov8s.mlmodel"
        MODEL_URL="https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.mlmodel"

        if [ -f "$MODEL_NAME" ]; then
            print_warning "Model already exists: $MODEL_NAME"
            read -p "  Re-download? [y/N] " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_info "Using existing model"
            else
                rm "$MODEL_NAME"
                if command -v curl &> /dev/null; then
                    curl -L -o "$MODEL_NAME" "$MODEL_URL" || {
                        print_error "Download failed. Please download manually from:"
                        print_step "$MODEL_URL"
                        exit 1
                    }
                else
                    print_error "curl not found. Please download manually from:"
                    print_step "$MODEL_URL"
                    exit 1
                fi
            fi
        else
            if command -v curl &> /dev/null; then
                curl -L -o "$MODEL_NAME" "$MODEL_URL" || {
                    print_error "Download failed. Please download manually from:"
                    print_step "$MODEL_URL"
                    exit 1
                }
            else
                print_error "curl not found. Please download manually from:"
                print_step "$MODEL_URL"
                exit 1
            fi
        fi

        if [ -f "$MODEL_NAME" ]; then
            MODEL_SIZE=$(du -h "$MODEL_NAME" | cut -f1)
            print_success "Model downloaded: $MODEL_NAME ($MODEL_SIZE)"
        else
            print_error "Download failed"
            exit 1
        fi
        ;;

    3)
        echo ""
        print_info "YOLOv3-Tiny CoreML model information"
        print_warning "Direct download link not available"
        print_step ""
        print_step "To obtain YOLOv3-Tiny CoreML model:"
        print_step "1. Visit: https://github.com/hollance/YOLO-CoreML-MPSNNGraph"
        print_step "2. Download the TinyYOLO.mlmodel file"
        print_step "3. Place it in the models/ directory"
        print_step "4. Rename to yolov3-tiny.mlmodel"
        print_step ""
        print_info "Alternative: Convert PyTorch/ONNX model using coremltools"
        ;;

    4)
        echo ""
        print_info "Using custom CoreML model"
        print_step ""
        print_step "Model Requirements:"
        print_step "- Format: .mlmodel (CoreML format)"
        print_step "- Task: Object detection"
        print_step "- Input: Single image (typically 416x416 or 640x640)"
        print_step "- Output: Bounding boxes, classes, confidence scores"
        print_step "- Optimization: Neural Engine compatible (compute_unit='ALL')"
        print_step ""
        print_step "Conversion from PyTorch/TensorFlow:"
        print_step "1. Install: pip install coremltools"
        print_step "2. Convert your model using coremltools.convert()"
        print_step "3. Place .mlmodel file in models/ directory"
        print_step "4. Update config.yaml with model path"
        print_step ""
        print_info "See README.md for detailed conversion instructions"
        ;;

    *)
        print_error "Invalid selection"
        exit 1
        ;;
esac

echo ""
echo "================================================"
echo "Next Steps"
echo "================================================"
echo ""

if [ "$MODEL_CHOICE" -eq 1 ] || [ "$MODEL_CHOICE" -eq 2 ]; then
    echo "1. Update config.yaml with model path:"
    echo "   coreml_model_path: \"models/$MODEL_NAME\""
    echo ""
    echo "2. Test the model with dry-run:"
    echo "   python main.py --dry-run"
    echo ""
    echo "3. Run the system:"
    echo "   python main.py"
    echo ""
else
    echo "1. Place your CoreML model in the models/ directory"
    echo ""
    echo "2. Update config.yaml with model path:"
    echo "   coreml_model_path: \"models/your-model.mlmodel\""
    echo ""
    echo "3. Test the model with dry-run:"
    echo "   python main.py --dry-run"
    echo ""
    echo "4. Run the system:"
    echo "   python main.py"
    echo ""
fi

print_success "Model setup complete!"
