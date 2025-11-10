#!/usr/bin/env python3
"""Web server entry point for the video recognition system.

This script starts the FastAPI web server that serves the dashboard
and provides REST API endpoints for event access.
"""

import logging
import os
import sys
from pathlib import Path

import uvicorn

from core.config import load_config
from core.logging_config import setup_logging


def main():
    # Load configuration first (needed for logging setup)
    try:
        config = load_config("config/config.yaml")
    except Exception as e:
        # Basic logging setup for error reporting
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Setup logging with config
    setup_logging(config)
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("Local Video Recognition System - Web Server")
    logger.info("=" * 60)

    # Verify database exists
    db_path = Path(config.db_path)
    if not db_path.exists():
        logger.error(f"Database not found at {db_path}")
        logger.error("Please run the main application first to create the database")
        sys.exit(1)

    # Verify schema version
    import sqlite3
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT version FROM schema_version")
        version = cursor.fetchone()[0]
        conn.close()

        if version < 3:
            logger.warning(f"Database schema version {version} detected")
            logger.warning("Epic 5 requires schema version 3+")
            logger.warning("Please run migrations/003_add_api_indexes.sql")
    except Exception as e:
        logger.warning(f"Could not verify schema version: {e}")

    # Get port from environment or default
    port = int(os.getenv("WEB_PORT", "8000"))
    host = "127.0.0.1"  # Localhost only for security

    # Check for development mode
    dev_mode = os.getenv("DEV_MODE") == "1"
    reload = dev_mode or "--reload" in sys.argv

    logger.info(f"Starting web server at http://{host}:{port}")
    logger.info(f"Database: {db_path}")
    logger.info(f"Development mode: {dev_mode}")
    logger.info(f"API documentation: http://{host}:{port}/docs")
    logger.info("Press Ctrl+C to stop")

    # Start server
    try:
        uvicorn.run(
            "api.app:app",
            host=host,
            port=port,
            reload=reload,
            log_config=None  # Use our logging config
        )
    except KeyboardInterrupt:
        logger.info("Web server stopped")
    except Exception as e:
        logger.error(f"Web server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
