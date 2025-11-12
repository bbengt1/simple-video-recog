"""Unit tests for dry-run functionality."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from core.dry_run import DryRunValidator
from core.config import SystemConfig


class TestDryRunValidator:
    """Test DryRunValidator functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock SystemConfig for testing."""
        config = MagicMock(spec=SystemConfig)
        config.camera_rtsp_url = "rtsp://test:1234@192.168.1.100:554/stream"
        config.camera_id = "test_camera"
        config.motion_threshold = 0.5
        config.frame_sample_rate = 5
        config.coreml_model_path = "models/yolov8n.mlmodel"
        config.ollama_base_url = "http://localhost:11434"
        config.ollama_model = "llava:7b"
        config.llm_timeout = 10
        config.blacklist_objects = ["cat", "tree"]
        config.deduplication_window = 30
        config.min_object_confidence = 0.5
        config.db_path = "data/events.db"
        config.max_storage_gb = 4.0
        config.min_retention_days = 7
        config.log_level = "INFO"
        config.metrics_interval = 60
        return config

    @pytest.fixture
    def validator(self, mock_config):
        """Create a DryRunValidator instance."""
        return DryRunValidator(mock_config)

    def test_init(self, validator, mock_config):
        """Test DryRunValidator initialization."""
        assert validator.config == mock_config
        assert "timestamp" in validator.results
        assert "version" in validator.results
        assert "validations" in validator.results
        assert "tests" in validator.results
        assert "summary" in validator.results

    @patch('core.dry_run.HealthChecker')
    def test_validate_configuration(self, mock_health_checker, validator):
        """Test configuration validation."""
        # Mock health checker
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.all_passed = True
        mock_result.failed_checks = []
        mock_result.warnings = []
        mock_instance.check_all.return_value = mock_result
        mock_health_checker.return_value = mock_instance

        with patch.object(validator, '_run_health_checks', return_value=True), \
             patch.object(validator, '_validate_models', return_value=True), \
             patch.object(validator, '_run_connection_tests', return_value=True), \
             patch.object(validator, '_analyze_storage', return_value=True), \
             patch.object(validator, '_save_results'):

            success = validator.run_full_validation()

            assert success
            assert validator.results["validations"]["configuration"]["status"] == "passed"

    @patch('core.dry_run.HealthChecker')
    def test_run_health_checks_success(self, mock_health_checker, validator):
        """Test successful health checks."""
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.all_passed = True
        mock_result.failed_checks = []  # No critical failures
        mock_result.warnings = ["warning1"]
        mock_instance.check_all.return_value = mock_result
        mock_health_checker.return_value = mock_instance

        success = validator._run_health_checks()

        assert success
        assert validator.results["validations"]["health_checks"]["status"] == "passed"
        assert validator.results["validations"]["health_checks"]["passed"] == 0  # Can't calculate without total
        assert validator.results["validations"]["health_checks"]["failed"] == 0
        assert validator.results["validations"]["health_checks"]["warnings"] == 1

    @patch('core.dry_run.HealthChecker')
    def test_run_health_checks_failure(self, mock_health_checker, validator):
        """Test failed health checks."""
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.all_passed = False
        mock_result.failed_checks = ["check1", "check2"]
        mock_result.warnings = []
        mock_instance.check_all.return_value = mock_result
        mock_health_checker.return_value = mock_instance

        success = validator._run_health_checks()

        assert not success
        assert validator.results["validations"]["health_checks"]["status"] == "failed"

    @patch('core.dry_run.CoreMLDetector')
    def test_validate_models_success(self, mock_coreml_detector, validator):
        """Test successful model validation."""
        mock_detector = MagicMock()
        mock_detector.model_metadata = {
            "input_shape": (1, 3, 416, 416),
            "ane_compatible": True
        }
        mock_coreml_detector.return_value = mock_detector

        with patch('core.dry_run.OllamaClient') as mock_ollama_client:
            mock_ollama = MagicMock()
            mock_ollama.connect.return_value = True
            mock_ollama.verify_model.return_value = True
            mock_ollama_client.return_value = mock_ollama

            success = validator._validate_models()

            assert success
            assert validator.results["tests"]["coreml"]["status"] == "passed"
            assert validator.results["tests"]["ollama"]["status"] == "passed"

    @patch('core.dry_run.CoreMLDetector')
    def test_validate_models_coreml_failure(self, mock_coreml_detector, validator):
        """Test CoreML validation failure (acceptable in dry-run)."""
        mock_detector = MagicMock()
        mock_detector.load_model.side_effect = Exception("Model load failed")
        mock_coreml_detector.return_value = mock_detector

        success = validator._validate_models()

        assert success  # CoreML failure is acceptable in dry-run
        assert validator.results["tests"]["coreml"]["status"] == "warning"

    @patch('core.dry_run.OllamaClient')
    def test_validate_models_ollama_failure(self, mock_ollama_client, validator):
        """Test Ollama validation failure."""
        with patch('core.dry_run.CoreMLDetector') as mock_coreml_detector:
            mock_detector = MagicMock()
            mock_detector.model_metadata = {"ane_compatible": True}
            mock_coreml_detector.return_value = mock_detector

            mock_ollama = MagicMock()
            mock_ollama.connect.side_effect = Exception("Connection failed")
            mock_ollama_client.return_value = mock_ollama

            success = validator._validate_models()

            assert not success
            assert validator.results["tests"]["ollama"]["status"] == "failed"

    @patch('core.dry_run.RTSPCameraClient')
    @patch('core.dry_run.MotionDetector')
    def test_run_connection_tests_success(self, mock_motion_detector, mock_rtsp_client, validator):
        """Test successful connection tests."""
        # Mock RTSP client
        mock_rtsp = MagicMock()
        mock_frame = MagicMock()
        mock_frame.shape = (1080, 1920, 3)
        mock_rtsp.get_latest_frame.return_value = mock_frame  # Correct method name
        mock_rtsp_client.return_value = mock_rtsp

        # Mock motion detector
        mock_motion = MagicMock()
        mock_motion.detect_motion.return_value = (True, 0.8, None)
        mock_motion_detector.return_value = mock_motion

        success = validator._run_connection_tests()

        assert success
        assert validator.results["tests"]["rtsp"]["status"] == "passed"
        assert validator.results["tests"]["motion"]["status"] == "passed"

    @patch('core.dry_run.RTSPCameraClient')
    def test_run_connection_tests_rtsp_failure(self, mock_rtsp_client, validator):
        """Test RTSP connection failure."""
        mock_rtsp = MagicMock()
        mock_rtsp.get_frame.return_value = None  # No frames captured
        mock_rtsp_client.return_value = mock_rtsp

        success = validator._run_connection_tests()

        assert not success
        assert validator.results["tests"]["rtsp"]["status"] == "failed"

    @patch('core.dry_run.StorageMonitor')
    def test_analyze_storage_success(self, mock_storage_monitor, validator):
        """Test successful storage analysis."""
        mock_monitor = MagicMock()
        mock_stats = MagicMock()
        mock_stats.total_bytes = 1073741824  # 1GB
        mock_stats.limit_bytes = 4294967296  # 4GB
        mock_stats.percentage_used = 0.25
        mock_stats.is_over_limit = False
        mock_monitor.check_usage.return_value = mock_stats
        mock_storage_monitor.return_value = mock_monitor

        success = validator._analyze_storage()

        assert success
        assert validator.results["tests"]["storage"]["status"] == "passed"
        assert validator.results["tests"]["storage"]["total_usage_bytes"] == 1073741824

    @patch('core.dry_run.StorageMonitor')
    def test_analyze_storage_failure(self, mock_storage_monitor, validator):
        """Test storage analysis failure."""
        mock_monitor = MagicMock()
        mock_monitor.check_usage.side_effect = Exception("Storage check failed")
        mock_storage_monitor.return_value = mock_monitor

        success = validator._analyze_storage()

        assert not success
        assert validator.results["tests"]["storage"]["status"] == "failed"

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_results(self, mock_json_dump, mock_file, validator):
        """Test saving results to file."""
        validator.results = {
            "validations": {"config": {"status": "passed"}},
            "tests": {"coreml": {"status": "passed"}},
            "summary": {}
        }

        validator._save_results()

        # Verify json.dump was called
        mock_json_dump.assert_called_once()

    def test_print_summary_success(self, validator, capsys):
        """Test printing success summary."""
        validator.results = {
            "summary": {
                "validations_passed": 2,
                "validations_total": 2,
                "tests_passed": 3,
                "tests_total": 3,
                "overall_success": True
            }
        }

        validator.print_summary()

        captured = capsys.readouterr()
        assert "✓ All validations passed" in captured.out
        assert "System ready for production" in captured.out

    def test_print_summary_failure(self, validator, capsys):
        """Test printing failure summary."""
        validator.results = {
            "summary": {
                "validations_passed": 1,
                "validations_total": 2,
                "tests_passed": 2,
                "tests_total": 3,
                "overall_success": False
            }
        }

        validator.print_summary()

        captured = capsys.readouterr()
        assert "✗ Validation failed" in captured.out
        assert "1 validations failed, 1 tests failed" in captured.out