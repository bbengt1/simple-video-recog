#!/usr/bin/env python3
"""Main entry point for the video recognition system.

This script initializes the system, performs health checks, and starts
the video processing pipeline.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.config import SystemConfig, load_config
from core.logging_config import setup_logging
from core.health_check import HealthChecker
from core.motion_detector import MotionDetector
from integrations.rtsp_client import RTSPCameraClient
from core.logging_config import get_logger

logger = get_logger(__name__)


def main():
    """Main application entry point."""
    try:
        # Load configuration
        if len(sys.argv) > 1:
            config_path = sys.argv[1]
        else:
            config_path = "config/config.yaml"
        config = load_config(config_path)

        # Setup logging
        setup_logging(config)

        logger.info("Starting video recognition system...")

        # Initialize components
        rtsp_client = RTSPCameraClient(config)
        motion_detector = MotionDetector(config)

        # Perform health checks
        health_checker = HealthChecker(config, rtsp_client, motion_detector)

        if not health_checker.run_checks():
            logger.error(
                "System health check failed. Please check the error messages above "
                "and fix any configuration or connectivity issues before restarting."
            )
            sys.exit(1)

        # TODO: Start processing pipeline (Story 1.7)
        logger.info("System initialization complete. Processing pipeline would start here.")

        # For now, just keep the system running
        try:
            while True:
                pass  # Replace with actual processing loop in Story 1.7
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
            rtsp_client.disconnect()
            logger.info("System shutdown complete")

    except Exception as e:
        logger.error(f"Fatal error during startup: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()