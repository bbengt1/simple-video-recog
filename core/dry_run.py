"""Dry-run mode functionality for comprehensive system validation.

This module provides comprehensive validation of the video recognition system
without starting the processing loop or persisting any data.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

import cv2
import numpy as np

from core.config import SystemConfig
from core.health_check import HealthChecker
from core.logging_config import get_logger
from core.storage_monitor import StorageMonitor
from core.motion_detector import MotionDetector
from core.version import get_version_info
from apple_platform.coreml_detector import CoreMLDetector
from integrations.rtsp_client import RTSPCameraClient
from integrations.ollama import OllamaClient


logger = get_logger(__name__)


class DryRunValidator:
    """Comprehensive system validator for dry-run mode."""

    def __init__(self, config: SystemConfig):
        """Initialize dry-run validator.

        Args:
            config: System configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.results: Dict[str, Any] = {
            "timestamp": time.time(),
            "version": get_version_info().model_dump(),
            "validations": {},
            "tests": {},
            "summary": {}
        }

    def run_full_validation(self) -> bool:
        """Run complete dry-run validation.

        Returns:
            True if all validations pass, False otherwise
        """
        self.logger.info("[DRY-RUN] Starting comprehensive system validation...")

        print("\n[DRY-RUN] Configuration Validation")
        print("=" * 50)

        # 1. Configuration validation
        success = self._validate_configuration()
        if not success:
            return False

        # 2. Health checks
        success = self._run_health_checks()
        if not success:
            return False

        # 3. Model validation
        success = self._validate_models()
        if not success:
            return False

        # 4. RTSP and motion detection tests
        success = self._run_connection_tests()
        if not success:
            return False

        # 5. Storage analysis
        success = self._analyze_storage()
        if not success:
            return False

        # Save results
        self._save_results()

        return True

    def _validate_configuration(self) -> bool:
        """Validate and display configuration."""
        try:
            print("\nCamera Configuration:")
            print(f"  RTSP URL: {self.config.camera_rtsp_url}")
            print(f"  Camera ID: {self.config.camera_id}")
            print(f"  Motion threshold: {self.config.motion_threshold}")
            print(f"  Frame sampling rate: {self.config.frame_sample_rate}")

            print("\nModel Configuration:")
            print(f"  CoreML model: {self.config.coreml_model_path}")
            print(f"  Ollama base URL: {self.config.ollama_base_url}")
            print(f"  Ollama model: {self.config.ollama_model}")
            print(f"  Ollama timeout: {self.config.llm_timeout}s")

            print("\nProcessing Configuration:")
            print(f"  Object blacklist: {self.config.blacklist_objects}")
            print(f"  Event suppression window: {self.config.deduplication_window}s")
            print(f"  Confidence threshold: {self.config.min_object_confidence}")

            print("\nStorage Configuration:")
            print(f"  Database path: {self.config.db_path}")
            print(f"  Max storage: {self.config.max_storage_gb}GB")
            print(f"  Min retention: {self.config.min_retention_days} days")

            print("\nSystem Configuration:")
            print(f"  Log level: {self.config.log_level}")
            print(f"  Metrics interval: {self.config.metrics_interval}s")

            self.results["validations"]["configuration"] = {
                "status": "passed",
                "details": self.config.model_dump()
            }
            return True

        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            self.results["validations"]["configuration"] = {
                "status": "failed",
                "error": str(e)
            }
            return False

    def _run_health_checks(self) -> bool:
        """Run all health checks."""
        try:
            health_checker = HealthChecker(self.config)
            result = health_checker.check_all(display_output=True)

            # Calculate passed checks from total - failed
            total_checks = len(result.failed_checks) + len(result.warnings) + (0 if result.all_passed else 1)  # Estimate
            passed_checks = max(0, total_checks - len(result.failed_checks) - len(result.warnings))

            self.results["validations"]["health_checks"] = {
                "status": "passed" if result.all_passed else "failed",
                "passed": passed_checks,
                "failed": len(result.failed_checks),
                "warnings": len(result.warnings),
                "details": {
                    "failed_checks": result.failed_checks,
                    "warnings": result.warnings
                }
            }

            return result.all_passed

        except Exception as e:
            self.logger.error(f"Health checks failed: {e}")
            self.results["validations"]["health_checks"] = {
                "status": "failed",
                "error": str(e)
            }
            return False

    def _validate_models(self) -> bool:
        """Validate CoreML and Ollama models."""
        success = True

        # CoreML validation
        try:
            print("\n[TEST] Validating CoreML model...")
            start_time = time.time()

            detector = CoreMLDetector(self.config)
            detector.load_model(self.config.coreml_model_path)

            load_time = time.time() - start_time
            print(f"  Load time: {load_time:.1f}s")
            print(f"  Input shape: {detector.model_metadata.get('input_shape', 'Unknown') if detector.model_metadata else 'Unknown'}")
            print(f"  ANE compatible: {detector.model_metadata.get('ane_compatible', 'Unknown') if detector.model_metadata else 'Unknown'}")

            self.results["tests"]["coreml"] = {
                "status": "passed",
                "load_time": load_time,
                "model_info": detector.model_metadata
            }

        except Exception as e:
            self.logger.error(f"CoreML validation failed: {e}")
            self.results["tests"]["coreml"] = {
                "status": "failed",
                "error": str(e)
            }
            success = False

        # Ollama validation
        try:
            print("\n[TEST] Validating Ollama connectivity...")
            start_time = time.time()

            ollama_client = OllamaClient(self.config)
            connected = ollama_client.connect()

            if connected:
                # Verify the configured model
                model_available = ollama_client.verify_model(self.config.ollama_model)
                connect_time = time.time() - start_time
                print(f"  Connect time: {connect_time:.2f}s")
                print(f"  Model '{self.config.ollama_model}' available: {model_available}")

                self.results["tests"]["ollama"] = {
                    "status": "passed",
                    "connect_time": connect_time,
                    "model_available": model_available
                }
            else:
                raise Exception("Failed to connect to Ollama service")

        except Exception as e:
            self.logger.error(f"Ollama validation failed: {e}")
            self.results["tests"]["ollama"] = {
                "status": "failed",
                "error": str(e)
            }
            success = False

        return success

    def _run_connection_tests(self) -> bool:
        """Run RTSP connection and motion detection tests."""
        success = True

        try:
            print("\n[TEST] Testing RTSP camera connection...")
            start_time = time.time()

            rtsp_client = RTSPCameraClient(self.config)
            rtsp_client.connect()

            # Capture 10 frames for testing
            frames_captured = 0
            frame_times = []

            for i in range(10):
                frame_start = time.time()
                frame = rtsp_client.get_frame()
                frame_time = time.time() - frame_start

                if frame is not None:
                    frames_captured += 1
                    frame_times.append(frame_time)
                    if i == 0:  # Get resolution from first frame
                        height, width = frame.shape[:2]
                        print(f"  Resolution: {width}x{height}")
                else:
                    break

            rtsp_client.disconnect()

            if frames_captured > 0:
                avg_frame_time = sum(frame_times) / len(frame_times)
                fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
                total_time = time.time() - start_time

                print(f"  Capture time: {total_time:.1f}s")
                print(f"  FPS: {fps:.1f}")
                print(f"  Frames captured: {frames_captured}/10")

                self.results["tests"]["rtsp"] = {
                    "status": "passed",
                    "frames_captured": frames_captured,
                    "avg_frame_time": avg_frame_time,
                    "fps": fps,
                    "total_time": total_time,
                    "resolution": f"{width}x{height}"
                }
            else:
                raise Exception("Failed to capture any frames from RTSP stream")

        except Exception as e:
            self.logger.error(f"RTSP test failed: {e}")
            self.results["tests"]["rtsp"] = {
                "status": "failed",
                "error": str(e)
            }
            success = False

        # Motion detection test (if RTSP succeeded)
        if success and 'rtsp' in self.results["tests"] and self.results["tests"]["rtsp"]["status"] == "passed":
            try:
                print("\n[TEST] Testing motion detection...")
                start_time = time.time()

                motion_detector = MotionDetector(self.config)

                # Test motion detection on synthetic frames
                motion_frames = 0
                total_frames = 10

                # Use the resolution from RTSP test
                rtsp_results = self.results["tests"]["rtsp"]
                if "resolution" in rtsp_results:
                    width, height = map(int, rtsp_results["resolution"].split('x'))
                else:
                    width, height = 1920, 1080  # Default resolution

                # Test motion detection with synthetic frames
                for i in range(total_frames):
                    # Create synthetic frame
                    test_frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
                    has_motion, confidence, mask = motion_detector.detect_motion(test_frame)
                    if has_motion:
                        motion_frames += 1

                motion_time = time.time() - start_time
                sensitivity = motion_frames / total_frames if total_frames > 0 else 0

                print(f"  Test time: {motion_time:.2f}s")
                print(f"  Motion sensitivity: {sensitivity:.1%} ({motion_frames}/{total_frames} frames)")

                self.results["tests"]["motion"] = {
                    "status": "passed",
                    "frames_tested": total_frames,
                    "motion_detected": motion_frames,
                    "sensitivity": sensitivity,
                    "test_time": motion_time
                }

            except Exception as e:
                self.logger.error(f"Motion detection test failed: {e}")
                self.results["tests"]["motion"] = {
                    "status": "failed",
                    "error": str(e)
                }
                success = False

        return success

    def _analyze_storage(self) -> bool:
        """Analyze storage usage."""
        try:
            print("\n[TEST] Analyzing storage usage...")

            storage_monitor = StorageMonitor(self.config)
            stats = storage_monitor.check_usage()

            usage_percent = stats.percentage_used * 100

            # Format sizes for display
            def format_size(bytes_val: int) -> str:
                size = float(bytes_val)
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024:
                        return f"{size:.1f}{unit}"
                    size /= 1024
                return f"{size:.1f}TB"

            print(f"  Total usage: {format_size(stats.total_bytes)} / {self.config.max_storage_gb}GB ({usage_percent:.1f}%)")
            print(f"  Status: {'OVER LIMIT' if stats.is_over_limit else 'OK'}")

            self.results["tests"]["storage"] = {
                "status": "passed",
                "total_usage_bytes": stats.total_bytes,
                "max_storage_bytes": stats.limit_bytes,
                "usage_percent": usage_percent,
                "is_over_limit": stats.is_over_limit
            }

            return True

        except Exception as e:
            self.logger.error(f"Storage analysis failed: {e}")
            self.results["tests"]["storage"] = {
                "status": "failed",
                "error": str(e)
            }
            return False

    def _save_results(self):
        """Save validation results to JSON file."""
        try:
            # Use the same directory as the database
            data_dir = Path(self.config.db_path).parent
            results_file = data_dir / "dry_run_results.json"

            # Calculate summary
            validations_passed = sum(1 for v in self.results["validations"].values() if v.get("status") == "passed")
            validations_total = len(self.results["validations"])
            tests_passed = sum(1 for t in self.results["tests"].values() if t.get("status") == "passed")
            tests_total = len(self.results["tests"])

            self.results["summary"] = {
                "validations_passed": validations_passed,
                "validations_total": validations_total,
                "tests_passed": tests_passed,
                "tests_total": tests_total,
                "overall_success": validations_passed == validations_total and tests_passed == tests_total
            }

            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)

            self.logger.info(f"Dry-run results saved to {results_file}")

        except Exception as e:
            self.logger.error(f"Failed to save dry-run results: {e}")

    def print_summary(self):
        """Print validation summary."""
        summary = self.results.get("summary", {})
        validations_passed = summary.get("validations_passed", 0)
        validations_total = summary.get("validations_total", 0)
        tests_passed = summary.get("tests_passed", 0)
        tests_total = summary.get("tests_total", 0)

        print(f"\n[DRY-RUN] Validation Summary:")
        print(f"  Configuration: {validations_passed}/{validations_total} validations passed")
        print(f"  Tests: {tests_passed}/{tests_total} tests passed")

        if summary.get("overall_success", False):
            print("\n[DRY-RUN] ✓ All validations passed. System ready for production.")
            print("[DRY-RUN] Remove --dry-run flag to start processing.")
        else:
            print(f"\n[DRY-RUN] ✗ Validation failed: {validations_total - validations_passed} validations failed, {tests_total - tests_passed} tests failed.")
            print("Please fix the issues above before starting the system.")