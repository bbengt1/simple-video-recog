"""Integration tests for health check functionality.

Tests end-to-end health check execution, timeout behavior, and console output formatting.
"""

import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest
import yaml


def create_test_config(**overrides):
    """Create a test configuration with optional overrides.

    Args:
        **overrides: Configuration values to override defaults

    Returns:
        Path to temporary config file
    """
    config = {
        "camera_rtsp_url": "rtsp://test:test@127.0.0.1:8554/test",
        "camera_id": "test_camera",
        "motion_threshold": 0.5,
        "frame_sample_rate": 10,
        "coreml_model_path": "models/yolov8n.mlmodel",
        "ollama_base_url": "http://localhost:11434",
        "ollama_model": "llava:7b",
        "db_path": "data/test.db",
        "log_level": "INFO",
        "metrics_interval": 60,
        "max_storage_gb": 4.0
    }

    # Apply overrides
    config.update(overrides)

    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        return f.name


class TestHealthCheckIntegration:
    """Integration tests for health check functionality."""

    def test_dry_run_with_all_checks_passing(self):
        """Test dry-run mode when all health checks pass (where possible)."""
        # Create config that should pass basic checks
        config_file = create_test_config()

        try:
            project_root = Path(__file__).parent.parent.parent
            cmd = [sys.executable, "main.py", "--dry-run", "--config", config_file]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=30
            )

            # Should exit with code 2 (validation failure) due to missing dependencies
            # but we verify the dry-run format is correct
            assert result.returncode == 2

            # Verify dry-run output format
            output = result.stdout + result.stderr
            assert "[STARTUP] Video Recognition System v" in output
            assert "[DRY-RUN]" in output
            assert "validation failed" in output.lower()

            # Verify expected check prefixes appear
            expected_prefixes = [
                "[CONFIG]", "[PLATFORM]", "[PYTHON]", "[DEPENDENCIES]",
                "[MODELS]", "[OLLAMA]", "[CAMERA]", "[PERMISSIONS]", "[STORAGE]"
            ]

            for prefix in expected_prefixes:
                assert prefix in output, f"Missing expected output prefix: {prefix}"

        finally:
            Path(config_file).unlink(missing_ok=True)

    def test_dry_run_console_output_format(self):
        """Test that dry-run console output matches acceptance criteria format."""
        config_file = create_test_config()

        try:
            project_root = Path(__file__).parent.parent.parent
            cmd = [sys.executable, "main.py", "--dry-run", "--config", config_file]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=30
            )

            output = result.stdout + result.stderr

            # Verify version header
            assert "[STARTUP] Video Recognition System v" in output

            # Verify check results have proper format (✓ or ✗ or ⚠ prefix)
            lines = output.split('\n')
            check_lines = [line for line in lines if any(prefix in line for prefix in [
                "[CONFIG]", "[PLATFORM]", "[PYTHON]", "[DEPENDENCIES]",
                "[MODELS]", "[OLLAMA]", "[CAMERA]", "[PERMISSIONS]", "[STORAGE]"
            ])]

            for line in check_lines:
                # Each check line should start with [PREFIX] followed by status symbol
                assert line.startswith('['), f"Line doesn't start with bracket: {line}"
                assert ']' in line, f"Line missing closing bracket: {line}"
                status_part = line.split(']')[1].strip()
                assert status_part.startswith(('✓', '✗', '⚠')), f"Invalid status symbol in: {line}"

        finally:
            Path(config_file).unlink(missing_ok=True)

    def test_dry_run_timeout_behavior(self):
        """Test that dry-run handles timeouts properly without hanging."""
        # Create config with unreachable RTSP URL that should timeout
        config_file = create_test_config(
            camera_rtsp_url="rtsp://192.168.255.255:554/unreachable"  # Unreachable IP
        )

        try:
            project_root = Path(__file__).parent.parent.parent
            cmd = [sys.executable, "main.py", "--dry-run", "--config", config_file]

            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=20  # Should complete within 20 seconds despite RTSP timeout
            )
            end_time = time.time()

            # Verify it completed within reasonable time (RTSP timeout is 10s)
            duration = end_time - start_time
            assert duration < 18, f"Dry-run took too long: {duration:.1f}s"

            # Should exit with validation failure
            assert result.returncode == 2

            # Verify RTSP timeout message appears
            output = result.stdout + result.stderr
            assert "RTSP connection timeout" in output or "RTSP read timeout" in output

        finally:
            Path(config_file).unlink(missing_ok=True)

    def test_dry_run_with_missing_dependencies(self):
        """Test dry-run mode properly reports missing dependencies."""
        config_file = create_test_config()

        try:
            project_root = Path(__file__).parent.parent.parent
            cmd = [sys.executable, "main.py", "--dry-run", "--config", config_file]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=30
            )

            output = result.stdout + result.stderr

            # Should detect missing CoreML model
            assert "CoreML model not found" in output or "models/yolov8n.mlmodel" in output

            # Should detect storage issues (depending on system)
            assert "[STORAGE]" in output

            # Should have final status message
            assert "[DRY-RUN]" in output
            assert "validation failed" in output.lower()

        finally:
            Path(config_file).unlink(missing_ok=True)

    def test_dry_run_with_valid_ollama_service(self):
        """Test dry-run mode with valid Ollama service (if running)."""
        config_file = create_test_config()

        try:
            project_root = Path(__file__).parent.parent.parent
            cmd = [sys.executable, "main.py", "--dry-run", "--config", config_file]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=30
            )

            output = result.stdout + result.stderr

            # Ollama check should appear (either pass or fail depending on service status)
            assert "[OLLAMA]" in output

            # If Ollama is running, should show success message
            if "✓ Ollama service running" in output:
                assert "model 'llava:7b' ready" in output
            else:
                # If not running, should show appropriate failure message
                assert "Ollama service" in output

        finally:
            Path(config_file).unlink(missing_ok=True)

    def test_normal_mode_runs_silently(self):
        """Test that normal mode (non-dry-run) doesn't display health check output."""
        config_file = create_test_config()

        try:
            project_root = Path(__file__).parent.parent.parent
            cmd = [sys.executable, "main.py", "--config", config_file]

            # Run with timeout since it will try to start processing
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=10  # Should fail quickly due to health check failure
            )

            output = result.stdout + result.stderr

            # Normal mode should NOT show formatted health check output
            assert "[STARTUP] Video Recognition System v" not in output
            assert "[CONFIG]" not in output
            assert "[PLATFORM]" not in output

            # But should still show startup messages
            assert "Starting video recognition system" in output

            # Should exit with health check failure
            assert result.returncode == 1

        finally:
            Path(config_file).unlink(missing_ok=True)

    def test_dry_run_exit_codes(self):
        """Test that dry-run mode uses correct exit codes."""
        # Test with config that will definitely fail
        config_file = create_test_config(
            camera_rtsp_url="rtsp://192.168.255.255:554/unreachable",
            coreml_model_path="/nonexistent/model.mlmodel"
        )

        try:
            project_root = Path(__file__).parent.parent.parent
            cmd = [sys.executable, "main.py", "--dry-run", "--config", config_file]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=20
            )

            # Should exit with code 2 (validation failure)
            assert result.returncode == 2, f"Expected exit code 2, got {result.returncode}"

            output = result.stdout + result.stderr
            assert "[DRY-RUN] ✗ Validation failed" in output

        finally:
            Path(config_file).unlink(missing_ok=True)