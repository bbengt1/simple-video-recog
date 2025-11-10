"""Unit tests for OllamaClient module."""

from unittest.mock import patch

import numpy as np
import pytest

from core.config import SystemConfig
from core.exceptions import OllamaConnectionError, OllamaModelNotFoundError, OllamaTimeoutError
from core.models import BoundingBox, DetectedObject, DetectionResult
from integrations.ollama import OllamaClient


@pytest.fixture
def mock_ollama_client(sample_config):
    """Create OllamaClient with mocked ollama library."""
    config = SystemConfig(**sample_config)
    with patch('integrations.ollama.ollama') as mock_ollama:
        client = OllamaClient(config)
        yield client, mock_ollama


@pytest.fixture
def mock_ollama_response():
    """Mock successful Ollama API response."""
    return {
        'models': [
            {'name': 'llava:7b', 'size': '4.7GB'},
            {'name': 'moondream:latest', 'size': '1.8GB'}
        ]
    }


@pytest.fixture
def sample_frame():
    """Create sample numpy frame for testing."""
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)


@pytest.fixture
def sample_detections():
    """Create sample DetectionResult with detected objects."""
    bbox = BoundingBox(x=100, y=50, width=200, height=150)
    obj = DetectedObject(label="person", confidence=0.95, bbox=bbox)
    return DetectionResult(objects=[obj], inference_time=0.05, frame_shape=(480, 640, 3))


