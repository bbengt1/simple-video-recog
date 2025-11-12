# Tests for web server entry point

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestWebServer:
    """Test web server entry point functionality."""

    @patch('web_server.uvicorn')
    @patch('logging.getLogger')
    def test_main_starts_server(self, mock_get_logger, mock_uvicorn):
        """Test main function starts the server."""
        from web_server import main

        # Mock logger
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        # Mock config loading
        with patch('web_server.load_config') as mock_load_config:
            mock_config = MagicMock()
            mock_config.db_path = "data/events.db"
            mock_config.log_level = "INFO"
            mock_load_config.return_value = mock_config

            # Mock database check
            with patch('pathlib.Path.exists', return_value=True):
                with patch('sqlite3.connect') as mock_connect:
                    # Call main and expect it to call uvicorn.run
                    main()

                    # Verify uvicorn run was called with correct parameters
                    mock_uvicorn.run.assert_called_once_with(
                        "api.app:app",
                        host="127.0.0.1",
                        port=8000,
                        reload=False,
                        log_config=None
                    )

    @patch('web_server.uvicorn')
    @patch('api.app.create_app')
    @patch('logging.getLogger')
    def test_main_custom_port(self, mock_get_logger, mock_create_app, mock_uvicorn):
        """Test main function with custom port environment variable."""
        from web_server import main
        import os

        # Set custom port
        os.environ['WEB_PORT'] = '9000'

        try:
            # Mock the dependencies
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            mock_app = MagicMock()
            mock_create_app.return_value = mock_app

            # Call main
            main()

            # Verify uvicorn run was called with custom port
            mock_uvicorn.run.assert_called_once_with(
                "api.app:app",
                host="127.0.0.1",
                port=9000,
                reload=False,
                log_config=None
            )

            # Verify logging
            mock_logger.info.assert_any_call("Starting web server at http://127.0.0.1:9000")

        finally:
            # Clean up environment
            del os.environ['WEB_PORT']

    @patch('web_server.uvicorn')
    @patch('api.app.create_app')
    @patch('logging.getLogger')
    def test_main_database_validation_failure(self, mock_get_logger, mock_create_app, mock_uvicorn):
        """Test main function handles database validation failure."""
        from web_server import main

        # Mock Path to make database not exist
        with patch('web_server.Path') as mock_path:
            mock_db_path = MagicMock()
            mock_db_path.exists.return_value = False
            mock_path.return_value = mock_db_path

            # Mock logger
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Call main and expect it to exit
            with pytest.raises(SystemExit):
                main()

            # Verify error was logged
            mock_logger.error.assert_called_with("Please run the main application first to create the database")

    @patch('web_server.uvicorn')
    @patch('api.app.create_app')
    @patch('logging.getLogger')
    def test_main_keyboard_interrupt(self, mock_get_logger, mock_create_app, mock_uvicorn):
        """Test main function handles keyboard interrupt gracefully."""
        from web_server import main

        # Mock uvicorn.run to raise KeyboardInterrupt
        mock_uvicorn.run.side_effect = KeyboardInterrupt()

        # Mock the dependencies
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_app = MagicMock()
        mock_create_app.return_value = mock_app

        # Call main
        main()

        # Verify graceful shutdown was logged
        mock_logger.info.assert_any_call("Web server stopped")

    @patch('web_server.uvicorn')
    @patch('api.app.create_app')
    @patch('logging.getLogger')
    def test_main_unexpected_error(self, mock_get_logger, mock_create_app, mock_uvicorn):
        """Test main function handles unexpected errors."""
        from web_server import main

        # Mock uvicorn.run to raise unexpected error
        mock_uvicorn.run.side_effect = RuntimeError("Unexpected error")

        # Mock the dependencies
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_app = MagicMock()
        mock_create_app.return_value = mock_app

        # Call main and expect it to exit
        with pytest.raises(SystemExit):
            main()

        # Verify error was logged
        mock_logger.error.assert_called_with("Web server error: Unexpected error")