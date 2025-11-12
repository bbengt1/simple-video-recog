# API tests for metrics and configuration endpoints

import pytest
from fastapi.testclient import TestClient

from api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_get_metrics_success(client):
    """Test metrics endpoint returns 200."""
    response = client.get("/api/metrics")

    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    assert "frames_processed" in data
    assert "events_created" in data
    assert "coreml_inference_avg" in data
    assert isinstance(data["frames_processed"], int)
    assert isinstance(data["events_created"], int)


def test_get_metrics_response_format(client):
    """Test metrics response format matches MetricsResponse model."""
    response = client.get("/api/metrics")

    assert response.status_code == 200
    data = response.json()

    # Check all required fields are present
    required_fields = [
        "timestamp", "frames_processed", "motion_detected", "motion_hit_rate",
        "events_created", "events_suppressed", "coreml_inference_avg",
        "coreml_inference_min", "coreml_inference_max", "coreml_inference_p95",
        "llm_inference_avg", "llm_inference_min", "llm_inference_max", "llm_inference_p95",
        "frame_processing_latency_avg", "cpu_usage_current", "cpu_usage_avg",
        "memory_usage_mb", "memory_usage_gb", "memory_usage_percent",
        "system_uptime_percent", "version"
    ]

    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


def test_get_config_success(client):
    """Test config endpoint returns 200."""
    response = client.get("/api/config")

    assert response.status_code == 200
    data = response.json()
    assert "camera_id" in data
    assert "motion_threshold" in data
    assert "version" in data


def test_get_config_response_format(client):
    """Test config response format matches ConfigResponse model."""
    response = client.get("/api/config")

    assert response.status_code == 200
    data = response.json()

    # Check required fields
    required_fields = [
        "camera_id", "motion_threshold", "frame_sample_rate",
        "blacklist_objects", "min_object_confidence", "ollama_model",
        "max_storage_gb", "min_retention_days", "log_level",
        "metrics_interval", "version"
    ]

    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Check field types
    assert isinstance(data["camera_id"], str)
    assert isinstance(data["motion_threshold"], float)
    assert isinstance(data["blacklist_objects"], list)


def test_get_config_no_sensitive_data(client):
    """Test config endpoint excludes sensitive fields."""
    response = client.get("/api/config")

    assert response.status_code == 200
    data = response.json()

    # These sensitive fields should NOT be present
    sensitive_fields = ["camera_rtsp_url", "rtsp_username", "rtsp_password"]
    for field in sensitive_fields:
        assert field not in data, f"Sensitive field exposed: {field}"


def test_dashboard_metrics_success(client):
    """Test dashboard metrics endpoint returns 200."""
    response = client.get("/api/dashboard/metrics")

    assert response.status_code == 200
    data = response.json()
    assert "system" in data
    assert "events" in data
    assert "cameras" in data


def test_dashboard_metrics_response_format(client):
    """Test dashboard metrics response format."""
    response = client.get("/api/dashboard/metrics")

    assert response.status_code == 200
    data = response.json()

    # Check system metrics
    system = data["system"]
    required_system_fields = [
        "cpu_usage_percent", "memory_used", "memory_total",
        "disk_used", "disk_total", "disk_usage_percent",
        "system_uptime_seconds", "app_uptime_seconds"
    ]
    for field in required_system_fields:
        assert field in system

    # Check events statistics
    events = data["events"]
    required_event_fields = [
        "total_events", "events_today", "events_this_hour",
        "events_per_hour_avg", "events_per_hour_previous"
    ]
    for field in required_event_fields:
        assert field in events

    # Check cameras array
    assert isinstance(data["cameras"], list)


def test_metrics_endpoints_no_auth_required(client):
    """Test that metrics endpoints don't require authentication."""
    # These should work without any auth headers
    endpoints = ["/api/metrics", "/api/config", "/api/dashboard/metrics"]

    for endpoint in endpoints:
        response = client.get(endpoint)
        # Should not return 401 Unauthorized
        assert response.status_code != 401