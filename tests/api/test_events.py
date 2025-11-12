# API tests for event endpoints

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_list_events_success(client):
    """Test event list returns 200 with valid pagination."""
    response = client.get("/api/events?limit=10&offset=0")

    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert isinstance(data["events"], list)


def test_list_events_time_range(client):
    """Test event list with time range filtering."""
    start = (datetime.now() - timedelta(days=1)).isoformat()
    end = datetime.now().isoformat()

    response = client.get(f"/api/events?start={start}&end={end}")

    assert response.status_code == 200
    data = response.json()
    # Should not fail, even if no events in range
    assert isinstance(data["events"], list)


def test_list_events_camera_filter(client):
    """Test event list with camera ID filtering."""
    response = client.get("/api/events?camera_id=test_camera")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["events"], list)


def test_list_events_pagination(client):
    """Test pagination works correctly."""
    # Get first page
    page1 = client.get("/api/events?limit=5&offset=0").json()
    # Get second page
    page2 = client.get("/api/events?limit=5&offset=5").json()

    assert page1["limit"] == 5
    assert page1["offset"] == 0
    assert page2["limit"] == 5
    assert page2["offset"] == 5


def test_list_events_invalid_limit(client):
    """Test invalid limit parameter returns 422."""
    response = client.get("/api/events?limit=2000")  # Max is 1000
    assert response.status_code == 422


def test_list_events_invalid_offset(client):
    """Test invalid offset parameter returns 422."""
    response = client.get("/api/events?offset=-1")
    assert response.status_code == 422


def test_get_event_success(client):
    """Test getting single event returns 200."""
    # First get an event ID from list
    events_response = client.get("/api/events?limit=1")
    if events_response.status_code == 200:
        events_data = events_response.json()
        if len(events_data["events"]) > 0:
            event_id = events_data["events"][0]["event_id"]

            response = client.get(f"/api/events/{event_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["event_id"] == event_id
            assert "detected_objects" in data
            assert "llm_description" in data
        else:
            # No events in database, skip test
            pytest.skip("No events in database")
    else:
        pytest.skip("Cannot get events list")


def test_get_event_not_found(client):
    """Test getting non-existent event returns 404."""
    response = client.get("/api/events/non_existent_event_id")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"]["code"] == "EVENT_NOT_FOUND"


def test_get_event_image_not_found(client):
    """Test getting image for non-existent event returns 404."""
    response = client.get("/api/events/non_existent_event_id/image")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"]["code"] == "EVENT_NOT_FOUND"


def test_list_events_response_format(client):
    """Test event list response format matches EventListResponse model."""
    response = client.get("/api/events?limit=1")

    assert response.status_code == 200
    data = response.json()

    # Check required fields
    required_fields = ["events", "total", "limit", "offset"]
    for field in required_fields:
        assert field in data

    # Check events array
    assert isinstance(data["events"], list)
    if len(data["events"]) > 0:
        event = data["events"][0]
        required_event_fields = ["event_id", "timestamp", "camera_id", "detected_objects", "llm_description", "image_path", "created_at"]
        for field in required_event_fields:
            assert field in event


def test_get_event_response_format(client):
    """Test single event response format matches Event model."""
    # Get first event from list
    events_response = client.get("/api/events?limit=1")
    if events_response.status_code == 200:
        events_data = events_response.json()
        if len(events_data["events"]) > 0:
            event_id = events_data["events"][0]["event_id"]

            response = client.get(f"/api/events/{event_id}")
            assert response.status_code == 200
            data = response.json()

            # Check required fields
            required_fields = ["event_id", "timestamp", "camera_id", "detected_objects", "llm_description", "image_path", "created_at"]
            for field in required_fields:
                assert field in data

            # Check detected_objects is array
            assert isinstance(data["detected_objects"], list)
        else:
            pytest.skip("No events in database")
    else:
        pytest.skip("Cannot get events list")