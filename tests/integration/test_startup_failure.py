"""Integration tests for system startup failure scenarios.

Tests system behavior when startup fails due to configuration or connectivity issues.
"""

import subprocess
import sys
import tempfile
import yaml
import os
from pathlib import Path


def test_startup_with_invalid_config():
    """Test system startup with invalid configuration."""
    # Create invalid config file (missing required camera_rtsp_url)
    invalid_config = {
        "camera_id": "test_camera",
        "log_level": "INFO"
        # Missing camera_rtsp_url (required field)
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(invalid_config, f)
        config_path = f.name

    try:
        # Run main.py with invalid config
        project_root = Path(__file__).parent.parent.parent
        result = subprocess.run(
            [sys.executable, 'main.py', '--config', config_path],
            capture_output=True,
            text=True,
            cwd=project_root,
            env={**os.environ, 'PYTHONPATH': str(project_root)}
        )

        # Verify non-zero exit code
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"

        # Verify error message appears in stderr
        assert "Configuration" in result.stderr or "config" in result.stderr.lower()

    finally:
        # Clean up temp file
        os.unlink(config_path)


def test_startup_with_invalid_rtsp_url():
    """Test system startup with invalid RTSP URL."""
    # Create config with invalid RTSP URL
    invalid_config = {
        "camera_rtsp_url": "rtsp://invalid:invalid@192.168.999.999:554/stream",
        "camera_id": "test_camera",
        "log_level": "INFO"
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(invalid_config, f)
        config_path = f.name

    try:
        # Run main.py with invalid RTSP URL
        project_root = Path(__file__).parent.parent.parent
        result = subprocess.run(
            [sys.executable, 'main.py', '--config', config_path],
            capture_output=True,
            text=True,
            cwd=project_root,
            env={**os.environ, 'PYTHONPATH': str(project_root)},
            timeout=10  # Don't wait too long for connection timeout
        )

        # Verify non-zero exit code (should fail during RTSP connection check)
        assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"

        # Verify error message about RTSP connection
        assert "RTSP" in result.stderr or "connection" in result.stderr.lower()

    finally:
        # Clean up temp file
        os.unlink(config_path)