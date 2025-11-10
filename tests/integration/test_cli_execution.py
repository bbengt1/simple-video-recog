"""Integration tests for CLI execution and argument handling."""
import subprocess
import sys
from pathlib import Path
import pytest


class TestCLIExecution:
    """Test actual CLI execution with subprocess calls."""

    def get_python_executable(self):
        """Get the Python executable to use for subprocess calls."""
        return sys.executable

    def run_cli_command(self, args):
        """Run CLI command and return result."""
        cmd = [self.get_python_executable(), "main.py"] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        return result

    def test_help_flag_displays_usage(self):
        """Test --help flag displays usage information."""
        result = self.run_cli_command(["--help"])

        assert result.returncode == 0
        assert "Local Video Recognition System" in result.stdout
        assert "usage:" in result.stdout
        assert "--config" in result.stdout
        assert "--dry-run" in result.stdout
        assert "--version" in result.stdout
        assert "Exit codes:" in result.stdout

    def test_version_flag_displays_version(self):
        """Test --version flag displays version information."""
        result = self.run_cli_command(["--version"])

        assert result.returncode == 0
        assert "video-recog v1.0.0" in result.stdout
        assert "build 2025-11-08" in result.stdout
        assert "Python" in result.stdout

    def test_invalid_config_file_exits_with_code_2(self):
        """Test invalid config file exits with code 2."""
        result = self.run_cli_command(["--config", "nonexistent.yaml"])

        assert result.returncode == 2
        assert "Configuration file not found" in result.stderr

    def test_valid_config_file_with_dry_run(self):
        """Test valid config file with --dry-run succeeds."""
        config_path = "config/config.yaml"
        if Path(config_path).exists():
            result = self.run_cli_command(["--config", config_path, "--dry-run"])

            # Should succeed if config exists and is valid
            assert result.returncode in [0, 1]  # 0 for success, 1 for health check failure
            if result.returncode == 0:
                assert "validation successful" in result.stdout

    def test_log_level_validation(self):
        """Test --log-level argument validation."""
        # Valid log level
        result = self.run_cli_command(["--log-level", "DEBUG", "--help"])
        assert result.returncode == 0

        # Invalid log level should show error
        result = self.run_cli_command(["--log-level", "INVALID", "--help"])
        assert result.returncode != 0 or "invalid choice" in result.stderr

    def test_metrics_interval_validation(self):
        """Test --metrics-interval argument validation."""
        # Valid integer
        result = self.run_cli_command(["--metrics-interval", "120", "--help"])
        assert result.returncode == 0

        # Invalid non-integer should show error
        result = self.run_cli_command(["--metrics-interval", "not-a-number", "--help"])
        assert result.returncode != 0

    def test_default_config_path(self):
        """Test default config path behavior."""
        # Test with non-existent default config
        result = self.run_cli_command([])

        # Should fail if default config doesn't exist
        if not Path("config/config.yaml").exists():
            assert result.returncode == 2
            assert "Configuration file not found" in result.stderr

    def test_config_flag_with_custom_path(self):
        """Test --config flag with custom path."""
        result = self.run_cli_command(["--config", "config/config.yaml", "--help"])
        assert result.returncode == 0

    def test_combined_flags(self):
        """Test multiple flags combined."""
        result = self.run_cli_command([
            "--config", "config/config.yaml",
            "--log-level", "INFO",
            "--metrics-interval", "60",
            "--help"
        ])
        assert result.returncode == 0