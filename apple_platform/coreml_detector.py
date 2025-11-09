"""CoreML object detection module for Apple Neural Engine.

This module provides the CoreMLDetector class for loading and managing
CoreML object detection models optimized for Apple Silicon hardware.
"""

import logging
from typing import Optional

import coremltools
import numpy as np

from core.config import SystemConfig
from core.exceptions import CoreMLLoadError


class CoreMLDetector:
    """CoreML object detector for Apple Neural Engine.

    Handles loading, validation, and management of CoreML object detection models
    with Apple Neural Engine compatibility checking and performance optimization.
    """

    def __init__(self, config: SystemConfig) -> None:
        """Initialize CoreML detector.

        Args:
            config: System configuration containing model path and settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.model: Optional[coremltools.models.MLModel] = None
        self.model_metadata: Optional[dict] = None
        self.is_loaded = False

    def load_model(self, model_path: str) -> None:
        """Load CoreML model from file path.

        Args:
            model_path: Path to .mlmodel file

        Raises:
            CoreMLLoadError: If model loading fails
        """
        try:
            # Load the CoreML model
            self.model = coremltools.models.MLModel(model_path)
            self.is_loaded = True

            # Check Apple Neural Engine compatibility
            compute_unit = getattr(self.model, 'compute_unit', None)
            if compute_unit == 'CPU_AND_GPU':
                self.logger.warning(
                    "Model will run on CPU/GPU (slower), consider using ANE-optimized model"
                )
                ane_compatible = False
            else:
                ane_compatible = True

            # Extract model metadata
            model_name = getattr(self.model, 'model_name', 'Unknown')
            input_description = self.model.input_description
            output_description = self.model.output_description

            # Get input shape if available
            input_shape = None
            if input_description:
                input_names = list(input_description)
                if input_names:
                    first_input = input_description[input_names[0]]
                    if hasattr(first_input, 'type') and hasattr(first_input.type, 'multiArrayType'):
                        shape = first_input.type.multiArrayType.shape
                        if shape:
                            input_shape = tuple(shape)

            # Store metadata
            self.model_metadata = {
                'ane_compatible': ane_compatible,
                'compute_unit': compute_unit,
                'model_name': model_name,
                'input_shape': input_shape,
                'input_description': input_description,
                'output_description': output_description,
            }

            # Log model details
            ane_status = "(ANE-compatible)" if ane_compatible else "(CPU/GPU)"
            self.logger.info(f"✓ CoreML model loaded: {model_name} {ane_status}")

            if input_shape:
                self.logger.info(f"Model input shape: {input_shape}")
            if input_shape:
                input_names = list(input_description)
                self.logger.debug(f"Model inputs: {input_names}")
            if output_description:
                output_names = list(output_description)
                self.logger.debug(f"Model outputs: {output_names}")

            # Model warm-up: Run inference on dummy frame
            import time
            start_time = time.time()

            # Create dummy frame based on input shape
            if input_shape and len(input_shape) >= 3:
                # Assume shape is (height, width, channels) or (channels, height, width)
                if len(input_shape) == 3:
                    # Try (height, width, channels) first
                    dummy_frame = np.random.rand(*input_shape).astype(np.float32)
                else:
                    # Fallback to common shape
                    dummy_frame = np.random.rand(416, 416, 3).astype(np.float32)
            else:
                # Default dummy frame for common object detection models
                dummy_frame = np.random.rand(416, 416, 3).astype(np.float32)

            # Run warm-up inference
            try:
                _ = self.model.predict({'input': dummy_frame})
                warmup_time = time.time() - start_time
                self.logger.info(f"Model warm-up completed in {warmup_time:.3f}s")
                self.model_metadata['warmup_time'] = warmup_time
            except Exception as e:
                self.logger.warning(f"Model warm-up failed: {str(e)}")
                warmup_time = time.time() - start_time
                self.model_metadata['warmup_time'] = warmup_time

        except FileNotFoundError:
            error_msg = f"CoreML model file not found: {model_path}"
            self.logger.error(error_msg)
            raise CoreMLLoadError(error_msg)

        except Exception as e:
            error_msg = f"Failed to load CoreML model from {model_path}: {str(e)}"
            self.logger.error(error_msg)
            raise CoreMLLoadError(error_msg)
