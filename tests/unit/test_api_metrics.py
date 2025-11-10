"""Unit tests for the metrics and configuration API endpoints.

Tests cover:
- Metrics endpoint functionality
- Configuration endpoint functionality
- MetricsCollector integration
- Response validation
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from api.app import create_app
from api.models import MetricsResponse, ConfigResponse
from core.metrics import MetricsSnapshot


class TestMetricsRoutes:
    """Test that metrics routes are properly registered."""

    def test_metrics_routes_registered(self):
        """Test that metrics routes are registered in the app."""
        from fastapi.routing import APIRoute

        app = create_app()

        routes = [str(route.path) for route in app.routes if isinstance(route, APIRoute)]
        assert '/api/metrics' in routes
        assert '/api/config' in routes


class TestMetricsModels:
    """Test Pydantic models for metrics and config."""

    def test_metrics_response_model(self):
        """Test MetricsResponse model validation."""
        test_timestamp = datetime(2025, 11, 8, 14, 32, 0)

        metrics_data = {
            "timestamp": test_timestamp,
            "frames_processed": 15234,
            "motion_detected": 1205,
            "motion_hit_rate": 0.079,
            "events_created": 342,
            "events_suppressed": 98,
            "coreml_inference_avg": 45.3,
            "coreml_inference_min": 32.1,
            "coreml_inference_max": 98.7,
            "coreml_inference_p95": 67.2,
            "llm_inference_avg": 1234.5,
            "llm_inference_min": 987.2,
            "llm_inference_max": 2456.8,
            "llm_inference_p95": 1876.4,
            "frame_processing_latency_avg": 1456.7,
            "cpu_usage_current": 42.3,
            "cpu_usage_avg": 38.7,
            "memory_usage_mb": 2048.0,
            "memory_usage_gb": 2.0,
            "memory_usage_percent": 12.5,
            "system_uptime_percent": 99.8,
            "version": "1.0.0"
        }

        response = MetricsResponse(**metrics_data)
        assert response.frames_processed == 15234
        assert response.version == "1.0.0"
        assert response.memory_usage_mb == 2048.0

    def test_config_response_model(self):
        """Test ConfigResponse model validation."""
        config_data = {
            "camera_id": "front_door",
            "motion_threshold": 0.5,
            "frame_sample_rate": 5,
            "blacklist_objects": ["bird", "cat"],
            "min_object_confidence": 0.5,
            "ollama_model": "llava:7b",
            "max_storage_gb": 4.0,
            "min_retention_days": 7,
            "log_level": "INFO",
            "metrics_interval": 60,
            "version": "1.0.0"
        }

        response = ConfigResponse(**config_data)
        assert response.camera_id == "front_door"
        assert response.motion_threshold == 0.5
        assert response.blacklist_objects == ["bird", "cat"]


class TestMetricsCollectorIntegration:
    """Test integration with MetricsCollector."""

    def test_get_metrics_collector_singleton(self):
        """Test that get_metrics_collector returns a singleton."""
        from core.metrics import get_metrics_collector

        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        assert collector1 is collector2
        assert collector1 is not None

    def test_metrics_collector_initialization(self):
        """Test MetricsCollector can be created."""
        from core.metrics import MetricsCollector

        # Create collector with mock config
        mock_config = Mock()
        mock_config.metrics_interval = 60

        collector = MetricsCollector(mock_config)
        assert isinstance(collector, MetricsCollector)

    def test_metrics_snapshot_creation(self):
        """Test that MetricsCollector can create snapshots."""
        from core.metrics import MetricsCollector, MetricsSnapshot

        # Create collector with mock config
        mock_config = Mock()
        mock_config.metrics_interval = 60

        collector = MetricsCollector(mock_config)
        snapshot = collector.collect()

        assert isinstance(snapshot, MetricsSnapshot)
        assert snapshot.version is not None
        assert isinstance(snapshot.frames_processed, int)