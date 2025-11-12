"""Unit tests for health check module."""

import numpy as np
import pytest
from unittest.mock import Mock, patch

import cv2

from core.health_check import HealthChecker, HealthCheckResult
from core.config import SystemConfig


class TestHealthCheckResult:
    """Test HealthCheckResult Pydantic model."""

    def test_valid_result(self):
        """Test creating valid HealthCheckResult."""
        result = HealthCheckResult(
            all_passed=True,
            failed_checks=[],
            warnings=[]
        )
        assert result.all_passed is True
        assert result.failed_checks == []
        assert result.warnings == []

    def test_failed_result(self):
        """Test creating failed HealthCheckResult."""
        result = HealthCheckResult(
            all_passed=False,
            failed_checks=["config: invalid", "platform: unsupported"],
            warnings=["storage: low space"]
        )
        assert result.all_passed is False
        assert len(result.failed_checks) == 2
        assert len(result.warnings) == 1


class TestHealthChecker:
    """Test HealthChecker class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock SystemConfig."""
        config = Mock(spec=SystemConfig)
        return config

    @pytest.fixture
    def health_checker(self, mock_config):
        """Create HealthChecker instance."""
        # Set required config attributes for StorageMonitor
        mock_config.max_storage_gb = 50.0
        mock_config.storage_check_interval = 100
        return HealthChecker(mock_config, timeout=5)

    def test_init(self, mock_config):
        """Test HealthChecker initialization."""
        checker = HealthChecker(mock_config, timeout=10)
        assert checker.config == mock_config
        assert checker.timeout == 10

    def test_init_default_timeout(self, mock_config):
        """Test HealthChecker initialization with default timeout."""
        checker = HealthChecker(mock_config)
        assert checker.timeout == 10

    @patch('core.health_check.get_logger')
    def test_logger_initialization(self, mock_get_logger, mock_config):
        """Test logger is initialized."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        checker = HealthChecker(mock_config)
        assert checker.logger == mock_logger
        mock_get_logger.assert_called_once_with('core.health_check')

    def test_check_all_success(self, health_checker):
        """Test check_all returns success when all checks pass."""
        with patch.object(health_checker, '_check_config', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_platform', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_python_version', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_dependencies', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_coreml_model', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_ollama_service', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_rtsp_connectivity', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_file_permissions', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_storage_availability', return_value=(True, "ok")):

            result = health_checker.check_all()

            assert isinstance(result, HealthCheckResult)
            assert result.all_passed is True
            assert result.failed_checks == []
            assert result.warnings == []

    def test_check_all_with_failures(self, health_checker):
        """Test check_all returns failure when some checks fail."""
        with patch.object(health_checker, '_check_config', return_value=(False, "config failed")), \
             patch.object(health_checker, '_check_platform', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_python_version', return_value=(False, "python failed")), \
             patch.object(health_checker, '_check_dependencies', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_coreml_model', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_ollama_service', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_rtsp_connectivity', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_file_permissions', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_storage_availability', return_value=(True, "ok")):

            result = health_checker.check_all()

            assert result.all_passed is False
            assert len(result.failed_checks) == 2
            assert "config: config failed" in result.failed_checks
            assert "python_version: python failed" in result.failed_checks

    def test_check_all_with_exception(self, health_checker):
        """Test check_all handles exceptions in checks."""
        with patch.object(health_checker, '_check_config', side_effect=Exception("test error")), \
             patch.object(health_checker, '_check_platform', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_python_version', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_dependencies', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_coreml_model', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_ollama_service', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_rtsp_connectivity', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_file_permissions', return_value=(True, "ok")), \
             patch.object(health_checker, '_check_storage_availability', return_value=(True, "ok")):

            result = health_checker.check_all()

            assert result.all_passed is False
            assert len(result.failed_checks) == 1
            assert "Unexpected error in config: test error" in result.failed_checks[0]

    @patch('core.health_check.get_logger')
    def test_logging_success(self, mock_get_logger, health_checker):
        """Test successful checks are logged at INFO level."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Re-initialize to get the logger
        health_checker.logger = mock_logger

        with patch.object(health_checker, '_check_config', return_value=(True, "config ok")), \
             patch.object(health_checker, '_check_platform', return_value=(True, "platform ok")):

            # Mock all other checks to avoid full execution
            for check_name in ['_check_python_version', '_check_dependencies', '_check_coreml_model',
                             '_check_ollama_service', '_check_rtsp_connectivity', '_check_file_permissions',
                             '_check_storage_availability']:
                patch.object(health_checker, check_name, return_value=(True, "ok"))

            health_checker.check_all()

            mock_logger.info.assert_any_call("✓ config: config ok")
            mock_logger.info.assert_any_call("✓ platform: platform ok")

    @patch('core.health_check.get_logger')
    def test_logging_failure(self, mock_get_logger, health_checker):
        """Test failed checks are logged at ERROR level."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        health_checker.logger = mock_logger

        with patch.object(health_checker, '_check_config', return_value=(False, "config failed")), \
             patch.object(health_checker, '_check_platform', return_value=(True, "platform ok")):

            for check_name in ['_check_python_version', '_check_dependencies', '_check_coreml_model',
                             '_check_ollama_service', '_check_rtsp_connectivity', '_check_file_permissions',
                             '_check_storage_availability']:
                patch.object(health_checker, check_name, return_value=(True, "ok"))

            health_checker.check_all()

            mock_logger.error.assert_any_call("✗ config: config failed")

    def test_check_config_success(self, health_checker):
        """Test config check passes with valid config."""
        # Mock config with required attributes
        health_checker.config.camera_rtsp_url = "rtsp://test"
        health_checker.config.camera_id = "test_camera"
        health_checker.config.coreml_model_path = "models/test.mlmodel"
        health_checker.config.ollama_model = "llava:latest"
        health_checker.config.motion_threshold = 25
        health_checker.config.max_storage_gb = 4

        success, message = health_checker._check_config()
        assert success is True
        assert "✓ Configuration loaded: test_camera" in message

    def test_check_config_missing_camera_url(self, health_checker):
        """Test config check fails with missing camera_rtsp_url."""
        health_checker.config.camera_rtsp_url = ""
        health_checker.config.camera_id = "test"
        health_checker.config.coreml_model_path = "models/test.mlmodel"
        health_checker.config.ollama_model = "llava:latest"

        success, message = health_checker._check_config()
        assert success is False
        assert "camera_rtsp_url is required" in message

    def test_check_config_missing_camera_id(self, health_checker):
        """Test config check fails with missing camera_id."""
        health_checker.config.camera_rtsp_url = "rtsp://test"
        health_checker.config.camera_id = ""
        health_checker.config.coreml_model_path = "models/test.mlmodel"
        health_checker.config.ollama_model = "llava:latest"

        success, message = health_checker._check_config()
        assert success is False
        assert "camera_id is required" in message

    def test_check_config_invalid_motion_threshold(self, health_checker):
        """Test config check fails with invalid motion_threshold."""
        health_checker.config.camera_rtsp_url = "rtsp://test"
        health_checker.config.camera_id = "test"
        health_checker.config.coreml_model_path = "models/test.mlmodel"
        health_checker.config.ollama_model = "llava:latest"
        health_checker.config.motion_threshold = 300  # Invalid > 255

        success, message = health_checker._check_config()
        assert success is False
        assert "motion_threshold must be between 0-255" in message

    def test_check_config_invalid_storage_limit(self, health_checker):
        """Test config check fails with invalid max_storage_gb."""
        health_checker.config.camera_rtsp_url = "rtsp://test"
        health_checker.config.camera_id = "test"
        health_checker.config.coreml_model_path = "models/test.mlmodel"
        health_checker.config.ollama_model = "llava:latest"
        health_checker.config.max_storage_gb = -1  # Invalid negative

        success, message = health_checker._check_config()
        assert success is False
        assert "max_storage_gb must be positive" in message

    @patch('platform.system')
    @patch('platform.machine')
    @patch('platform.mac_ver')
    def test_check_platform_success(self, mock_mac_ver, mock_machine, mock_system, health_checker):
        """Test platform check passes on valid macOS arm64."""
        mock_system.return_value = 'Darwin'
        mock_machine.return_value = 'arm64'
        mock_mac_ver.return_value = ('14.2', ('', '', ''), 'arm64')

        success, message = health_checker._check_platform()
        assert success is True
        assert "✓ Platform validated: macOS 14.2 on Apple" in message

    @patch('platform.system')
    def test_check_platform_wrong_os(self, mock_system, health_checker):
        """Test platform check fails on non-macOS."""
        mock_system.return_value = 'Linux'

        success, message = health_checker._check_platform()
        assert success is False
        assert "macOS required, detected Linux" in message

    @patch('platform.system')
    @patch('platform.machine')
    def test_check_platform_wrong_arch(self, mock_machine, mock_system, health_checker):
        """Test platform check fails on non-arm64."""
        mock_system.return_value = 'Darwin'
        mock_machine.return_value = 'x86_64'

        success, message = health_checker._check_platform()
        assert success is False
        assert "Apple Silicon (arm64) required, detected x86_64" in message

    @patch('platform.system')
    @patch('platform.machine')
    @patch('platform.mac_ver')
    def test_check_platform_old_macos(self, mock_mac_ver, mock_machine, mock_system, health_checker):
        """Test platform check fails on macOS < 13.0."""
        mock_system.return_value = 'Darwin'
        mock_machine.return_value = 'arm64'
        mock_mac_ver.return_value = ('12.6', ('', '', ''), 'arm64')

        success, message = health_checker._check_platform()
        assert success is False
        assert "macOS 13.0+ required" in message

    def test_check_python_version_success(self, health_checker):
        """Test python version check passes on Python 3.10+."""
        # Python 3.14 is running, which is >= 3.10
        success, message = health_checker._check_python_version()
        assert success is True
        assert "✓ Python version:" in message

    @patch('sys.version_info', (3, 9, 7))
    def test_check_python_version_too_old(self, health_checker):
        """Test python version check fails on Python < 3.10."""
        success, message = health_checker._check_python_version()
        assert success is False
        assert "Python error: Python 3.10+ required, detected 3.9.7" in message

    def test_check_dependencies_success(self, health_checker):
        """Test dependencies check passes when all are available."""
        with patch.dict('sys.modules', {
            'cv2': Mock(__version__="4.8.1"),
            'coremltools': Mock(__version__="7.0"),
            'ollama': Mock()
        }):
            success, message = health_checker._check_dependencies()
            assert success is True
            assert "✓ Dependencies:" in message

    def test_check_dependencies_missing_ollama(self, health_checker):
        """Test dependencies check fails when ollama is missing."""
        with patch.dict('sys.modules', {
            'cv2': Mock(__version__="4.8.1"),
            'coremltools': Mock(__version__="7.0"),
            'ollama': None  # Simulate missing ollama
        }):
            success, message = health_checker._check_dependencies()
            assert success is False
            assert "Ollama not installed" in message

    def test_check_dependencies_old_opencv(self, health_checker):
        """Test dependencies check fails when OpenCV is too old."""
        with patch.dict('sys.modules', {
            'cv2': Mock(__version__="4.5.0"),  # Too old
            'coremltools': Mock(__version__="7.0"),
            'ollama': Mock()
        }):
            success, message = health_checker._check_dependencies()
            assert success is False
            assert "OpenCV 4.5.0 < 4.8.1" in message

    @patch('os.path.exists', return_value=True)
    def test_check_coreml_model_success(self, mock_exists, health_checker):
        """Test CoreML model check passes with valid ANE-compatible model."""
        health_checker.config.coreml_model_path = "models/yolov8n.mlmodel"

        mock_model = Mock()
        mock_model.compute_unit = 'ALL'  # ANE-compatible
        mock_model.model_name = 'YOLOv8n'
        mock_model.input_description = {'image': Mock()}
        mock_model.output_description = {
            'coordinates': Mock(),
            'confidence': Mock(),
            'labels': Mock()
        }

        with patch('coremltools.models.MLModel', return_value=mock_model):
            success, message = health_checker._check_coreml_model()
            assert success is True
            assert "✓ CoreML model loaded: YOLOv8n (ANE-compatible)" in message

    @patch('os.path.exists', return_value=False)
    def test_check_coreml_model_file_not_found(self, mock_exists, health_checker):
        """Test CoreML model check fails when model file doesn't exist."""
        health_checker.config.coreml_model_path = "models/yolov8n.mlmodel"
        success, message = health_checker._check_coreml_model()
        assert success is False
        assert "CoreML model not found:" in message

    @patch('os.path.exists', return_value=True)
    @patch('coremltools.models.MLModel', side_effect=Exception("Invalid model"))
    def test_check_coreml_model_load_failed(self, mock_mlmodel, mock_exists, health_checker):
        """Test CoreML model check fails when model loading throws exception."""
        health_checker.config.coreml_model_path = "models/yolov8n.mlmodel"
        success, message = health_checker._check_coreml_model()
        assert success is False
        assert "CoreML model load failed: Invalid model" in message

    @patch('os.path.exists', return_value=True)
    def test_check_coreml_model_cpu_gpu_only(self, mock_exists, health_checker):
        """Test CoreML model check warns about CPU/GPU-only model."""
        health_checker.config.coreml_model_path = "models/yolov8n.mlmodel"
        mock_model = Mock()
        mock_model.compute_unit = 'CPU_AND_GPU'  # Not ANE-compatible
        mock_model.model_name = 'YOLOv8n'
        mock_model.input_description = {'image': Mock()}
        mock_model.output_description = {
            'coordinates': Mock(),
            'confidence': Mock()
        }

        with patch('coremltools.models.MLModel', return_value=mock_model):
            success, message = health_checker._check_coreml_model()
            assert success is True
            assert "CPU/GPU - consider ANE-optimized model" in message

    @patch('os.path.exists', return_value=True)
    def test_check_coreml_model_missing_image_input(self, mock_exists, health_checker):
        """Test CoreML model check fails when model lacks image input."""
        health_checker.config.coreml_model_path = "models/yolov8n.mlmodel"
        mock_model = Mock()
        mock_model.compute_unit = 'ALL'
        mock_model.input_description = {'text': Mock()}  # No image input
        mock_model.output_description = {
            'coordinates': Mock(),
            'confidence': Mock()
        }

        with patch('coremltools.models.MLModel', return_value=mock_model):
            success, message = health_checker._check_coreml_model()
            assert success is False
            assert "missing image input for object detection" in message

    @patch('os.path.exists', return_value=True)
    def test_check_coreml_model_missing_outputs(self, mock_exists, health_checker):
        """Test CoreML model check fails when model lacks required outputs."""
        health_checker.config.coreml_model_path = "models/yolov8n.mlmodel"
        mock_model = Mock()
        mock_model.compute_unit = 'ALL'
        mock_model.input_description = {'image': Mock()}
        mock_model.output_description = {'text_output': Mock()}  # Missing coordinates/confidence

        with patch('coremltools.models.MLModel', return_value=mock_model):
            success, message = health_checker._check_coreml_model()
            assert success is False
            assert "missing required object detection outputs" in message

    @patch('os.path.exists', return_value=True)
    @patch.dict('sys.modules', {'coremltools': None})
    def test_check_coreml_model_coremltools_missing(self, mock_exists, health_checker):
        """Test CoreML model check fails when coremltools is not installed."""
        health_checker.config.coreml_model_path = "models/yolov8n.mlmodel"
        success, message = health_checker._check_coreml_model()
        assert success is False
        assert "CoreML Tools not installed" in message

    def test_check_ollama_service_success(self, health_checker):
        """Test Ollama service check passes when service is running and model is available."""
        health_checker.config.ollama_model = "llava:7b"

        mock_response = Mock()
        mock_response.models = [Mock(model="llava:7b"), Mock(model="llava:13b")]

        with patch('ollama.list', return_value=mock_response), \
             patch('ollama.show', return_value=Mock()):
            success, message = health_checker._check_ollama_service()
            assert success is True
            assert "✓ Ollama service running, model 'llava:7b' ready" in message

    def test_check_ollama_service_not_running(self, health_checker):
        """Test Ollama service check fails when service is not running."""
        with patch('ollama.list', side_effect=Exception("Connection refused")):
            success, message = health_checker._check_ollama_service()
            assert success is False
            assert "Ollama service not running:" in message

    def test_check_ollama_service_no_models(self, health_checker):
        """Test Ollama service check fails when no models are available."""
        mock_response = Mock()
        mock_response.models = []

        with patch('ollama.list', return_value=mock_response):
            success, message = health_checker._check_ollama_service()
            assert success is False
            assert "no models available" in message

    def test_check_ollama_service_model_not_found(self, health_checker):
        """Test Ollama service check fails when configured model is not available."""
        health_checker.config.ollama_model = "missing-model:latest"

        mock_response = Mock()
        mock_response.models = [Mock(model="llava:7b"), Mock(model="llava:13b")]

        with patch('ollama.list', return_value=mock_response):
            success, message = health_checker._check_ollama_service()
            assert success is False
            assert "Configured model 'missing-model:latest' not available" in message

    def test_check_ollama_service_model_verification_failed(self, health_checker):
        """Test Ollama service check fails when model verification fails."""
        health_checker.config.ollama_model = "llava:7b"

        mock_response = Mock()
        mock_response.models = [Mock(model="llava:7b")]

        with patch('ollama.list', return_value=mock_response), \
             patch('ollama.show', side_effect=Exception("Model verification failed")):
            success, message = health_checker._check_ollama_service()
            assert success is False
            assert "verification failed:" in message

    @patch.dict('sys.modules', {'ollama': None})
    def test_check_ollama_service_ollama_missing(self, health_checker):
        """Test Ollama service check fails when ollama client is not installed."""
        success, message = health_checker._check_ollama_service()
        assert success is False
        assert "Ollama client not installed" in message

    def test_check_rtsp_connectivity_success(self, health_checker):
        """Test RTSP connectivity check passes with valid stream."""
        health_checker.config.camera_rtsp_url = "rtsp://test:pass@192.168.1.100:554/stream"

        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((720, 1280, 3), dtype=np.uint8))  # Valid frame
        mock_cap.get.side_effect = lambda prop: 30.0 if prop == cv2.CAP_PROP_FPS else 0x34363248  # H264 codec

        with patch('cv2.VideoCapture', return_value=mock_cap):
            success, message = health_checker._check_rtsp_connectivity()
            assert success is True
            assert "✓ RTSP connected:" in message
            assert "1280x720" in message

    def test_check_rtsp_connectivity_connection_failed(self, health_checker):
        """Test RTSP connectivity check fails when connection cannot be established."""
        health_checker.config.camera_rtsp_url = "rtsp://invalid:stream"

        mock_cap = Mock()
        mock_cap.isOpened.return_value = False

        with patch('cv2.VideoCapture', return_value=mock_cap):
            success, message = health_checker._check_rtsp_connectivity()
            assert success is False
            assert "RTSP connection failed:" in message

    def test_check_rtsp_connectivity_read_failed(self, health_checker):
        """Test RTSP connectivity check fails when unable to read frame."""
        health_checker.config.camera_rtsp_url = "rtsp://test:pass@192.168.1.100:554/stream"

        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (False, None)  # Failed to read frame

        with patch('cv2.VideoCapture', return_value=mock_cap):
            success, message = health_checker._check_rtsp_connectivity()
            assert success is False
            assert "RTSP stream error:" in message

    def test_check_rtsp_connectivity_invalid_resolution(self, health_checker):
        """Test RTSP connectivity check fails with invalid frame resolution."""
        health_checker.config.camera_rtsp_url = "rtsp://test:pass@192.168.1.100:554/stream"

        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((200, 300, 3), dtype=np.uint8))  # Too small

        with patch('cv2.VideoCapture', return_value=mock_cap):
            success, message = health_checker._check_rtsp_connectivity()
            assert success is False
            assert "Invalid resolution 300x200" in message

    def test_check_rtsp_connectivity_invalid_format(self, health_checker):
        """Test RTSP connectivity check fails with invalid frame format."""
        health_checker.config.camera_rtsp_url = "rtsp://test:pass@192.168.1.100:554/stream"

        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((720, 1280), dtype=np.uint8))  # Grayscale, not BGR

        with patch('cv2.VideoCapture', return_value=mock_cap):
            success, message = health_checker._check_rtsp_connectivity()
            assert success is False
            assert "Invalid format" in message

    @patch.dict('sys.modules', {'cv2': None})
    def test_check_rtsp_connectivity_opencv_missing(self, health_checker):
        """Test RTSP connectivity check fails when OpenCV is not installed."""
        success, message = health_checker._check_rtsp_connectivity()
        assert success is False
        assert "OpenCV not installed" in message

    @patch('os.path.exists')
    @patch('os.path.isdir')
    @patch('tempfile.NamedTemporaryFile')
    def test_check_file_permissions_success(self, mock_tempfile, mock_isdir, mock_exists, health_checker):
        """Test file permissions check passes when all directories are writable."""
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_tempfile.return_value.__enter__.return_value.write.return_value = None
        mock_tempfile.return_value.__enter__.return_value.flush.return_value = None

        success, message = health_checker._check_file_permissions()
        assert success is True
        assert "✓ Write permissions verified" in message

    @patch('os.path.exists', return_value=False)
    def test_check_file_permissions_directory_missing(self, mock_exists, health_checker):
        """Test file permissions check fails when directory doesn't exist."""
        success, message = health_checker._check_file_permissions()
        assert success is False
        assert "does not exist" in message

    @patch('os.path.exists', return_value=True)
    @patch('os.path.isdir', return_value=False)
    def test_check_file_permissions_not_directory(self, mock_isdir, mock_exists, health_checker):
        """Test file permissions check fails when path is not a directory."""
        success, message = health_checker._check_file_permissions()
        assert success is False
        assert "is not a directory" in message

    @patch('os.path.exists', return_value=True)
    @patch('os.path.isdir', return_value=True)
    @patch('tempfile.NamedTemporaryFile', side_effect=OSError("Permission denied"))
    def test_check_file_permissions_write_denied(self, mock_tempfile, mock_isdir, mock_exists, health_checker):
        """Test file permissions check fails when write access is denied."""
        success, message = health_checker._check_file_permissions()
        assert success is False
        assert "No write permission" in message

    @patch('core.storage_monitor.StorageMonitor')
    def test_check_storage_availability_success(self, mock_storage_monitor_class, health_checker):
        """Test storage availability check passes with normal usage."""
        # Mock StorageMonitor instance and its check_usage method
        mock_monitor = Mock()
        mock_stats = Mock()
        mock_stats.total_bytes = 20 * 1024**3  # 20GB used
        mock_stats.limit_bytes = 50 * 1024**3  # 50GB limit
        mock_stats.percentage_used = 0.4  # 40%
        mock_stats.is_over_limit = False
        mock_monitor.check_usage.return_value = mock_stats
        mock_storage_monitor_class.return_value = mock_monitor

        success, message = health_checker._check_storage_availability()
        assert success is True
        assert "✓ Storage:" in message

    @patch('core.storage_monitor.StorageMonitor')
    def test_check_storage_availability_limit_exceeded(self, mock_storage_monitor_class, health_checker):
        """Test storage availability check fails when limit is exceeded."""
        # Mock StorageMonitor instance and its check_usage method
        mock_monitor = Mock()
        mock_stats = Mock()
        mock_stats.total_bytes = 60 * 1024**3  # 60GB used
        mock_stats.limit_bytes = 50 * 1024**3  # 50GB limit
        mock_stats.percentage_used = 1.2  # 120%
        mock_stats.is_over_limit = True
        mock_monitor.check_usage.return_value = mock_stats
        mock_storage_monitor_class.return_value = mock_monitor

        success, message = health_checker._check_storage_availability()
        assert success is False
        assert "Storage limit exceeded" in message

    @patch('core.storage_monitor.StorageMonitor')
    def test_check_storage_availability_warning(self, mock_storage_monitor_class, health_checker):
        """Test storage availability check warns when usage is high."""
        # Mock StorageMonitor instance and its check_usage method
        mock_monitor = Mock()
        mock_stats = Mock()
        mock_stats.total_bytes = 45 * 1024**3  # 45GB used
        mock_stats.limit_bytes = 50 * 1024**3  # 50GB limit
        mock_stats.percentage_used = 0.9  # 90%
        mock_stats.is_over_limit = False
        mock_monitor.check_usage.return_value = mock_stats
        mock_storage_monitor_class.return_value = mock_monitor

        success, message = health_checker._check_storage_availability()
        assert success is True
        assert "⚠ Storage usage high:" in message

    @patch('builtins.print')
    def test_display_startup_header_success(self, mock_print, health_checker):
        """Test display_startup_header with successful version retrieval."""
        with patch('core.version.get_version_info') as mock_get_version_info:
            mock_version_info = Mock()
            mock_version_info.version = "1.2.3"
            mock_get_version_info.return_value = mock_version_info

            health_checker.display_startup_header()

            mock_print.assert_called_once_with("[STARTUP] Video Recognition System v1.2.3")

    @patch('builtins.print')
    def test_display_startup_header_import_error(self, mock_print, health_checker):
        """Test display_startup_header with import error fallback."""
        with patch('core.version.get_version_info', side_effect=ImportError("Module not found")):
            health_checker.display_startup_header()

            mock_print.assert_called_once_with("[STARTUP] Video Recognition System vunknown")

    @patch('builtins.print')
    def test_check_all_with_display_output_true(self, mock_print, health_checker):
        """Test check_all with display_output=True shows formatted output."""
        # Mock all checks to pass
        with patch.object(health_checker, '_check_config', return_value=(True, "✓ Config: valid")), \
             patch.object(health_checker, '_check_platform', return_value=(True, "✓ Platform: macOS arm64")), \
             patch.object(health_checker, '_check_python_version', return_value=(True, "✓ Python: 3.10+")), \
             patch.object(health_checker, '_check_dependencies', return_value=(True, "✓ Dependencies: all present")), \
             patch.object(health_checker, '_check_coreml_model', return_value=(True, "✓ CoreML: model loaded")), \
             patch.object(health_checker, '_check_ollama_service', return_value=(True, "✓ Ollama: service available")), \
             patch.object(health_checker, '_check_rtsp_connectivity', return_value=(True, "✓ RTSP: camera connected")), \
             patch.object(health_checker, '_check_file_permissions', return_value=(True, "✓ Permissions: write access")), \
             patch.object(health_checker, '_check_storage_availability', return_value=(True, "✓ Storage: 10.0GB available")):

            result = health_checker.check_all(display_output=True)

            assert result.all_passed is True
            assert result.failed_checks == []
            assert result.warnings == []

            # Verify print calls for each check
            expected_calls = [
                "[STARTUP] Video Recognition System v1.0.0",
                "[CONFIG] ✓ Config: valid",
                "[PLATFORM] ✓ Platform: macOS arm64",
                "[PYTHON] ✓ Python: 3.10+",
                "[DEPENDENCIES] ✓ Dependencies: all present",
                "[MODELS] ✓ CoreML: model loaded",
                "[OLLAMA] ✓ Ollama: service available",
                "[CAMERA] ✓ RTSP: camera connected",
                "[PERMISSIONS] ✓ Permissions: write access",
                "[STORAGE] ✓ Storage: 10.0GB available",
                "[READY] ✓ All health checks passed"
            ]
            assert mock_print.call_count == len(expected_calls)
            for i, expected in enumerate(expected_calls):
                assert mock_print.call_args_list[i][0][0] == expected

    @patch('builtins.print')
    def test_check_all_with_display_output_false(self, mock_print, health_checker):
        """Test check_all with display_output=False suppresses output."""
        # Mock all checks to pass
        with patch.object(health_checker, '_check_config', return_value=(True, "✓ Config: valid")), \
             patch.object(health_checker, '_check_platform', return_value=(True, "✓ Platform: macOS arm64")), \
             patch.object(health_checker, '_check_python_version', return_value=(True, "✓ Python: 3.10+")), \
             patch.object(health_checker, '_check_dependencies', return_value=(True, "✓ Dependencies: all present")), \
             patch.object(health_checker, '_check_coreml_model', return_value=(True, "✓ CoreML: model loaded")), \
             patch.object(health_checker, '_check_ollama_service', return_value=(True, "✓ Ollama: service available")), \
             patch.object(health_checker, '_check_rtsp_connectivity', return_value=(True, "✓ RTSP: camera connected")), \
             patch.object(health_checker, '_check_file_permissions', return_value=(True, "✓ Permissions: write access")), \
             patch.object(health_checker, '_check_storage_availability', return_value=(True, "✓ Storage: 10.0GB available")):

            result = health_checker.check_all(display_output=False)

            assert result.all_passed is True
            assert result.failed_checks == []
            assert result.warnings == []

            # Verify no print calls were made
            mock_print.assert_not_called()

    @patch('builtins.print')
    def test_check_all_with_failures_and_display_output(self, mock_print, health_checker):
        """Test check_all with failures shows formatted output including failures."""
        # Mock some checks to fail
        with patch.object(health_checker, '_check_config', return_value=(True, "✓ Config: valid")), \
             patch.object(health_checker, '_check_platform', return_value=(False, "Platform: unsupported")), \
             patch.object(health_checker, '_check_python_version', return_value=(True, "✓ Python: 3.10+")), \
             patch.object(health_checker, '_check_dependencies', return_value=(False, "Dependencies: missing opencv")), \
             patch.object(health_checker, '_check_coreml_model', return_value=(True, "✓ CoreML: model loaded")), \
             patch.object(health_checker, '_check_ollama_service', return_value=(True, "✓ Ollama: service available")), \
             patch.object(health_checker, '_check_rtsp_connectivity', return_value=(True, "✓ RTSP: camera connected")), \
             patch.object(health_checker, '_check_file_permissions', return_value=(True, "✓ Permissions: write access")), \
             patch.object(health_checker, '_check_storage_availability', return_value=(True, "⚠ Storage: usage high")):

            result = health_checker.check_all(display_output=True)

            assert result.all_passed is False
            assert len(result.failed_checks) == 2
            assert len(result.warnings) == 1

            # Verify print calls include failures and final status
            expected_calls = [
                "[STARTUP] Video Recognition System v1.0.0",
                "[CONFIG] ✓ Config: valid",
                "[PLATFORM] ✗ Platform: unsupported",
                "[PYTHON] ✓ Python: 3.10+",
                "[DEPENDENCIES] ✗ Dependencies: missing opencv",
                "[MODELS] ✓ CoreML: model loaded",
                "[OLLAMA] ✓ Ollama: service available",
                "[CAMERA] ✓ RTSP: camera connected",
                "[PERMISSIONS] ✓ Permissions: write access",
                "[STORAGE] ⚠ Storage: usage high",
                "[ERROR] ✗ 2 health check(s) failed, 1 warning(s). Cannot start processing."
            ]
            assert mock_print.call_count == len(expected_calls)
            for i, expected in enumerate(expected_calls):
                assert mock_print.call_args_list[i][0][0] == expected

    @patch('cv2.VideoCapture')
    def test_check_rtsp_connectivity_timeout(self, mock_video_capture, health_checker):
        """Test RTSP connectivity check times out properly."""
        import time
        health_checker.config.camera_rtsp_url = "rtsp://test:stream"

        # Mock VideoCapture that hangs during connection
        def hanging_init(rtsp_url):
            time.sleep(0.2)  # Sleep longer than timeout
            mock_cap = Mock()
            mock_cap.isOpened.return_value = False
            return mock_cap

        mock_video_capture.side_effect = hanging_init

        # Set very short timeout for test
        health_checker.timeout = 0.1

        success, message = health_checker._check_rtsp_connectivity()
        assert success is False
        assert "RTSP connection timeout" in message
        assert "within 0.1s" in message

    @patch('cv2.VideoCapture')
    def test_check_rtsp_connectivity_read_timeout(self, mock_video_capture, health_checker):
        """Test RTSP frame read times out properly."""
        import time
        health_checker.config.camera_rtsp_url = "rtsp://test:stream"

        # Mock VideoCapture that opens but read hangs
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True

        def hanging_read():
            time.sleep(0.2)  # Sleep longer than timeout
            return (False, None)

        mock_cap.read.side_effect = hanging_read
        mock_video_capture.return_value = mock_cap

        # Set very short timeout for test
        health_checker.timeout = 0.1

        success, message = health_checker._check_rtsp_connectivity()
        assert success is False
        assert "RTSP read timeout" in message
        assert "within 0.1s" in message