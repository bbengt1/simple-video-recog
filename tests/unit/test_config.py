"""Unit tests for configuration validation."""


import pytest
import yaml
from pydantic import ValidationError

from core.config import SystemConfig, load_config


class TestSystemConfig:
    """Test SystemConfig Pydantic model validation."""

    def test_valid_config_loads_successfully(self, sample_config):
        """Test that valid config loads and returns SystemConfig instance."""
        # Act: Create SystemConfig from valid dictionary
        config = SystemConfig(**sample_config)

        # Assert: Verify SystemConfig instance and values
        assert isinstance(config, SystemConfig)
        assert config.camera_id == "test_camera"
        assert config.motion_threshold == 0.5
        assert config.frame_sample_rate == 5
        assert config.max_storage_gb == 4.0
        assert config.log_level == "INFO"

    def test_missing_required_field_raises_validation_error(self):
        """Test that missing required field (camera_rtsp_url) raises ValidationError."""
        # Arrange: Config missing required camera_rtsp_url
        invalid_config = {
            "camera_id": "test_camera",
            "motion_threshold": 0.5,
        }

        # Act & Assert: Expect ValidationError
        with pytest.raises(ValidationError) as exc_info:
            SystemConfig(**invalid_config)

        # Verify error mentions the missing field
        error_str = str(exc_info.value)
        assert "camera_rtsp_url" in error_str.lower()

    def test_invalid_type_raises_validation_error(self):
        """Test that invalid type (motion_threshold as string) raises ValidationError."""
        # Arrange: motion_threshold as string instead of float
        invalid_config = {
            "camera_rtsp_url": "rtsp://test",
            "motion_threshold": "high",  # Should be float
        }

        # Act & Assert: Expect ValidationError
        with pytest.raises(ValidationError) as exc_info:
            SystemConfig(**invalid_config)

        # Verify error mentions type issue
        error_str = str(exc_info.value)
        assert "motion_threshold" in error_str.lower()

    def test_out_of_range_motion_threshold_raises_validation_error(self):
        """Test that out-of-range motion_threshold (2.0) raises ValidationError."""
        # Arrange: motion_threshold exceeds valid range (0.0-1.0)
        invalid_config = {
            "camera_rtsp_url": "rtsp://test",
            "motion_threshold": 2.0,  # Should be <=1.0
        }

        # Act & Assert: Expect ValidationError
        with pytest.raises(ValidationError) as exc_info:
            SystemConfig(**invalid_config)

        # Verify error mentions range constraint
        error_str = str(exc_info.value)
        assert "motion_threshold" in error_str.lower()

    def test_out_of_range_frame_sample_rate_raises_validation_error(self):
        """Test that out-of-range frame_sample_rate (100) raises ValidationError."""
        # Arrange: frame_sample_rate exceeds valid range (1-30)
        invalid_config = {
            "camera_rtsp_url": "rtsp://test",
            "frame_sample_rate": 100,  # Should be <=30
        }

        # Act & Assert: Expect ValidationError
        with pytest.raises(ValidationError) as exc_info:
            SystemConfig(**invalid_config)

        # Verify error mentions range constraint
        error_str = str(exc_info.value)
        assert "frame_sample_rate" in error_str.lower()

    def test_default_values_applied(self):
        """Test that default values are applied for optional fields."""
        # Arrange: Minimal config with only required field
        minimal_config = {"camera_rtsp_url": "rtsp://test"}

        # Act: Create config
        config = SystemConfig(**minimal_config)

        # Assert: Verify defaults applied
        assert config.camera_id == "camera_1"
        assert config.motion_threshold == 0.5
        assert config.frame_sample_rate == 5
        assert config.blacklist_objects == ["bird", "cat"]
        assert config.min_object_confidence == 0.5
        assert config.ollama_model == "llava:7b"
        assert config.max_storage_gb == 4.0
        assert config.log_level == "INFO"


class TestLoadConfig:
    """Test load_config() function."""

    def test_load_valid_config_file(self, temp_config_file):
        """Test that valid config file loads successfully."""
        # Act: Load configuration
        config = load_config(str(temp_config_file))

        # Assert: Verify SystemConfig instance and values
        assert isinstance(config, SystemConfig)
        assert config.camera_id == "test_camera"
        assert config.motion_threshold == 0.5

    def test_missing_config_file_raises_file_not_found_error(self, tmp_path):
        """Test that missing config file raises FileNotFoundError with clear message."""
        # Arrange: Non-existent config file path
        missing_file = tmp_path / "nonexistent.yaml"

        # Act & Assert: Expect FileNotFoundError
        with pytest.raises(FileNotFoundError) as exc_info:
            load_config(str(missing_file))

        # Verify error message is helpful
        error_str = str(exc_info.value)
        assert "not found" in error_str.lower()
        assert "config.example.yaml" in error_str

    def test_invalid_yaml_syntax_raises_yaml_error(self, tmp_path):
        """Test that invalid YAML syntax raises yaml.YAMLError with helpful message."""
        # Arrange: Create file with invalid YAML syntax
        invalid_yaml_file = tmp_path / "invalid.yaml"
        with open(invalid_yaml_file, "w") as f:
            f.write("camera_rtsp_url: rtsp://test\n")
            f.write("invalid: yaml: syntax: here\n")  # Invalid syntax

        # Act & Assert: Expect yaml.YAMLError
        with pytest.raises(yaml.YAMLError) as exc_info:
            load_config(str(invalid_yaml_file))

        # Verify error message mentions parsing failure
        error_str = str(exc_info.value)
        assert "parse" in error_str.lower() or "yaml" in error_str.lower()

    def test_validation_error_includes_field_details(self, tmp_path):
        """Test that validation error messages include field name and helpful details."""
        # Arrange: Config file with validation error (out of range value)
        invalid_config_file = tmp_path / "invalid.yaml"
        with open(invalid_config_file, "w") as f:
            yaml.dump(
                {
                    "camera_rtsp_url": "rtsp://test",
                    "motion_threshold": 5.0,  # Out of range
                },
                f,
            )

        # Act & Assert: Expect ValidationError
        with pytest.raises(ValidationError) as exc_info:
            load_config(str(invalid_config_file))

        # Verify error message is informative
        error_str = str(exc_info.value)
        assert "motion_threshold" in error_str.lower()
