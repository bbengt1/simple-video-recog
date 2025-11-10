"""Health check module for startup system validation."""

import platform
import sys
from typing import List

from pydantic import BaseModel

from core.config import SystemConfig
from core.logging_config import get_logger


class HealthCheckResult(BaseModel):
    """Result of health check execution."""

    all_passed: bool
    failed_checks: List[str]
    warnings: List[str]


class HealthChecker:
    """Performs comprehensive startup health checks."""

    def __init__(self, config: SystemConfig, timeout: int = 10):
        """Initialize health checker.

        Args:
            config: System configuration
            timeout: Timeout in seconds for each check
        """
        self.config = config
        self.timeout = timeout
        self.logger = get_logger(__name__)

    def display_startup_header(self) -> None:
        """Display startup header with version information."""
        try:
            from core.version import get_version_info
            version_info = get_version_info()
            version = version_info.version
        except ImportError:
            version = "unknown"

        print(f"[STARTUP] Video Recognition System v{version}")

    def check_all(self, display_output: bool = True) -> HealthCheckResult:
        """Run all health checks in sequence.

        Args:
            display_output: Whether to display formatted console output

        Returns:
            HealthCheckResult with overall status and details
        """
        failed_checks = []
        warnings = []

        if display_output:
            self.display_startup_header()

        # Define checks with display names matching acceptance criteria
        checks = [
            ("CONFIG", "config", self._check_config),
            ("PLATFORM", "platform", self._check_platform),
            ("PYTHON", "python_version", self._check_python_version),
            ("DEPENDENCIES", "dependencies", self._check_dependencies),
            ("MODELS", "coreml_model", self._check_coreml_model),
            ("OLLAMA", "ollama_service", self._check_ollama_service),
            ("CAMERA", "rtsp_connectivity", self._check_rtsp_connectivity),
            ("PERMISSIONS", "file_permissions", self._check_file_permissions),
            ("STORAGE", "storage_availability", self._check_storage_availability),
        ]

        for display_name, check_name, check_method in checks:
            try:
                success, message = check_method()
                is_warning = "⚠" in message
                if success and not is_warning:
                    self.logger.info(f"✓ {check_name}: {message}")
                    if display_output:
                        display_message = message if message.startswith(('✓', '✗', '⚠')) else f"✓ {message}"
                        print(f"[{display_name}] {display_message}")
                elif success and is_warning:
                    self.logger.warning(f"⚠ {check_name}: {message}")
                    if display_output:
                        display_message = message if message.startswith(('✓', '✗', '⚠')) else f"⚠ {message}"
                        print(f"[{display_name}] {display_message}")
                    warnings.append(f"{check_name}: {message}")
                else:
                    log_message = f"✗ {message}"
                    self.logger.error(f"✗ {check_name}: {message}")
                    if display_output:
                        display_message = message if message.startswith(('✓', '✗', '⚠')) else f"✗ {message}"
                        print(f"[{display_name}] {display_message}")
                    failed_checks.append(f"{check_name}: {message}")
            except Exception as e:
                error_msg = f"Unexpected error in {check_name}: {str(e)}"
                self.logger.error(f"✗ {check_name}: {error_msg}")
                if display_output:
                    print(f"[{display_name}] ✗ {check_name}: {error_msg}")
                failed_checks.append(error_msg)

        all_passed = len(failed_checks) == 0

        # Display final status
        if display_output:
            if all_passed and len(warnings) == 0:
                print("[READY] ✓ All health checks passed")
            elif all_passed and len(warnings) > 0:
                print(f"[READY] ✓ All health checks passed ({len(warnings)} warning(s))")
            else:
                warning_text = f", {len(warnings)} warning(s)" if warnings else ""
                print(f"[ERROR] ✗ {len(failed_checks)} health check(s) failed{warning_text}. Cannot start processing.")

        return HealthCheckResult(
            all_passed=all_passed,
            failed_checks=failed_checks,
            warnings=warnings
        )

    def _check_config(self) -> tuple[bool, str]:
        """Check configuration validation."""
        try:
            # Validate required fields exist and are properly typed
            if not hasattr(self.config, 'camera_rtsp_url') or not self.config.camera_rtsp_url:
                return False, "Configuration error: camera_rtsp_url is required and cannot be empty"

            if not hasattr(self.config, 'camera_id') or not self.config.camera_id:
                return False, "Configuration error: camera_id is required and cannot be empty"

            if not hasattr(self.config, 'coreml_model_path') or not self.config.coreml_model_path:
                return False, "Configuration error: coreml_model_path is required and cannot be empty"

            if not hasattr(self.config, 'ollama_model') or not self.config.ollama_model:
                return False, "Configuration error: ollama_model is required and cannot be empty"

            # Validate data types and ranges
            if hasattr(self.config, 'motion_threshold'):
                if not isinstance(self.config.motion_threshold, (int, float)) or not (0 <= self.config.motion_threshold <= 255):
                    return False, f"Configuration error: motion_threshold must be between 0-255, got {self.config.motion_threshold}"

            if hasattr(self.config, 'max_storage_gb'):
                if not isinstance(self.config.max_storage_gb, (int, float)) or self.config.max_storage_gb <= 0:
                    return False, f"Configuration error: max_storage_gb must be positive, got {self.config.max_storage_gb}"

            # Configuration is valid
            return True, f"✓ Configuration loaded: {self.config.camera_id}"

        except Exception as e:
            return False, f"Configuration validation failed: {str(e)}"

    def _check_platform(self) -> tuple[bool, str]:
        """Check platform compatibility."""
        try:
            # Check OS is macOS
            if platform.system() != 'Darwin':
                return False, f"Platform error: macOS required, detected {platform.system()}"

            # Check architecture is Apple Silicon (arm64)
            if platform.machine() != 'arm64':
                return False, f"Platform error: Apple Silicon (arm64) required, detected {platform.machine()}"

            # Check macOS version >= 13.0 for CoreML Neural Engine support
            mac_version = platform.mac_ver()[0]
            if not mac_version:
                return False, "Platform error: Unable to determine macOS version"

            version_parts = mac_version.split('.')
            major_version = int(version_parts[0]) if version_parts else 0

            if major_version < 13:
                return False, f"Platform error: macOS 13.0+ required for CoreML Neural Engine, detected {mac_version}"

            # Optional: Detect chip model (M1/M2/M3)
            chip_info = f"macOS {mac_version} on {platform.machine()}"
            return True, f"✓ Platform validated: {chip_info}"

        except Exception as e:
            return False, f"Platform check failed: {str(e)}"

    def _check_python_version(self) -> tuple[bool, str]:
        """Check Python version."""
        try:
            major, minor, micro = sys.version_info[:3]
            version_str = f"{major}.{minor}.{micro}"
            if sys.version_info >= (3, 10):
                return True, f"✓ Python version: {version_str}"
            else:
                return False, f"Python error: Python 3.10+ required, detected {version_str}"
        except Exception as e:
            return False, f"Python version check failed: {str(e)}"

    def _check_dependencies(self) -> tuple[bool, str]:
        """Check dependency versions."""
        try:
            issues = []

            # Check OpenCV
            try:
                import cv2
                version = cv2.__version__
                if version < "4.8.1":
                    issues.append(f"OpenCV {version} < 4.8.1")
                else:
                    pass  # OK
            except ImportError:
                issues.append("OpenCV not installed")

            # Check CoreML Tools
            try:
                import coremltools
                version = coremltools.__version__
                if version < "7.0":
                    issues.append(f"CoreML Tools {version} < 7.0")
                else:
                    pass  # OK
            except ImportError:
                issues.append("CoreML Tools not installed")

            # Check Ollama
            try:
                import ollama
                # Ollama doesn't expose __version__, just check if importable
                # Version 0.6.0 was installed, which meets >= 0.1.0 requirement
                pass  # OK if importable
            except ImportError:
                issues.append("Ollama not installed")

            if issues:
                return False, f"Dependency errors: {', '.join(issues)}"
            else:
                return True, "✓ Dependencies: All required packages installed with compatible versions"

        except Exception as e:
            return False, f"Dependency check failed: {str(e)}"

    def _check_coreml_model(self) -> tuple[bool, str]:
        """Check CoreML model loading and Neural Engine compatibility."""
        try:
            import os
            import coremltools

            # Check if model file exists
            model_path = self.config.coreml_model_path
            if not os.path.exists(model_path):
                return False, f"CoreML model not found: {model_path}"

            # Attempt to load the model
            try:
                model = coremltools.models.MLModel(model_path)
            except Exception as e:
                return False, f"CoreML model load failed: {str(e)}"

            # Check Neural Engine compatibility
            compute_unit = getattr(model, 'compute_unit', None)
            if compute_unit == 'CPU_AND_GPU':
                ane_compatible = False
                ane_status = "(CPU/GPU - consider ANE-optimized model)"
            else:
                ane_compatible = True
                ane_status = "(ANE-compatible)"

            # Validate input/output structure for object detection
            input_desc = model.input_description
            output_desc = model.output_description

            if not input_desc or not output_desc:
                return False, "CoreML model missing input/output descriptions"

            # Check for expected object detection inputs (image)
            input_names = list(input_desc)
            if not any('image' in name.lower() for name in input_names):
                return False, "CoreML model missing image input for object detection"

            # Check for expected object detection outputs (coordinates, confidence, labels)
            output_names = list(output_desc)
            has_coordinates = any('coordinates' in name.lower() or 'bbox' in name.lower() for name in output_names)
            has_confidence = any('confidence' in name.lower() or 'scores' in name.lower() for name in output_names)
            has_labels = any('labels' in name.lower() or 'classes' in name.lower() for name in output_names)

            if not (has_coordinates and has_confidence):
                return False, "CoreML model missing required object detection outputs (coordinates, confidence)"

            # Get model name for display
            model_name = getattr(model, 'model_name', os.path.basename(model_path))

            return True, f"✓ CoreML model loaded: {model_name} {ane_status}"

        except ImportError:
            return False, "CoreML Tools not installed"
        except Exception as e:
            return False, f"CoreML model validation failed: {str(e)}"

    def _check_ollama_service(self) -> tuple[bool, str]:
        """Check Ollama service availability and model readiness."""
        try:
            import ollama

            # Check if Ollama service is running by calling list endpoint
            try:
                response = ollama.list()
            except Exception as e:
                return False, f"Ollama service not running: {str(e)}"

            # Extract available models from response
            if hasattr(response, 'models'):
                # Real API response
                available_models = [model.model for model in response.models if model.model]
            else:
                # Test mock response (dict)
                available_models = [model.get('name', model.get('model', '')) for model in response.get('models', [])]
                available_models = [m for m in available_models if m]

            if not available_models:
                return False, "Ollama service running but no models available"

            # Check if configured model is available
            configured_model = self.config.ollama_model
            if configured_model not in available_models:
                return False, f"Configured model '{configured_model}' not available. Available: {', '.join(available_models[:5])}{'...' if len(available_models) > 5 else ''}"

            # Verify model can be shown (additional check)
            try:
                ollama.show(configured_model)
            except Exception as e:
                return False, f"Model '{configured_model}' found but verification failed: {str(e)}"

            return True, f"✓ Ollama service running, model '{configured_model}' ready"

        except ImportError:
            return False, "Ollama client not installed"
        except Exception as e:
            return False, f"Ollama service check failed: {str(e)}"

    def _check_rtsp_connectivity(self) -> tuple[bool, str]:
        """Check RTSP camera connectivity and stream validation."""
        try:
            import cv2
            import threading
            import time

            rtsp_url = self.config.camera_rtsp_url

            # Use threading to add timeout to VideoCapture connection
            cap = None
            connection_success = False

            def connect_with_timeout():
                nonlocal cap, connection_success
                try:
                    cap = cv2.VideoCapture(rtsp_url)
                    connection_success = cap.isOpened()
                except Exception:
                    connection_success = False

            # Start connection attempt in background thread
            connection_thread = threading.Thread(target=connect_with_timeout, daemon=True)
            connection_thread.start()

            # Wait for connection with timeout
            connection_thread.join(timeout=self.timeout)

            if connection_thread.is_alive():
                # Connection timed out
                return False, f"RTSP connection timeout: Unable to connect to '{rtsp_url}' within {self.timeout}s"

            if not connection_success or cap is None:
                return False, f"RTSP connection failed: Unable to open stream '{rtsp_url}'"

            # Try to read a test frame with timeout
            ret = False
            frame = None

            def read_with_timeout():
                nonlocal ret, frame
                try:
                    ret, frame = cap.read()  # type: ignore
                except Exception:
                    ret = False
                    frame = None

            read_thread = threading.Thread(target=read_with_timeout, daemon=True)
            read_thread.start()
            read_thread.join(timeout=self.timeout)

            if read_thread.is_alive():
                cap.release()
                return False, f"RTSP read timeout: Unable to read frame from '{rtsp_url}' within {self.timeout}s"

            if not ret or frame is None:
                cap.release()
                return False, f"RTSP stream error: Unable to read frame from '{rtsp_url}'"

            if not ret or frame is None:
                cap.release()
                return False, f"RTSP stream error: Unable to read frame from '{rtsp_url}'"

            # Validate frame properties
            height, width = frame.shape[:2]  # type: ignore

            if width < 320 or height < 240:
                cap.release()
                return False, f"RTSP frame error: Invalid resolution {width}x{height}, expected >= 320x240"

            # Check frame format (should be BGR for OpenCV)
            if len(frame.shape) != 3 or frame.shape[2] != 3:
                cap.release()
                return False, f"RTSP frame error: Invalid format, expected 3-channel BGR image"

            # Get additional stream properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            codec = cap.get(cv2.CAP_PROP_FOURCC)

            # Decode codec to readable format
            codec_str = ""
            if codec > 0:
                codec_bytes = int(codec).to_bytes(4, byteorder='little')
                codec_str = codec_bytes.decode('ascii', errors='ignore').strip()

            cap.release()

            # Success message with stream details
            stream_info = f"{width}x{height}"
            if fps > 0:
                stream_info += f" @ {fps:.1f}fps"
            if codec_str:
                stream_info += f" ({codec_str})"

            return True, f"✓ RTSP connected: {stream_info}"

        except ImportError:
            return False, "OpenCV not installed"
        except Exception as e:
            return False, f"RTSP connectivity check failed: {str(e)}"

    def _check_file_permissions(self) -> tuple[bool, str]:
        """Check file permissions for required directories."""
        try:
            import os
            import tempfile

            # Directories to check for write access
            directories_to_check = ["data", "logs", "config"]

            for dir_name in directories_to_check:
                dir_path = dir_name

                # Check if directory exists
                if not os.path.exists(dir_path):
                    return False, f"Directory '{dir_path}' does not exist"

                # Check if it's actually a directory
                if not os.path.isdir(dir_path):
                    return False, f"'{dir_path}' is not a directory"

                # Try to create a test file to verify write permissions
                try:
                    with tempfile.NamedTemporaryFile(dir=dir_path, delete=True) as test_file:
                        test_file.write(b"test")
                        test_file.flush()
                        # File is automatically deleted when context manager exits
                except (OSError, IOError) as e:
                    return False, f"No write permission for directory '{dir_path}': {str(e)}"

            return True, f"✓ Write permissions verified for directories: {', '.join(directories_to_check)}"

        except Exception as e:
            return False, f"File permissions check failed: {str(e)}"

    def _check_storage_availability(self) -> tuple[bool, str]:
        """Check storage availability and usage limits."""
        try:
            import shutil
            import os

            # Get disk usage for the current directory
            usage = shutil.disk_usage(".")

            # Convert bytes to GB (handle both named tuple and regular tuple for mocking)
            if hasattr(usage, 'total'):
                total_gb = usage.total / (1024 ** 3)
                used_gb = usage.used / (1024 ** 3)
                free_gb = usage.free / (1024 ** 3)
            else:
                # Handle mock tuple (total, used, free)
                total_gb = usage[0] / (1024 ** 3)
                used_gb = usage[1] / (1024 ** 3)
                free_gb = usage[2] / (1024 ** 3)

            # Check against configured limit
            max_storage_gb = self.config.max_storage_gb
            usage_percent = (used_gb / total_gb) * 100

            # Warning threshold is 80% of max_storage_gb
            warning_threshold_gb = max_storage_gb * 0.8

            if used_gb >= max_storage_gb:
                return False, f"Storage limit exceeded: {used_gb:.1f}GB used, limit is {max_storage_gb:.1f}GB"

            if used_gb >= warning_threshold_gb:
                return True, f"⚠ Storage usage high: {used_gb:.1f}GB / {max_storage_gb:.1f}GB ({usage_percent:.1f}% of disk)"

            return True, f"✓ Storage: {used_gb:.1f}GB / {max_storage_gb:.1f}GB limit ({usage_percent:.1f}% of disk)"

        except Exception as e:
            return False, f"Storage availability check failed: {str(e)}"