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
from integrations.rtsp_client import RTSPCameraClient
from core.logging_config import get_logger

logger = get_logger(__name__)


def parse_arguments():
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Local Video Recognition System - Motion detection with CoreML object detection and Ollama LLM semantic understanding",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py config.yaml                    # Run with config file
  python main.py config/config.yaml             # Run with full path
        """
    )

    parser.add_argument(
        "config_file",
        help="Path to YAML configuration file"
    )

    return parser.parse_args()


def main():
    """Main application entry point."""
    try:
        # Parse command-line arguments
        args = parse_arguments()

        # Load configuration
        config = load_config(args.config_file)

        # Setup logging
        setup_logging(config)

        logger.info("Starting video recognition system...")

        # Initialize components
        rtsp_client = RTSPCameraClient(config)
        motion_detector = MotionDetector(config)
        frame_sampler = FrameSampler(config)

        # Perform health checks
        health_checker = HealthChecker(config, rtsp_client, motion_detector)

        if not health_checker.run_checks():
            logger.error(
                "System health check failed. Please check the error messages above "
                "and fix any configuration or connectivity issues before restarting."
            )
            sys.exit(1)

        # Initialize and start processing pipeline
        pipeline = ProcessingPipeline(
            rtsp_client=rtsp_client,
            motion_detector=motion_detector,
            frame_sampler=frame_sampler,
            config=config
        )

        logger.info("System initialization complete. Starting processing pipeline...")

        # Start the processing pipeline (runs until shutdown signal)
        pipeline.run()

        # Pipeline completed (shutdown signal received)
        logger.info("Processing pipeline stopped. System shutdown complete.")

    except Exception as e:
        logger.error(f"Fatal error during startup: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()