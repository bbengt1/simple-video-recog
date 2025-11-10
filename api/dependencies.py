# API dependencies for FastAPI application

import logging
import sqlite3
from pathlib import Path

from core.config import load_config

logger = logging.getLogger(__name__)

# Module-level configuration and connection
_config = None
_db_conn = None

def get_config():
    """Get or load system configuration."""
    global _config
    if _config is None:
        _config = load_config("config/config.yaml")
    return _config

def get_db_connection():
    """
    Get read-only database connection.

    Connection is created once and reused across requests.
    Read-only mode prevents write contention with main application.
    """
    global _db_conn

    if _db_conn is None:
        config = get_config()
        db_path = Path(config.db_path)

        # Open in read-only mode
        try:
            _db_conn = sqlite3.connect(
                f"file:{db_path}?mode=ro",
                uri=True,
                check_same_thread=False  # Allow sharing across threads
            )
            _db_conn.row_factory = sqlite3.Row  # Access columns by name
            logger.info(f"Database connection established (read-only): {db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    return _db_conn

def close_db_connection():
    """Close database connection on shutdown."""
    global _db_conn
    if _db_conn is not None:
        _db_conn.close()
        _db_conn = None
        logger.info("Database connection closed")
