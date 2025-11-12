"""Ollama LLM service integration module.

This module provides the OllamaClient class for connecting to and verifying
local Ollama LLM services for semantic event description generation.
"""

import base64
import time

import cv2
import numpy as np
import ollama
from ollama._types import ResponseError

from core.config import SystemConfig
from core.exceptions import OllamaConnectionError, OllamaModelNotFoundError, OllamaTimeoutError
from core.logging_config import get_logger
from core.models import DetectionResult


class OllamaClient:
    """Client for interacting with local Ollama LLM service.

    This class provides methods to connect to and verify Ollama service availability,
    as well as check if specific vision models are downloaded and ready for use.

    Attributes:
        config: System configuration containing Ollama settings.
        logger: Logger instance for structured logging.
    """

    def __init__(self, config: SystemConfig):
        """Initialize OllamaClient with system configuration.

        Args:
            config: SystemConfig instance containing Ollama base URL, model name,
                   and timeout settings.
        """
        self.config = config
        self.logger = get_logger(__name__)

    def connect(self) -> bool:
        """Connect to Ollama service and verify it's running.

        Calls the /api/tags endpoint to verify the Ollama service is accessible
        and lists all available models for troubleshooting.

        Returns:
            True if connection successful.

        Raises:
            OllamaConnectionError: If Ollama service is not reachable.
        """
        try:
            # Call /api/tags to verify service connectivity
            response = ollama.list()

            # Log successful connection
            self.logger.info(f"✓ Ollama service: Connected ({self.config.ollama_base_url})")

            # Log available models at DEBUG level for troubleshooting
            # Handle both dict (test mocks) and ListResponse (real API)
            if hasattr(response, 'models'):
                # Real API response
                models = [model.model for model in response.models if model.model]
            else:
                # Test mock response (dict)
                models = [model.get('name', model.get('model', '')) for model in response.get('models', [])]
                models = [m for m in models if m]  # Filter out empty strings
            self.logger.debug(f"Available models: {', '.join(models) if models else 'None'}")

            return True

        except ResponseError as e:
            error_msg = f"Ollama service not reachable at {self.config.ollama_base_url}. Is Ollama running?"
            self.logger.error(f"{error_msg} (ResponseError: {str(e)})")
            raise OllamaConnectionError(error_msg) from e
        except Exception as e:
            error_msg = f"Ollama service not reachable at {self.config.ollama_base_url}. Is Ollama running?"
            self.logger.error(f"{error_msg} (Unexpected error: {type(e).__name__}: {str(e)})")
            raise OllamaConnectionError(error_msg) from e

    def verify_model(self, model_name: str) -> bool:
        """Verify that a specific vision model is available.

        Calls the /api/show endpoint to check if the specified model is downloaded
        and available for use.

        Args:
            model_name: Name of the model to verify (e.g., "llava:7b").

        Returns:
            True if model is available.

        Raises:
            OllamaModelNotFoundError: If the specified model is not found.
        """
        try:
            # Call /api/show to check model availability
            ollama.show(model_name)

            # Log successful verification
            self.logger.info(f"✓ Vision model: {model_name} (available)")

            return True

        except ResponseError as e:
            if "not found" in str(e).lower() or "404" in str(e):
                error_msg = f"Vision model '{model_name}' not found. Run: ollama pull {model_name}"
                self.logger.error(error_msg)
                raise OllamaModelNotFoundError(error_msg) from e
            else:
                # Other HTTP errors (500, etc.)
                error_msg = f"Failed to verify vision model '{model_name}': {str(e)}"
                self.logger.error(error_msg)
                raise OllamaModelNotFoundError(error_msg) from e
        except Exception as e:
            # Handle generic exceptions (including test mocks)
            if "model not found" in str(e).lower() or "not found" in str(e).lower():
                error_msg = f"Vision model '{model_name}' not found. Run: ollama pull {model_name}"
                self.logger.error(error_msg)
                raise OllamaModelNotFoundError(error_msg) from e
            else:
                error_msg = f"Failed to verify vision model '{model_name}': {type(e).__name__}: {str(e)}"
                self.logger.error(error_msg)
                raise OllamaModelNotFoundError(error_msg) from e

    def generate_description(self, frame: np.ndarray, detections: DetectionResult) -> str:
        """Generate semantic description of detected objects in frame.

        Encodes the frame as base64 JPEG, constructs a vision prompt with detected
        object labels, and calls Ollama's vision model to generate a natural language
        description of the scene.

        Args:
            frame: OpenCV frame (numpy array in BGR format) containing detected objects.
            detections: DetectionResult containing detected objects and metadata.

        Returns:
            Natural language description of the scene and detected objects.

        Raises:
            OllamaTimeoutError: If LLM inference exceeds configured timeout.
            OllamaConnectionError: If Ollama service is unreachable during generation.
        """
        # Encode frame to base64 JPEG
        base64_image = self._encode_frame_to_base64(frame)

        # Construct vision prompt with detected object labels
        object_labels = [obj.label for obj in detections.objects]
        prompt = self._construct_vision_prompt(object_labels)

        try:
            # Start timing LLM inference
            start_time = time.perf_counter()

            # Log request details for debugging
            self.logger.debug(f"Sending to Ollama: model={self.config.ollama_model}, prompt='{prompt[:50]}...', image_size={len(base64_image)} chars")

            # Call Ollama vision API
            response = ollama.generate(
                model=self.config.ollama_model,
                prompt=prompt,
                images=[base64_image],
                stream=False
            )

            # Calculate inference time
            inference_time = time.perf_counter() - start_time

            # Extract generated text from response
            description = response.get('response', '').strip()

            # Log successful generation with timing
            self.logger.info(f"✓ LLM description generated ({len(description)} chars) in {inference_time:.2f}s")

            # Log warning if inference exceeds 5 seconds
            if inference_time > 5.0:
                self.logger.warning(f"LLM inference exceeded 5s threshold: {inference_time:.2f}s")

            return description

        except ResponseError as e:
            if "timeout" in str(e).lower() or "deadline" in str(e).lower():
                error_msg = f"LLM inference timeout after {self.config.llm_timeout}s"
                self.logger.warning(error_msg)
                raise OllamaTimeoutError(error_msg) from e
            else:
                error_msg = f"LLM generation failed: {str(e)}"
                self.logger.error(error_msg)
                raise OllamaConnectionError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error during LLM generation: {type(e).__name__}: {str(e)}"
            self.logger.error(error_msg)
            raise OllamaConnectionError(error_msg) from e

    def _encode_frame_to_base64(self, frame: np.ndarray) -> str:
        """Encode OpenCV frame to base64 JPEG string.

        Args:
            frame: OpenCV frame (numpy array in BGR format).

        Returns:
            Base64-encoded JPEG data URL.
        """
        # Validate frame
        if frame is None or frame.size == 0:
            raise ValueError("Frame is None or empty")

        if len(frame.shape) != 3 or frame.shape[2] != 3:
            raise ValueError(f"Invalid frame shape: {frame.shape}, expected (H, W, 3)")

        # Convert BGR to RGB for JPEG encoding
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Encode as JPEG
        success, buffer = cv2.imencode('.jpg', rgb_frame)
        if not success:
            raise ValueError("Failed to encode frame as JPEG")

        # Convert to base64
        base64_bytes = base64.b64encode(buffer.tobytes())
        base64_string = base64_bytes.decode('utf-8')

        # Validate base64 string
        try:
            # Test that we can decode it back
            test_decode = base64.b64decode(base64_string)
            if len(test_decode) == 0:
                raise ValueError("Base64 decoding resulted in empty data")
        except Exception as e:
            raise ValueError(f"Generated invalid base64: {e}")

        self.logger.debug(f"Encoded frame {frame.shape} to base64 JPEG ({len(base64_string)} chars)")

        # Return base64 string (Ollama expects just the base64 data, not data URL format)
        return base64_string

    def _construct_vision_prompt(self, object_labels: list[str]) -> str:
        """Construct vision prompt with detected object context.

        Args:
            object_labels: List of detected object labels.

        Returns:
            Formatted vision prompt for LLM.
        """
        if object_labels:
            labels_text = ", ".join(object_labels)
            return f"Describe what is happening in this image. Focus on: {labels_text}. Provide a concise, natural description of the scene and any actions."
        else:
            return "Describe what is happening in this image. Provide a concise, natural description of the scene and any actions."
