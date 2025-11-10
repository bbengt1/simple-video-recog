"""Integration tests for Ollama service connectivity.

These tests require a running Ollama service to pass. They are designed to
gracefully skip when Ollama is not available, allowing CI/CD pipelines to
run without external dependencies.
"""

import pytest
from pydantic import HttpUrl

from core.config import SystemConfig
from core.exceptions import OllamaConnectionError, OllamaModelNotFoundError
from integrations.ollama import OllamaClient


@pytest.fixture
def integration_config():
    """Configuration for integration tests."""
    return SystemConfig(
        camera_rtsp_url="rtsp://test:pass@192.168.1.100:554/stream",
        camera_id="test_camera",
        motion_threshold=0.5,
        frame_sample_rate=5,
        coreml_model_path="models/yolov8n.mlmodel",
        blacklist_objects=["bird", "cat"],
        min_object_confidence=0.5,
        ollama_base_url=HttpUrl("http://localhost:11434"),
        ollama_model="llava:7b",
        llm_timeout=10,
        db_path="data/events.db",
        max_storage_gb=4.0,
        min_retention_days=7,
        log_level="INFO",
        metrics_interval=60,
    )


@pytest.fixture
def ollama_client(integration_config):
    """OllamaClient instance for integration testing."""
    return OllamaClient(integration_config)


class TestOllamaIntegration:
    """Integration tests for real Ollama service connectivity."""

    def test_connect_real_service(self, ollama_client, caplog):
        """Test connection to real Ollama service when available."""
        try:
            with caplog.at_level("DEBUG"):
                result = ollama_client.connect()

            # If we get here, connection was successful
            assert result is True
            assert "✓ Ollama service: Connected" in caplog.text

        except OllamaConnectionError:
            # Ollama service is not running - this is expected in CI/CD
            pytest.skip("Ollama service not available for integration testing")

    def test_verify_model_real_service(self, ollama_client, caplog):
        """Test model verification with real Ollama service when available."""
        try:
            # First ensure we can connect
            ollama_client.connect()

            # Now try to verify the model
            with caplog.at_level("INFO"):
                result = ollama_client.verify_model("llava:7b")

            # If we get here, model verification was successful
            assert result is True
            assert "✓ Vision model: llava:7b (available)" in caplog.text

        except OllamaConnectionError:
            # Ollama service is not running
            pytest.skip("Ollama service not available for integration testing")

        except OllamaModelNotFoundError:
            # Model is not downloaded - this is expected if Ollama is running but model not pulled
            pytest.skip("llava:7b model not downloaded. Run: ollama pull llava:7b")

    def test_verify_model_not_found_real_service(self, ollama_client):
        """Test model verification failure with real service when model doesn't exist."""
        try:
            # First ensure we can connect
            ollama_client.connect()

            # Try to verify a non-existent model
            with pytest.raises(OllamaModelNotFoundError) as exc_info:
                ollama_client.verify_model("nonexistent-model-12345")

            # Verify error message
            assert "Vision model 'nonexistent-model-12345' not found" in str(exc_info.value)
            assert "Run: ollama pull nonexistent-model-12345" in str(exc_info.value)

        except OllamaConnectionError:
            # Ollama service is not running
            pytest.skip("Ollama service not available for integration testing")

    def test_api_response_format(self, ollama_client):
        """Test that real API responses have expected structure."""
        try:
            # Connect and verify we get proper response format
            ollama_client.connect()

            # Verify model to ensure API responses are properly structured
            ollama_client.verify_model("llava:7b")

            # If we get here without exceptions, API format is correct

        except OllamaConnectionError:
            pytest.skip("Ollama service not available for integration testing")

        except OllamaModelNotFoundError:
            pytest.skip("llava:7b model not downloaded. Run: ollama pull llava:7b")

    @pytest.mark.parametrize("model_name", ["llava:7b", "moondream:latest"])
    def test_verify_multiple_models(self, ollama_client, model_name):
        """Test verification of different vision models."""
        try:
            # First ensure we can connect
            ollama_client.connect()

            # Try to verify the specified model
            try:
                result = ollama_client.verify_model(model_name)
                assert result is True
            except OllamaModelNotFoundError:
                # Model not available - skip this specific model test
                pytest.skip(f"{model_name} model not downloaded. Run: ollama pull {model_name}")

        except OllamaConnectionError:
            # Ollama service is not running
            pytest.skip("Ollama service not available for integration testing")