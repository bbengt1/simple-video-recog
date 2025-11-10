"""Integration tests for main entry point and CLI functionality."""

import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest
import yaml


def create_test_config():
    """Create a minimal test configuration for integration testing.

    Returns:
        Path to temporary config file
    """
    config = {
        "camera_rtsp_url": "rtsp://test:test@127.0.0.1:8554/test",
        "camera_id": "test_camera",
        "motion_threshold": 0.5,
        "frame_sample_rate": 10,
        "coreml_model_path": "models/test.mlmodel",
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llava:7b",
        "db_path": "data/test.db",
        "log_level": "INFO",
        "metrics_interval": 60
    }

    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        return f.name


def test_main_with_valid_config():
    """Test main.py starts and performs health checks with valid configuration.

    Note: This test expects health check to fail due to no RTSP server running,
    but verifies the system handles this gracefully.
    """
    config_file = create_test_config()

    try:
        # Start the process in dry-run mode to see health check output
        cmd = [sys.executable, "main.py", "--config", config_file, "--dry-run"]
        process = subprocess.Popen(
            cmd,
            cwd=Path(__file__).parent.parent.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait for process to complete (health check failure causes exit)
        stdout, stderr = process.communicate(timeout=10)

        # Verify process exited with health check failure (expected)
        assert process.returncode == 2, f"Process should exit with code 2 due to health check failure in dry-run mode, got {process.returncode}"

        # Verify expected log messages in output
        combined_output = stdout + stderr
        assert "Starting video recognition system..." in combined_output
        assert "Dry-run validation failed" in combined_output
        assert "RTSP connection failed" in combined_output

    finally:
        # Clean up temp file
        os.unlink(config_file)


def test_main_with_missing_config():
    """Test main.py exits with error when default config file doesn't exist."""
    cmd = [sys.executable, "main.py"]
    process = subprocess.Popen(
        cmd,
        cwd=Path(__file__).parent.parent.parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    stdout, stderr = process.communicate(timeout=5)

    # Should exit with code 2 (config invalid)
    assert process.returncode == 2
    assert "Configuration file not found" in stderr


def test_main_with_invalid_config_path():
    """Test main.py exits with error when config file doesn't exist."""
    cmd = [sys.executable, "main.py", "--config", "/nonexistent/config.yaml"]
    process = subprocess.Popen(
        cmd,
        cwd=Path(__file__).parent.parent.parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    stdout, stderr = process.communicate(timeout=5)

    # Should exit with code 2 (config invalid)
    assert process.returncode == 2
    combined_output = stdout + stderr
    assert "Configuration file not found" in combined_output


def test_main_help_display():
    """Test main.py --help displays usage information."""
    cmd = [sys.executable, "main.py", "--help"]
    process = subprocess.Popen(
        cmd,
        cwd=Path(__file__).parent.parent.parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    stdout, stderr = process.communicate(timeout=5)

    assert process.returncode == 0
    assert "Local Video Recognition System" in stdout
    assert "--config" in stdout
    assert "Examples:" in stdout