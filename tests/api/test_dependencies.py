# Tests for API dependencies

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from api.dependencies import get_config, get_db_connection, close_db_connection


class TestConfigDependency:
    """Test configuration dependency loading."""

    @patch('api.dependencies.load_config')
    def test_get_config_loads_once(self, mock_load_config):
        """Test that config is loaded only once and cached."""
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        # First call should load config
        config1 = get_config()
        assert config1 == mock_config
        mock_load_config.assert_called_once_with("config/config.yaml")

        # Second call should return cached config
        config2 = get_config()
        assert config2 == mock_config
        # Should still be called only once
        mock_load_config.assert_called_once()


class TestDatabaseDependency:
    """Test database dependency functions."""

    def setup_method(self):
        """Reset global state before each test."""
        import api.dependencies
        api.dependencies._config = None
        api.dependencies._db_conn = None

    @patch('api.dependencies.get_config')
    @patch('api.dependencies.sqlite3.connect')
    def test_get_db_connection_read_only(self, mock_connect, mock_get_config):
        """Test database connection is read-only."""
        # Setup mocks
        mock_config = MagicMock()
        mock_config.db_path = "data/events.db"
        mock_get_config.return_value = mock_config

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Call function
        conn = get_db_connection()

        # Verify connection was made with read-only URI
        mock_connect.assert_called_once_with(
            "file:data/events.db?mode=ro",
            uri=True,
            check_same_thread=False
        )
        assert conn == mock_conn

    @patch('api.dependencies.get_config')
    @patch('api.dependencies.sqlite3.connect')
    def test_get_db_connection_cached(self, mock_connect, mock_get_config):
        """Test database connection is cached and reused."""
        # Setup mocks
        mock_config = MagicMock()
        mock_config.db_path = "data/events.db"
        mock_get_config.return_value = mock_config

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # First call
        conn1 = get_db_connection()
        assert conn1 is mock_conn

        # Second call should return cached connection
        conn2 = get_db_connection()
        assert conn2 is mock_conn

        # sqlite3.connect should only be called once
        mock_connect.assert_called_once()

    @patch('api.dependencies.sqlite3.connect')
    def test_close_db_connection(self, mock_connect):
        """Test database connection can be closed."""
        # Set up a mock connection in the global variable
        mock_conn = MagicMock()
        import api.dependencies
        api.dependencies._db_conn = mock_conn

        # Close connection
        close_db_connection()

        # Verify connection was closed
        mock_conn.close.assert_called_once()
        # Verify global variable was reset
        assert api.dependencies._db_conn is None

    def test_close_db_connection_no_connection(self):
        """Test closing connection when none exists."""
        from api.dependencies import _db_conn

        # Ensure no connection
        _db_conn = None

        # Should not raise error
        close_db_connection()

        # Should remain None
        assert _db_conn is None