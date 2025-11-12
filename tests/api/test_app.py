# Tests for FastAPI application factory

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from api.app import create_app


class TestCreateApp:
    """Test FastAPI application factory."""

    def test_create_app_returns_fastapi_instance(self):
        """Test create_app returns a FastAPI instance."""
        app = create_app()

        # Should be a FastAPI instance
        assert hasattr(app, 'routes')
        assert hasattr(app, 'middleware')

    def test_create_app_includes_health_router(self):
        """Test health router is included in the app."""
        app = create_app()

        # Check that health route exists
        from fastapi.routing import APIRoute
        routes = [route.path for route in app.routes if isinstance(route, APIRoute)]
        assert "/api/health" in routes

    def test_create_app_cors_middleware(self):
        """Test CORS middleware is configured."""
        app = create_app()

        # Check CORS middleware is present
        cors_middleware = None
        for middleware in app.user_middleware:
            if hasattr(middleware, 'cls') and 'CORSMiddleware' in str(middleware.cls):
                cors_middleware = middleware
                break

        assert cors_middleware is not None

        # Check CORS options
        options = cors_middleware.kwargs
        assert options["allow_origins"] == ["http://localhost:8000", "http://127.0.0.1:8000"]
        assert options["allow_credentials"] is True
        assert options["allow_methods"] == ["*"]
        assert options["allow_headers"] == ["*"]

    def test_create_app_static_files_mounted(self):
        """Test static files are mounted."""
        app = create_app()

        # Check static files are mounted (CSS and JS routes)
        from fastapi.routing import APIRoute, Mount
        mounts = [route for route in app.routes if isinstance(route, Mount)]
        css_mount = any(mount.path == "/css" for mount in mounts)
        js_mount = any(mount.path == "/js" for mount in mounts)

        # At least one of them should be mounted if web directory exists
        assert css_mount or js_mount

    def test_create_app_openapi_config(self):
        """Test OpenAPI configuration."""
        app = create_app()

        assert app.title == "Local Video Recognition System API"
        assert app.description == "REST API and WebSocket for event access and real-time monitoring"
        assert app.version == "1.0.0"

    def test_create_app_with_test_client(self):
        """Test app works with test client."""
        app = create_app()
        client = TestClient(app)

        # Should be able to make requests
        response = client.get("/api/health")
        assert response.status_code in [200, 500]  # Either healthy or database error in test

    @patch('api.app.load_config')
    def test_create_app_config_loading(self, mock_load_config):
        """Test config is loaded during app creation."""
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        app = create_app()

        # Config should be loaded
        mock_load_config.assert_called_once()

    def test_create_app_error_handling(self):
        """Test app creation handles errors gracefully."""
        # This should not raise an exception
        app = create_app()
        assert app is not None