class TestOllamaClient:
    """Test cases for OllamaClient functionality."""

    def test_connect_success(self, mock_ollama_client, mock_ollama_response, caplog):
        """Test successful connection to Ollama service."""
        client, mock_ollama = mock_ollama_client

        # Mock successful ollama.list() response
        mock_ollama.list.return_value = mock_ollama_response

        # Call connect method
        with caplog.at_level("DEBUG"):
            result = client.connect()

        # Verify return value
        assert result is True

        # Verify ollama.list() was called
        mock_ollama.list.assert_called_once()

        # Verify success log message
        assert "✓ Ollama service: Connected" in caplog.text
        assert "http://localhost:11434" in caplog.text

        # Verify debug log with available models
        assert "Available models: llava:7b, moondream:latest" in caplog.text

    def test_connect_service_unreachable(self, mock_ollama_client, caplog):
        """Test connection failure when Ollama service is unreachable."""
        client, mock_ollama = mock_ollama_client

        # Mock connection failure
        mock_ollama.list.side_effect = Exception("Connection refused")

        # Verify OllamaConnectionError is raised
        with pytest.raises(OllamaConnectionError) as exc_info:
            client.connect()

        # Verify error message
        assert "Ollama service not reachable at http://localhost:11434" in str(exc_info.value)
        assert "Is Ollama running?" in str(exc_info.value)

        # Verify error log message
        assert "Ollama service not reachable" in caplog.text

    def test_verify_model_success(self, mock_ollama_client, caplog):
        """Test successful model verification."""
        client, mock_ollama = mock_ollama_client

        # Mock successful ollama.show() response
        mock_ollama.show.return_value = {'modelfile': 'FROM llava:7b'}

        # Call verify_model method
        with caplog.at_level("INFO"):
            result = client.verify_model("llava:7b")

        # Verify return value
        assert result is True

        # Verify ollama.show() was called with correct model name
        mock_ollama.show.assert_called_once_with("llava:7b")

        # Verify success log message
        assert "✓ Vision model: llava:7b (available)" in caplog.text

    def test_verify_model_not_found(self, mock_ollama_client, caplog):
        """Test model verification failure when model is not found."""
        client, mock_ollama = mock_ollama_client

        # Mock model not found error
        mock_ollama.show.side_effect = Exception("model not found")

        # Verify OllamaModelNotFoundError is raised
        with pytest.raises(OllamaModelNotFoundError) as exc_info:
            client.verify_model("nonexistent-model")

        # Verify error message
        assert "Vision model 'nonexistent-model' not found" in str(exc_info.value)
        assert "Run: ollama pull nonexistent-model" in str(exc_info.value)

        # Verify error log message
        assert "Vision model 'nonexistent-model' not found" in caplog.text

    def test_verify_model_different_model_name(self, mock_ollama_client, caplog):
        """Test model verification with different model name."""
        client, mock_ollama = mock_ollama_client

        # Mock successful response for moondream model
        mock_ollama.show.return_value = {'modelfile': 'FROM moondream:latest'}

        # Call verify_model with different model
        with caplog.at_level("INFO"):
            result = client.verify_model("moondream:latest")

        # Verify return value
        assert result is True

        # Verify ollama.show() was called with correct model name
        mock_ollama.show.assert_called_once_with("moondream:latest")

        # Verify success log message
        assert "✓ Vision model: moondream:latest (available)" in caplog.text

    def test_connect_empty_models_list(self, mock_ollama_client, caplog):
        """Test connection when no models are available."""
        client, mock_ollama = mock_ollama_client

        # Mock response with empty models list
        mock_ollama.list.return_value = {'models': []}

        # Call connect method
        with caplog.at_level("DEBUG"):
            result = client.connect()

        # Verify return value
        assert result is True

        # Verify debug log shows "None" for empty models list
        assert "Available models: None" in caplog.text

    def test_generate_description_success(self, mock_ollama_client, sample_frame, sample_detections, caplog):
        """Test successful generation of semantic description."""
        client, mock_ollama = mock_ollama_client

        # Mock successful ollama.generate() response
        mock_response = {'response': 'A person is standing in front of a building.'}
        mock_ollama.generate.return_value = mock_response

        # Call generate_description method
        with caplog.at_level("INFO"):
            result = client.generate_description(sample_frame, sample_detections)

        # Verify return value
        assert result == 'A person is standing in front of a building.'

        # Verify ollama.generate() was called with correct parameters
        mock_ollama.generate.assert_called_once()
        call_args = mock_ollama.generate.call_args
        assert call_args[1]['model'] == client.config.ollama_model
        assert 'images' in call_args[1]
        assert len(call_args[1]['images']) == 1
        assert call_args[1]['images'][0].startswith('data:image/jpeg;base64,')

        # Verify success log message includes timing
        assert "✓ LLM description generated" in caplog.text
        assert "in" in caplog.text and "s" in caplog.text  # Should include timing like "in 0.12s"

    def test_generate_description_timeout(self, mock_ollama_client, sample_frame, sample_detections):
        """Test timeout handling during LLM generation."""
        client, mock_ollama = mock_ollama_client

        # Mock timeout response error
        from ollama._types import ResponseError
        mock_ollama.generate.side_effect = ResponseError("Request timeout")

        # Call generate_description method and expect timeout error
        with pytest.raises(OllamaTimeoutError) as exc_info:
            client.generate_description(sample_frame, sample_detections)

        # Verify error message
        assert "LLM inference timeout" in str(exc_info.value)

    def test_generate_description_connection_error(self, mock_ollama_client, sample_frame, sample_detections):
        """Test connection error handling during LLM generation."""
        client, mock_ollama = mock_ollama_client

        # Mock connection response error
        from ollama._types import ResponseError
        mock_ollama.generate.side_effect = ResponseError("Connection refused")

        # Call generate_description method and expect connection error
        with pytest.raises(OllamaConnectionError) as exc_info:
            client.generate_description(sample_frame, sample_detections)

        # Verify error message
        assert "LLM generation failed" in str(exc_info.value)

    def test_construct_vision_prompt_with_objects(self, mock_ollama_client):
        """Test vision prompt construction with detected objects."""
        client, _ = mock_ollama_client

        # Test with object labels
        object_labels = ["person", "car", "dog"]
        prompt = client._construct_vision_prompt(object_labels)

        expected = "Describe what is happening in this image. Focus on: person, car, dog. Provide a concise, natural description of the scene and any actions."
        assert prompt == expected

    def test_construct_vision_prompt_no_objects(self, mock_ollama_client):
        """Test vision prompt construction without detected objects."""
        client, _ = mock_ollama_client

        # Test with empty object labels
        prompt = client._construct_vision_prompt([])

        expected = "Describe what is happening in this image. Provide a concise, natural description of the scene and any actions."
        assert prompt == expected
