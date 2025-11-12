# Tests for health check endpoint

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from api.app import create_app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    app = create_app()
    return TestClient(app)


class TestHealthCheck:
    """Test health check endpoint functionality."""

    def test_health_check_success(self, client):
        """Test health check returns 200 when database is accessible."""
        # Health check should return 200 OK with healthy status
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "ok"
        assert data["uptime_seconds"] >= 0
        assert "version" in data
        assert "timestamp" in data

    def test_health_check_response_time(self, client):
        """Test health check responds in <50ms."""
        import time

        start = time.time()
        response = client.get("/api/health")
        duration = (time.time() - start) * 1000  # Convert to ms

        assert response.status_code == 200
        assert duration < 50, f"Health check took {duration}ms (target: <50ms)"

    def test_health_check_json_structure(self, client):
        """Test health check returns correct JSON structure."""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()

        # Check required fields exist
        required_fields = ["status", "database", "uptime_seconds", "version", "timestamp"]
        for field in required_fields:
            assert field in data

        # Check data types
        assert isinstance(data["status"], str)
        assert isinstance(data["database"], str)
        assert isinstance(data["uptime_seconds"], int)
        assert isinstance(data["version"], str)

    def test_health_check_openapi_docs_accessible(self, client):
        """Test OpenAPI documentation is accessible."""
        response = client.get("/docs")

        # Should return HTML page (not 404)
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "redoc" in response.text.lower()

    def test_health_check_redoc_docs_accessible(self, client):
        """Test ReDoc documentation is accessible."""
        response = client.get("/redoc")

        # Should return HTML page (not 404)
        assert response.status_code == 200
        assert "redoc" in response.text.lower()