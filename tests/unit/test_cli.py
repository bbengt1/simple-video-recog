"""Unit tests for CLI argument parsing and validation."""
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.version import format_version_output, get_version_info


class TestVersionInfo:
    """Test version information functionality."""

    def test_get_version_info(self):
        """Test version info collection."""
        info = get_version_info()

        assert info.version == "1.0.0"
        assert info.build_date == "2025-11-08"
        assert info.python_version is not None
        assert info.platform is not None

    def test_format_version_output(self):
        """Test version output formatting."""
        output = format_version_output()

        assert "Video Recognition System v1.0.0" in output
        assert "Build: 2025-11-08" in output
        assert "Python:" in output
        assert "Platform:" in output
        assert "Dependencies:" in output


class TestCLIArgumentParsing:
    """Test CLI argument parsing functionality."""

    def test_version_flag_returns_early(self):
        """Test that --version flag displays version and returns."""
        from main import main

        with patch('main.parse_arguments') as mock_parse_args, \
             patch('builtins.print') as mock_print:
            # Mock arguments with version flag
            mock_args = MagicMock()
            mock_args.version = True
            mock_parse_args.return_value = mock_args

            main()

            mock_print.assert_called_once()
            printed_output = mock_print.call_args[0][0]
            assert "Video Recognition System v1.0.0" in printed_output

    @patch('main.parse_arguments')
    @patch('main.load_config')
    @patch('sys.exit')
    @patch('builtins.print')
    def test_invalid_config_file_exits_with_code_2(self, mock_print, mock_exit,
                                                   mock_load_config, mock_parse_args):
        """Test that invalid config file path exits with code 2."""
        from main import main

        # Mock arguments
        mock_args = MagicMock()
        mock_args.version = False
        mock_args.config_file = "nonexistent.yaml"
        mock_parse_args.return_value = mock_args

        # Mock load_config to raise FileNotFoundError
        mock_load_config.side_effect = FileNotFoundError("Configuration file not found: nonexistent.yaml")

        main()

        mock_print.assert_called_once()
        call_args = mock_print.call_args
        assert call_args[1]['file'] == sys.stderr  # Should print to stderr
        error_msg = call_args[0][0]
        assert "Configuration file not found" in error_msg
        mock_exit.assert_called_once_with(2)

    @patch('main.parse_arguments')
    @patch('main.load_config')
    @patch('main.setup_logging')
    @patch('main.HealthChecker')
    @patch('main.RTSPCameraClient')
    @patch('main.DryRunValidator')
    @patch('main.MotionDetector')
    @patch('main.FrameSampler')
    @patch('main.CoreMLDetector')
    @patch('main.EventDeduplicator')
    @patch('main.OllamaClient')
    @patch('main.ImageAnnotator')
    @patch('main.ProcessingPipeline')
    @patch('sys.exit')
    def test_dry_run_mode_exits_after_validation(self, mock_exit, mock_pipeline, mock_image_annotator, mock_ollama,
                                                mock_deduplicator, mock_coreml, mock_frame_sampler,
                                                mock_motion, mock_rtsp, mock_dry_run_validator, mock_health, mock_setup_logging,
                                                mock_load_config, mock_parse_args):
        """Test that --dry-run validates and exits without starting pipeline."""
        import main

        # Mock arguments
        mock_args = MagicMock()
        mock_args.version = False
        mock_args.dry_run = True
        mock_args.config_file = "config/config.yaml"
        mock_args.log_level = None
        mock_args.metrics_interval = None
        mock_parse_args.return_value = mock_args

        # Mock config with real values to avoid MagicMock formatting issues
        from core.config import SystemConfig
        mock_config = SystemConfig(
            camera_id="test_camera",
            camera_rtsp_url="rtsp://test:test@127.0.0.1:554/test",
            coreml_model_path="/tmp/test.mlmodel",
            ollama_base_url="http://localhost:11434",
            ollama_model="test",
            motion_threshold=0.5,
            frame_sample_rate=5,
            blacklist_objects=[],
            db_path="/tmp/test.db",
            max_storage_gb=10.0,
            min_retention_days=7,
            log_level="INFO",
            metrics_interval=60
        )
        mock_load_config.return_value = mock_config

        # Mock successful health check
        mock_health_instance = MagicMock()
        mock_health_instance.run_checks.return_value = True
        mock_health.return_value = mock_health_instance

        # Mock successful dry run validation
        mock_dry_run_instance = MagicMock()
        mock_dry_run_instance.run_full_validation.return_value = True
        mock_dry_run_instance.print_summary.return_value = None  # Mock print_summary to do nothing
        mock_dry_run_validator.return_value = mock_dry_run_instance

        with patch('builtins.print') as mock_print:
            main.main()

            # Check that the success message was printed
            print_calls = [call.args[0] for call in mock_print.call_args_list]
            assert any("✓ All validations passed. System ready for production." in call for call in print_calls)
            mock_exit.assert_called_once_with(0)

    @patch('main.parse_arguments')
    @patch('main.Path')
    @patch('main.load_config')
    @patch('main.setup_logging')
    def test_config_override_log_level(self, mock_setup_logging, mock_load_config,
                                      mock_path_class, mock_parse_args):
        """Test that --log-level overrides config."""
        from main import main

        # Mock arguments
        mock_args = MagicMock()
        mock_args.version = False
        mock_args.dry_run = False
        mock_args.config_file = "config/config.yaml"
        mock_args.log_level = "DEBUG"
        mock_args.metrics_interval = None
        mock_parse_args.return_value = mock_args

        # Mock config file exists
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path_class.return_value = mock_path

        # Mock config
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        # Mock components and health check to avoid full execution
        with patch('main.HealthChecker') as mock_health, \
             patch('main.RTSPCameraClient'), \
             patch('main.MotionDetector'), \
             patch('main.FrameSampler'), \
             patch('main.CoreMLDetector'), \
             patch('main.EventDeduplicator'), \
             patch('main.OllamaClient'), \
             patch('main.ImageAnnotator'), \
             patch('main.ProcessingPipeline') as mock_pipeline, \
             patch('main.get_logger'), \
             patch('sys.exit'):
            mock_health_instance = MagicMock()
            mock_health_instance.run_checks.return_value = True
            mock_health.return_value = mock_health_instance

            mock_pipeline_instance = MagicMock()
            mock_pipeline.return_value = mock_pipeline_instance

            main()

            # Verify config was overridden
            assert mock_config.log_level == "DEBUG"

    @patch('main.parse_arguments')
    @patch('main.Path')
    @patch('main.load_config')
    @patch('main.setup_logging')
    def test_config_override_metrics_interval(self, mock_setup_logging, mock_load_config,
                                             mock_path_class, mock_parse_args):
        """Test that --metrics-interval overrides config."""
        from main import main

        # Mock arguments
        mock_args = MagicMock()
        mock_args.version = False
        mock_args.dry_run = False
        mock_args.config_file = "config/config.yaml"
        mock_args.log_level = None
        mock_args.metrics_interval = 120
        mock_parse_args.return_value = mock_args

        # Mock config file exists
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path_class.return_value = mock_path

        # Mock config
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        # Mock components and health check to avoid full execution
        with patch('main.HealthChecker') as mock_health, \
             patch('main.RTSPCameraClient'), \
             patch('main.MotionDetector'), \
             patch('main.FrameSampler'), \
             patch('main.CoreMLDetector'), \
             patch('main.EventDeduplicator'), \
             patch('main.OllamaClient'), \
             patch('main.ImageAnnotator'), \
             patch('main.ProcessingPipeline') as mock_pipeline, \
             patch('main.get_logger'), \
             patch('sys.exit'):
            mock_health_instance = MagicMock()
            mock_health_instance.run_checks.return_value = True
            mock_health.return_value = mock_health_instance

            mock_pipeline_instance = MagicMock()
            mock_pipeline.return_value = mock_pipeline_instance

            main()

            # Verify config was overridden
            assert mock_config.metrics_interval == 120