"""Unit tests for example configuration file validation.

This test ensures that config.example.yaml is valid and can be loaded
successfully by the configuration system.
"""

import pytest
from pathlib import Path

from core.config import SystemConfig, load_config


def test_example_config_exists():
    """Test that example configuration file exists."""
    config_path = Path("config/config.example.yaml")
    assert config_path.exists(), "config.example.yaml not found"
    assert config_path.is_file(), "config.example.yaml is not a file"


def test_example_config_is_valid_yaml():
    """Test that example configuration is valid YAML syntax."""
    import yaml

    config_path = Path("config/config.example.yaml")

    with open(config_path, 'r') as f:
        try:
            yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"config.example.yaml has invalid YAML syntax: {e}")


def test_example_config_loads_successfully():
    """Test that example configuration can be loaded by SystemConfig."""
    config_path = "config/config.example.yaml"

    try:
        config = load_config(config_path)
        assert isinstance(config, SystemConfig), "Loaded config is not a SystemConfig instance"
    except Exception as e:
        pytest.fail(f"Failed to load config.example.yaml: {e}")


def test_example_config_has_required_fields():
    """Test that example configuration contains all required fields."""
    config = load_config("config/config.example.yaml")

    # Required camera fields
    assert hasattr(config, 'camera_rtsp_url'), "Missing camera_rtsp_url"
    assert config.camera_rtsp_url is not None, "camera_rtsp_url is None"
    assert hasattr(config, 'camera_id'), "Missing camera_id"
    assert config.camera_id is not None, "camera_id is None"

    # Required model fields
    assert hasattr(config, 'coreml_model_path'), "Missing coreml_model_path"
    assert config.coreml_model_path is not None, "coreml_model_path is None"
    assert hasattr(config, 'ollama_model'), "Missing ollama_model"
    assert config.ollama_model is not None, "ollama_model is None"

    # Required processing fields
    assert hasattr(config, 'motion_threshold'), "Missing motion_threshold"
    assert hasattr(config, 'frame_sample_rate'), "Missing frame_sample_rate"

    # Required storage fields
    assert hasattr(config, 'db_path'), "Missing db_path"
    assert hasattr(config, 'max_storage_gb'), "Missing max_storage_gb"


def test_example_config_field_types():
    """Test that example configuration fields have correct types."""
    config = load_config("config/config.example.yaml")

    # String fields
    assert isinstance(config.camera_rtsp_url, str), "camera_rtsp_url must be string"
    assert isinstance(config.camera_id, str), "camera_id must be string"
    assert isinstance(config.coreml_model_path, str), "coreml_model_path must be string"
    assert isinstance(config.ollama_model, str), "ollama_model must be string"
    assert isinstance(config.ollama_base_url, str), "ollama_base_url must be string"
    assert isinstance(config.db_path, str), "db_path must be string"
    assert isinstance(config.log_level, str), "log_level must be string"

    # Numeric fields
    assert isinstance(config.motion_threshold, (int, float)), "motion_threshold must be numeric"
    assert isinstance(config.frame_sample_rate, int), "frame_sample_rate must be int"
    assert isinstance(config.min_object_confidence, float), "min_object_confidence must be float"
    assert isinstance(config.llm_timeout, int), "llm_timeout must be int"
    assert isinstance(config.deduplication_window, int), "deduplication_window must be int"
    assert isinstance(config.max_storage_gb, (int, float)), "max_storage_gb must be numeric"
    assert isinstance(config.min_retention_days, int), "min_retention_days must be int"
    assert isinstance(config.metrics_interval, int), "metrics_interval must be int"

    # List fields
    assert isinstance(config.blacklist_objects, list), "blacklist_objects must be list"


def test_example_config_field_ranges():
    """Test that example configuration fields have valid ranges."""
    config = load_config("config/config.example.yaml")

    # Motion threshold (0.0-1.0 normalized or 0-255 raw)
    assert 0 <= config.motion_threshold <= 255, "motion_threshold out of range"

    # Frame sample rate (1-30)
    assert 1 <= config.frame_sample_rate <= 30, "frame_sample_rate out of range"

    # Confidence threshold (0.0-1.0)
    assert 0.0 <= config.min_object_confidence <= 1.0, "min_object_confidence out of range"

    # LLM timeout (1-60 seconds)
    assert 1 <= config.llm_timeout <= 60, "llm_timeout out of range"

    # Deduplication window (1-300 seconds)
    assert 1 <= config.deduplication_window <= 300, "deduplication_window out of range"

    # Storage limit (positive)
    assert config.max_storage_gb > 0, "max_storage_gb must be positive"

    # Retention days (positive)
    assert config.min_retention_days > 0, "min_retention_days must be positive"

    # Metrics interval (minimum 10 seconds)
    assert config.metrics_interval >= 10, "metrics_interval must be >= 10"


def test_example_config_log_level_valid():
    """Test that example configuration has valid log level."""
    config = load_config("config/config.example.yaml")

    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
    assert config.log_level in valid_levels, f"log_level must be one of {valid_levels}"


def test_example_config_ollama_base_url_format():
    """Test that Ollama base URL is properly formatted."""
    config = load_config("config/config.example.yaml")

    assert config.ollama_base_url.startswith("http://") or \
           config.ollama_base_url.startswith("https://"), \
           "ollama_base_url must start with http:// or https://"


def test_example_config_blacklist_objects_valid():
    """Test that blacklist_objects contains valid object names."""
    config = load_config("config/config.example.yaml")

    # Ensure all items are strings
    for obj in config.blacklist_objects:
        assert isinstance(obj, str), f"blacklist_objects item '{obj}' must be string"
        assert len(obj) > 0, "blacklist_objects cannot contain empty strings"


def test_example_config_paths_format():
    """Test that file paths in config are properly formatted."""
    config = load_config("config/config.example.yaml")

    # Model path should end with .mlmodel
    assert config.coreml_model_path.endswith(".mlmodel"), \
           "coreml_model_path must end with .mlmodel"

    # Database path should end with .db
    assert config.db_path.endswith(".db"), \
           "db_path must end with .db"


def test_example_config_camera_rtsp_url_format():
    """Test that RTSP URL is properly formatted."""
    config = load_config("config/config.example.yaml")

    assert config.camera_rtsp_url.startswith("rtsp://"), \
           "camera_rtsp_url must start with rtsp://"


def test_example_config_pydantic_validation():
    """Test that Pydantic validation passes for example config."""
    config = load_config("config/config.example.yaml")

    # If we got here, Pydantic validation passed
    # Try to access model_dump to verify it's a valid Pydantic model
    try:
        config_dict = config.model_dump()
        assert isinstance(config_dict, dict), "model_dump() should return dict"
        assert len(config_dict) > 0, "model_dump() should not be empty"
    except Exception as e:
        pytest.fail(f"Pydantic model validation failed: {e}")


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
