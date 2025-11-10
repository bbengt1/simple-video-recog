"""Configuration management module.

This module provides the SystemConfig Pydantic model for validating
YAML configuration files and the load_config() function for loading
and validating configurations.
"""

from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class SystemConfig(BaseModel):
    """System configuration loaded from config/config.yaml."""

    # Camera Configuration
    camera_rtsp_url: str = Field(
        ...,
        description="RTSP stream URL",
        examples=["rtsp://admin:password@192.168.1.100:554/stream1"],
    )
    camera_id: str = Field(
        default="camera_1", description="Camera identifier for multi-camera support"
    )

    # Motion Detection
    motion_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Motion detection sensitivity (0=very sensitive, 1=less sensitive)",
    )
    frame_sample_rate: int = Field(
        default=5, ge=1, le=30, description="Frames per second to process during motion"
    )

    # Object Detection
    coreml_model_path: str = Field(
        default="models/yolov8n.mlmodel", description="Path to CoreML model file"
    )
    blacklist_objects: List[str] = Field(
        default_factory=lambda: ["bird", "cat"], description="Object labels to ignore"
    )
    min_object_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence to include detected object",
    )

    # LLM Configuration
    ollama_base_url: str = Field(
        default="http://localhost:11434", description="Ollama API endpoint"
    )
    ollama_model: str = Field(
        default="llava:7b", description="LLM model name (llava or moondream)"
    )
    llm_timeout: int = Field(
        default=10, ge=1, le=60, description="LLM request timeout in seconds"
    )

    # Event Deduplication
    deduplication_window: int = Field(
        default=30, ge=1, le=300, description="Time window in seconds for event deduplication"
    )

    # Storage
    db_path: str = Field(
        default="data/events.db", description="SQLite database file path"
    )
    max_storage_gb: float = Field(
        default=4.0, gt=0, description="Maximum storage limit in GB"
    )
    storage_check_interval: int = Field(
        default=100, ge=1, description="Check storage usage every N events"
    )
    min_retention_days: int = Field(
        default=7, ge=1, description="Minimum days to retain events"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging verbosity (DEBUG, INFO, WARNING, ERROR)",
    )
    metrics_interval: int = Field(
        default=60, ge=10, description="Metrics collection interval in seconds"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "camera_rtsp_url": "rtsp://admin:password@192.168.1.100:554/stream1",
                "camera_id": "front_door",
                "motion_threshold": 0.5,
                "frame_sample_rate": 5,
                "coreml_model_path": "models/yolov8n.mlmodel",
                "blacklist_objects": ["bird", "cat"],
                "min_object_confidence": 0.5,
                "ollama_base_url": "http://localhost:11434",
                "ollama_model": "llava:7b",
                "llm_timeout": 10,
                "db_path": "data/events.db",
                "max_storage_gb": 4.0,
                "storage_check_interval": 100,
                "min_retention_days": 7,
                "log_level": "INFO",
                "metrics_interval": 60,
            }
        }
    )


def load_config(config_path: str) -> SystemConfig:
    """Load and validate system configuration from YAML file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Validated SystemConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValidationError: If config validation fails
        yaml.YAMLError: If YAML parsing fails
    """
    # Convert to Path object
    config_file = Path(config_path)

    # Check if file exists
    if not config_file.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Please create a config file by copying config.example.yaml:\n"
            f"  cp config/config.example.yaml {config_path}"
        )

    # Read and parse YAML file
    try:
        with open(config_file, "r") as f:
            config_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(
            f"Failed to parse YAML configuration file: {config_path}\n"
            f"Error: {str(e)}\n"
            f"Please check your YAML syntax."
        )

    # Validate configuration data against Pydantic schema
    try:
        config = SystemConfig(**config_data)
        return config
    except ValidationError as e:
        # Re-raise with additional context about the config file
        raise ValueError(
            f"Configuration Validation Error in {config_path}:\n"
            f"{str(e)}"
        )
