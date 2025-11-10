"""Integration tests for version display functionality."""

import subprocess
import sys
from pathlib import Path

import pytest


class TestVersionDisplay:
    """Test --version flag integration."""

    def test_version_flag_execution(self):
        """Test that --version flag executes without error and produces output."""
        # Get the Python executable path
        python_exe = sys.executable

        # Run main.py --version
        result = subprocess.run(
            [python_exe, "main.py", "--version"],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should exit successfully
        assert result.returncode == 0

        # Should have output
        assert result.stdout.strip()
        # Allow stderr for coremltools warnings in test environment

        # Check basic format
        output = result.stdout
        assert "Video Recognition System v" in output
        assert "Build:" in output
        assert "Python:" in output
        assert "Platform:" in output
        assert "Dependencies:" in output
        assert "OpenCV:" in output
        assert "CoreML Tools:" in output
        assert "Ollama:" in output

    def test_version_flag_with_invalid_args(self):
        """Test --version flag works even with invalid other args."""
        python_exe = sys.executable

        # Run with --version and invalid config
        result = subprocess.run(
            [python_exe, "main.py", "--version", "--config", "nonexistent.yaml"],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should still work since --version exits early
        assert result.returncode == 0
        assert "Video Recognition System v" in result.stdout

    def test_version_output_format(self):
        """Test that version output matches expected format structure."""
        python_exe = sys.executable

        result = subprocess.run(
            [python_exe, "main.py", "--version"],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True,
            timeout=10
        )

        output = result.stdout

        # Check line-by-line structure
        lines = output.strip().split('\n')
        assert len(lines) >= 7  # Header + build + python + platform + dependencies header + 3 deps

        # First line should be "Video Recognition System vX.Y.Z"
        assert lines[0].startswith("Video Recognition System v")
        assert "1.0.0" in lines[0]

        # Second line should be "Build: YYYY-MM-DD (commit ...)"
        assert lines[1].startswith("Build: 2025-11-08 (commit ")

        # Third line should be "Python: 3.X.Y"
        assert lines[2].startswith("Python: 3.")
        assert "." in lines[2]

        # Fourth line should be "Platform: ..."
        assert lines[3].startswith("Platform: ")

        # Fifth line should be "Dependencies:"
        assert lines[4] == "Dependencies:"

        # Following lines should be dependency versions
        dep_lines = [line for line in lines[5:] if line.strip()]
        assert len(dep_lines) >= 3
        assert any("OpenCV:" in line for line in dep_lines)
        assert any("CoreML Tools:" in line for line in dep_lines)
        assert any("Ollama:" in line for line in dep_lines)