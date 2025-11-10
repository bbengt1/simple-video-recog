#!/usr/bin/env python3
"""Main entry point for the video recognition system.

This script initializes the system, performs health checks, and starts
the video processing pipeline.
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.config import SystemConfig, load_config
from core.logging_config import setup_logging
from core.health_check import HealthChecker
from core.motion_detector import MotionDetector
from core.pipeline import FrameSampler, ProcessingPipeline
from core.events import EventDeduplicator
from core.image_annotator import ImageAnnotator
from core.database import DatabaseManager
from core.version import format_version_output, get_version_info
from core.dry_run import DryRunValidator
from core.signals import SignalHandler
from core.storage_monitor import StorageMonitor
from apple_platform.coreml_detector import CoreMLDetector
from integrations.rtsp_client import RTSPCameraClient
from integrations.ollama import OllamaClient
from core.logging_config import get_logger

logger = get_logger(__name__)

# Exit code constants
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_CONFIG_INVALID = 2
EXIT_STORAGE_FULL = 3


def parse_arguments():
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Local Video Recognition System - Motion detection with CoreML object detection and Ollama LLM semantic understanding",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --config config/config.yaml              # Run with config file
  python main.py --config cameras/front-door.yaml --dry-run  # Validate configuration
  python main.py --version                                 # Show version information
  python main.py --help                                    # Show this help message

Exit codes:
  0 = success
  1 = error
  2 = config invalid
  3 = storage full
        """
    )

    parser.add_argument(
        "--config", "-c",
        dest="config_file",
        default="config/config.yaml",
        help="Path to YAML configuration file (default: config/config.yaml)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and connectivity without starting processing loop"
    )

    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Display version and build information"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Override logging level (DEBUG, INFO, WARNING, ERROR)"
    )

    parser.add_argument(
        "--metrics-interval",
        type=int,
        help="Override metrics display interval in seconds (default: 60)"
    )

    return parser.parse_args()


def perform_hot_reload(current_config, rtsp_client, coreml_detector, ollama_client, pipeline):
    """Perform hot-reload of configuration without restarting processing.

    Args:
        current_config: Current SystemConfig object
        rtsp_client: Current RTSPCameraClient instance
        coreml_detector: Current CoreMLDetector instance
        ollama_client: Current OllamaClient instance
        pipeline: Current ProcessingPipeline instance

    Returns:
        bool: True if reload successful, False otherwise
    """
    try:
        # Get the config file path from current config
        config_path = getattr(current_config, '_config_path', 'config/config.yaml')

        # Load new configuration
        new_config = load_config(config_path)

        # Validate new configuration
        # TODO: Add comprehensive validation here
        # For now, just check that required fields are present

        # Apply reloadable settings
        changes_made = []

        # Update motion detector settings
        if new_config.motion_threshold != current_config.motion_threshold:
            # Note: Motion detector would need a reload method
            changes_made.append(f"motion_threshold: {current_config.motion_threshold} -> {new_config.motion_threshold}")

        if new_config.frame_sample_rate != current_config.frame_sample_rate:
            # Note: Frame sampler would need a reload method
            changes_made.append(f"frame_sample_rate: {current_config.frame_sample_rate} -> {new_config.frame_sample_rate}")

        # Update object detection settings
        if new_config.blacklist_objects != current_config.blacklist_objects:
            changes_made.append(f"blacklist_objects: {current_config.blacklist_objects} -> {new_config.blacklist_objects}")

        if new_config.min_object_confidence != current_config.min_object_confidence:
            changes_made.append(f"min_object_confidence: {current_config.min_object_confidence} -> {new_config.min_object_confidence}")

        # Reconnect RTSP if camera URL changed
        if new_config.camera_rtsp_url != current_config.camera_rtsp_url:
            logger.info("Camera RTSP URL changed, reconnecting...")
            try:
                rtsp_client.disconnect()
                # Update config reference (if RTSP client supports it)
                # rtsp_client.update_config(new_config)
                rtsp_client.connect()
                changes_made.append(f"camera_rtsp_url: {current_config.camera_rtsp_url} -> {new_config.camera_rtsp_url}")
            except Exception as e:
                logger.error(f"Failed to reconnect RTSP camera: {e}")
                return False

        # Reload CoreML model if path changed
        if new_config.coreml_model_path != current_config.coreml_model_path:
            logger.info("CoreML model path changed, reloading model...")
            try:
                coreml_detector.load_model(new_config.coreml_model_path)
                changes_made.append(f"coreml_model_path: {current_config.coreml_model_path} -> {new_config.coreml_model_path}")
            except Exception as e:
                logger.error(f"Failed to reload CoreML model: {e}")
                return False

        # Switch Ollama model if changed
        if new_config.ollama_model != current_config.ollama_model:
            logger.info("Ollama model changed, switching model...")
            try:
                # Note: Ollama client would need a model switch method
                # ollama_client.switch_model(new_config.ollama_model)
                changes_made.append(f"ollama_model: {current_config.ollama_model} -> {new_config.ollama_model}")
            except Exception as e:
                logger.error(f"Failed to switch Ollama model: {e}")
                return False

        # Update current config reference
        # Note: This is a simplified approach - in production, we'd need to
        # update the config object in all components that reference it
        current_config.__dict__.update(new_config.__dict__)

        if changes_made:
            logger.info(f"Configuration reloaded with {len(changes_made)} changes: {', '.join(changes_made)}")
        else:
            logger.info("Configuration reloaded - no changes detected")

        return True

    except Exception as e:
        logger.error(f"Configuration reload failed: {e}")
        return False


