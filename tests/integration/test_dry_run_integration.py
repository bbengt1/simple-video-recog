"""Integration tests for dry-run functionality."""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.dry_run import DryRunValidator
from core.config import SystemConfig


class TestDryRunIntegration:
    """Integration tests for DryRunValidator."""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file."""
        config_data = {
            "camera_rtsp_url": "rtsp://test:1234@192.168.1.100:554/stream",
            "camera_id": "test_camera",
            "motion_threshold": 0.5,
            "frame_sample_rate": 5,
            "coreml_model_path": "models/yolov8n.mlmodel",
            "ollama_base_url": "http://localhost:11434",
            "ollama_model": "llava:7b",
            "llm_timeout": 10,
            "blacklist_objects": ["cat", "tree"],
            "deduplication_window": 30,
            "min_object_confidence": 0.5,
            "db_path": "data/events.db",
            "max_storage_gb": 4.0,
            "min_retention_days": 7,
            "log_level": "INFO",
            "metrics_interval": 60
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(config_data, f)
            return f.name

    @pytest.fixture
    def config(self, temp_config_file):
        """Load config from temp file."""
        from core.config import load_config
        return load_config(temp_config_file)

    @pytest.fixture
    def validator(self, config):
        """Create DryRunValidator with real config."""
        return DryRunValidator(config)

    @patch('core.dry_run.HealthChecker')
    @patch('core.dry_run.CoreMLDetector')
    @patch('core.dry_run.OllamaClient')
    @patch('core.dry_run.RTSPCameraClient')
    @patch('core.dry_run.MotionDetector')
    @patch('core.dry_run.StorageMonitor')
    def test_full_validation_success(self, mock_storage_monitor, mock_motion_detector,
                                   mock_rtsp_client, mock_ollama_client, mock_coreml_detector,
                                   mock_health_checker, validator):
        """Test full validation with all components succeeding."""
        # Mock health checker
        mock_health_instance = MagicMock()
        mock_health_result = MagicMock()
        mock_health_result.all_passed = True
        mock_health_result.failed_checks = []
        mock_health_result.warnings = []
        mock_health_instance.check_all.return_value = mock_health_result
        mock_health_checker.return_value = mock_health_instance

        # Mock CoreML detector
        mock_coreml = MagicMock()
        mock_coreml.model_metadata = {
            "input_shape": (1, 3, 416, 416),
            "ane_compatible": True
        }
        mock_coreml_detector.return_value = mock_coreml

        # Mock Ollama client
        mock_ollama = MagicMock()
        mock_ollama.connect.return_value = True
        mock_ollama.verify_model.return_value = True
        mock_ollama_client.return_value = mock_ollama

        # Mock RTSP client
        mock_rtsp = MagicMock()
        mock_frame = MagicMock()
        mock_frame.shape = (1080, 1920, 3)
        mock_rtsp.get_latest_frame.return_value = mock_frame
        mock_rtsp.connect.return_value = True
        mock_rtsp.start_capture.return_value = None
        mock_rtsp.stop_capture.return_value = None
        mock_rtsp.disconnect.return_value = None
        mock_rtsp_client.return_value = mock_rtsp

        # Mock motion detector
        mock_motion = MagicMock()
        mock_motion.detect_motion.return_value = (True, 0.8, None)
        mock_motion_detector.return_value = mock_motion

        # Mock storage monitor
        mock_storage = MagicMock()
        mock_stats = MagicMock()
        mock_stats.total_bytes = 1073741824  # 1GB
        mock_stats.limit_bytes = 4294967296  # 4GB
        mock_stats.percentage_used = 0.25
        mock_stats.is_over_limit = False
        mock_storage.check_usage.return_value = mock_stats
        mock_storage_monitor.return_value = mock_storage

        # Run validation
        success = validator.run_full_validation()

        assert success
        # Summary is calculated in _save_results, so check after it runs
        summary = validator.results["summary"]
        assert summary["overall_success"] is True
        assert summary["validations_passed"] == 2  # configuration + health_checks
        assert summary["tests_passed"] == 5  # coreml, ollama, rtsp, motion, storage

    @patch('core.dry_run.HealthChecker')
    @patch('core.dry_run.CoreMLDetector')
    def test_validation_with_health_check_failure(self, mock_coreml_detector, mock_health_checker, validator):
        """Test validation when health checks fail."""
        # Mock health checker failure
        mock_health_instance = MagicMock()
        mock_health_result = MagicMock()
        mock_health_result.all_passed = False
        mock_health_result.failed_checks = ["database", "logs"]
        mock_health_result.warnings = []
        mock_health_instance.check_all.return_value = mock_health_result
        mock_health_checker.return_value = mock_health_instance

        # Mock CoreML success
        mock_coreml = MagicMock()
        mock_coreml.model_metadata = {"ane_compatible": True}
        mock_coreml_detector.return_value = mock_coreml

        with patch.object(validator, '_validate_models', return_value=True), \
             patch.object(validator, '_run_connection_tests', return_value=True), \
             patch.object(validator, '_analyze_storage', return_value=True):

            success = validator.run_full_validation()

            assert not success
            # Summary is calculated in _save_results which runs on success only
            # For failure cases, we need to check the individual results
            assert validator.results["validations"]["health_checks"]["status"] == "failed"

    @patch('core.dry_run.CoreMLDetector')
    def test_validation_with_coreml_failure(self, mock_coreml_detector, validator):
        """Test validation when CoreML fails (treated as warning in dry-run mode)."""
        # Mock CoreML failure
        mock_coreml = MagicMock()
        mock_coreml.load_model.side_effect = Exception("Model not found")
        mock_coreml_detector.return_value = mock_coreml

        with patch.object(validator, '_run_health_checks', return_value=True), \
             patch.object(validator, '_run_connection_tests', return_value=True), \
             patch.object(validator, '_analyze_storage', return_value=True):

            success = validator.run_full_validation()

            # In dry-run mode, CoreML failures are treated as warnings, not failures
            assert success
            assert validator.results["tests"]["coreml"]["status"] == "warning"

    @patch('core.dry_run.RTSPCameraClient')
    def test_validation_with_rtsp_failure(self, mock_rtsp_client, validator):
        """Test validation when RTSP connection fails."""
        # Mock RTSP failure
        mock_rtsp = MagicMock()
        mock_rtsp.get_frame.return_value = None  # No frames
        mock_rtsp_client.return_value = mock_rtsp

        with patch.object(validator, '_run_health_checks', return_value=True), \
             patch.object(validator, '_validate_models', return_value=True), \
             patch.object(validator, '_analyze_storage', return_value=True):

            success = validator.run_full_validation()

            assert not success
            assert validator.results["tests"]["rtsp"]["status"] == "failed"

    def test_results_file_creation(self, validator, tmp_path):
        """Test that results file is created correctly."""
        results_file = tmp_path / "dry_run_results.json"

        # Mock the results
        validator.results = {
            "timestamp": "2024-01-01T12:00:00Z",
            "version": "1.0.0",
            "validations": {"config": {"status": "passed"}},
            "tests": {"coreml": {"status": "passed"}},
            "summary": {"overall_success": True}
        }

        # Mock the config.db_path to point to tmp_path
        with patch.object(validator.config, 'db_path', str(tmp_path / "test.db")):
            validator._save_results()

            # Verify file was created
            assert results_file.exists()

            # Verify content
            with open(results_file, 'r') as f:
                saved_results = json.load(f)

            assert saved_results == validator.results

    def test_configuration_display(self, validator, capsys):
        """Test that configuration is displayed correctly."""
        validator._validate_configuration()

        captured = capsys.readouterr()
        assert "Camera Configuration:" in captured.out
        assert "RTSP URL: rtsp://test:1234@192.168.1.100:554/stream" in captured.out
        assert "Camera ID: test_camera" in captured.out
        assert "Motion threshold: 0.5" in captured.out

    @patch('core.dry_run.HealthChecker')
    def test_health_check_integration(self, mock_health_checker, validator):
        """Test health check integration."""
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.all_passed = True
        mock_result.failed_checks = []
        mock_result.warnings = ["Low disk space"]
        mock_instance.check_all.return_value = mock_result
        mock_health_checker.return_value = mock_instance

        success = validator._run_health_checks()

        assert success
        assert validator.results["validations"]["health_checks"]["status"] == "passed"

    @patch('core.dry_run.StorageMonitor')
    def test_storage_analysis_display(self, mock_storage_monitor, validator, capsys):
        """Test storage analysis display."""
        mock_monitor = MagicMock()
        mock_stats = MagicMock()
        mock_stats.total_bytes = 2147483648  # 2GB
        mock_stats.limit_bytes = 4294967296  # 4GB
        mock_stats.percentage_used = 0.5
        mock_stats.is_over_limit = False
        mock_monitor.check_usage.return_value = mock_stats
        mock_storage_monitor.return_value = mock_monitor

        validator._analyze_storage()

        captured = capsys.readouterr()
        assert "[TEST] Analyzing storage usage..." in captured.out
        assert "2.0GB / 4.0GB (50.0%)" in captured.out
        assert "Status: OK" in captured.out