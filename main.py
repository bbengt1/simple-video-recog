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
from core.version import format_version_output
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

        logger.info("Starting video recognition system...")

        # Initialize components
        rtsp_client = RTSPCameraClient(config)
        motion_detector = MotionDetector(config)
        frame_sampler = FrameSampler(config)
        coreml_detector = CoreMLDetector(config)
        event_deduplicator = EventDeduplicator(config)
        ollama_client = OllamaClient(config)
        image_annotator = ImageAnnotator()

        # Perform health checks
        health_checker = HealthChecker(config, rtsp_client, motion_detector)

        if not health_checker.run_checks():
            logger.error(
                "System health check failed. Please check the error messages above "
                "and fix any configuration or connectivity issues before restarting."
            )
            sys.exit(EXIT_ERROR)

        # Handle dry-run mode
        if args.dry_run:
            logger.info("Dry-run mode: Configuration and connectivity validation successful.")
            print("Configuration and connectivity validation successful.")
            sys.exit(EXIT_SUCCESS)

        # Initialize and start processing pipeline
        pipeline = ProcessingPipeline(
            rtsp_client=rtsp_client,
            motion_detector=motion_detector,
            frame_sampler=frame_sampler,
            coreml_detector=coreml_detector,
            event_deduplicator=event_deduplicator,
            ollama_client=ollama_client,
            image_annotator=image_annotator,
            config=config
        )

        logger.info("System initialization complete. Starting processing pipeline...")

        # Start the processing pipeline (runs until shutdown signal)
        pipeline.run()

        # Pipeline completed (shutdown signal received)
        logger.info("Processing pipeline stopped. System shutdown complete.")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(EXIT_CONFIG_INVALID)
    except Exception as e:
        logger.error(f"Fatal error during startup: {e}", exc_info=True)
        sys.exit(EXIT_ERROR)


if __name__ == "__main__":
    main()