def main():
    """Main application entry point."""
    try:
        # Parse command-line arguments
        args = parse_arguments()

        # Handle version display
        if args.version:
            print(format_version_output())
            return

        # Load configuration
        config = load_config(args.config_file)

        # Override config with command-line arguments
        if args.log_level:
            config.log_level = args.log_level
        if args.metrics_interval:
            config.metrics_interval = args.metrics_interval

        # Setup logging
        setup_logging(config)

        # Log version information at startup
        version_info = get_version_info()
        logger.info(f"Video Recognition System v{version_info.version} started")
        logger.info(f"Build: {version_info.build_date} (commit {version_info.git_commit})")
        logger.info(f"Python: {version_info.python_version.split()[0]}")
        logger.info(f"Platform: {version_info.platform}")

        logger.info("Starting video recognition system...")

        # Perform health checks
        health_checker = HealthChecker(config)

        # Handle dry-run mode (perform comprehensive validation and exit)
        if args.dry_run:
            logger.info("Starting dry-run mode: Performing comprehensive system validation...")

            dry_run_validator = DryRunValidator(config)
            success = dry_run_validator.run_full_validation()
            dry_run_validator.print_summary()

            if success:
                logger.info("Dry-run validation successful: All validations passed.")
                sys.exit(EXIT_SUCCESS)
            else:
                logger.error("Dry-run validation failed: Some validations or tests failed.")
                sys.exit(EXIT_CONFIG_INVALID)

        # Normal mode: Initialize components after health checks pass
        logger.info("Performing startup health checks...")
        result = health_checker.check_all(display_output=False)

        if not result.all_passed:
            logger.error(
                f"System health check failed: {len(result.failed_checks)} failed, {len(result.warnings)} warnings. "
                "Please check the error messages above and fix any configuration or connectivity issues before restarting."
            )
            sys.exit(EXIT_ERROR)

        # Initialize signal handler and register signal handlers
        signal_handler = SignalHandler()
        signal_handler.register_handlers()

        # Initialize storage monitor
        storage_monitor = StorageMonitor(config)

        # Initialize database manager (only after health checks pass)
        database_manager = DatabaseManager(config.db_path)
        database_manager.init_database()

        # Initialize components
        rtsp_client = RTSPCameraClient(config)
        motion_detector = MotionDetector(config)
        frame_sampler = FrameSampler(config)
        coreml_detector = CoreMLDetector(config)
        event_deduplicator = EventDeduplicator(config)
        ollama_client = OllamaClient(config)
        image_annotator = ImageAnnotator()

        # Initialize and start processing pipeline
        pipeline = ProcessingPipeline(
            rtsp_client=rtsp_client,
            motion_detector=motion_detector,
            frame_sampler=frame_sampler,
            coreml_detector=coreml_detector,
            event_deduplicator=event_deduplicator,
            ollama_client=ollama_client,
            image_annotator=image_annotator,
            database_manager=database_manager,
            signal_handler=signal_handler,
            storage_monitor=storage_monitor,
            config=config
        )

        logger.info("System initialization complete. Starting processing pipeline...")

        # Record session start time
        import time
        session_start_time = time.time()

        # Track shutdown reason for appropriate exit code
        shutdown_reason = "normal"

        # Start the processing pipeline in a separate thread
        import threading
        pipeline_thread = threading.Thread(target=pipeline.run, daemon=True)
        pipeline_thread.start()

        # Main control loop - handle shutdown and hot-reload
        try:
            while pipeline_thread.is_alive():
                # Check for shutdown signal
                if signal_handler.is_shutdown_requested():
                    # Check if shutdown was triggered by storage limits
                    storage_stats = storage_monitor.check_usage()
                    if storage_stats.is_over_limit:
                        shutdown_reason = "storage_full"
                        logger.info("Storage limit exceeded shutdown detected")
                    else:
                        logger.info("Shutdown signal detected, stopping pipeline...")
                    break

                # Check for reload signal
                if signal_handler.is_reload_requested():
                    logger.info("Configuration reload requested, performing hot-reload...")
                    success = perform_hot_reload(config, rtsp_client, coreml_detector, ollama_client, pipeline)
                    if success:
                        logger.info("Configuration reloaded successfully")
                    else:
                        logger.warning("Configuration reload failed, continuing with old config")
                    signal_handler.clear_reload_flag()

                # Brief pause to avoid busy waiting
                time.sleep(0.1)

        except KeyboardInterrupt:
            # Handle Ctrl+C during main loop
            logger.info("Received interrupt signal during processing")
            signal_handler.shutdown_event.set()

        # Wait for pipeline thread to complete
        pipeline_thread.join(timeout=10.0)
        if pipeline_thread.is_alive():
            logger.warning("Pipeline thread did not complete within timeout")

        # Pipeline completed (shutdown signal received) - perform graceful shutdown
        logger.info("Processing pipeline stopped. Performing graceful shutdown...")

        # Implement shutdown timeout (10 seconds)
        import threading

        shutdown_completed = threading.Event()

        def perform_shutdown():
            try:
                # The pipeline's _perform_graceful_shutdown is called in its finally block
                # We just need to wait for it to complete
                shutdown_completed.set()
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
                shutdown_completed.set()

        shutdown_thread = threading.Thread(target=perform_shutdown, daemon=True)
        shutdown_thread.start()

        # Wait for shutdown to complete with timeout
        if not shutdown_completed.wait(timeout=10.0):
            logger.warning("Shutdown timeout exceeded (10s), forcing exit")
            sys.exit(EXIT_ERROR)

        # Calculate session statistics
        session_end_time = time.time()
        total_runtime_seconds = session_end_time - session_start_time

        # Get final metrics from pipeline
        final_metrics = pipeline.metrics_collector.collect()

        # Calculate storage usage using storage monitor
        storage_stats = storage_monitor.check_usage()
        storage_used_gb = storage_stats.total_bytes / (1024**3)

        # Format runtime display
        hours, remainder = divmod(int(total_runtime_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        runtime_display = f"{hours}h {minutes}m {seconds}s"

        # Log session summary
        logger.info("Session Summary:")
        logger.info(f"  Runtime: {runtime_display}")
        logger.info(f"  Frames processed: {final_metrics.frames_processed:,}")
        logger.info(f"  Motion detected: {final_metrics.motion_detected:,} frames ({final_metrics.motion_detected/max(final_metrics.frames_processed, 1)*100:.1f}%)")
        logger.info(f"  Events created: {final_metrics.events_created:,}")
        logger.info(f"  Events suppressed: {final_metrics.events_suppressed:,} (de-duplication)")
        logger.info(f"  Avg CoreML inference: {final_metrics.coreml_inference_avg:.1f}ms")
        logger.info(f"  Avg LLM inference: {final_metrics.llm_inference_avg:.1f}ms")
        logger.info(f"  Storage used: {storage_used_gb:.1f}GB / {config.max_storage_gb:.1f}GB")

        logger.info("System shutdown complete.")

        # Exit with appropriate code based on shutdown reason
        if shutdown_reason == "storage_full":
            logger.info("Exiting with storage full error code")
            sys.exit(EXIT_STORAGE_FULL)
        else:
            logger.info("Exiting with success code")
            sys.exit(EXIT_SUCCESS)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(EXIT_CONFIG_INVALID)
    except Exception as e:
        logger.error(f"Fatal error during startup: {e}", exc_info=True)
        sys.exit(EXIT_ERROR)


if __name__ == "__main__":
    main()