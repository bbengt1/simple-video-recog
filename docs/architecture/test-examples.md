# Test Examples

## Frontend Component Test (Phase 2)

```javascript
// tests/frontend/unit/test_event_card.test.js
import { describe, it, expect, vi } from 'vitest';
import { EventCard } from '../../../web/components/EventCard.js';

describe('EventCard Component', () => {
  const mockEvent = {
    event_id: 'evt_12345',
    timestamp: '2025-11-08T14:32:15Z',
    camera_id: 'front_door',
    motion_confidence: 0.87,
    detected_objects: [
      { label: 'person', confidence: 0.92, bbox: { x: 120, y: 50, width: 180, height: 320 } }
    ],
    llm_description: 'Person approaching front door',
    image_path: 'data/events/2025-11-08/evt_12345.jpg'
  };

  it('should render event card with correct content', () => {
    const onClick = vi.fn();
    const card = EventCard(mockEvent, onClick);

    expect(card.className).toBe('event-card');
    expect(card.textContent).toContain('Person approaching front door');
    expect(card.textContent).toContain('person (92%)');
  });

  it('should call onClick handler when clicked', () => {
    const onClick = vi.fn();
    const card = EventCard(mockEvent, onClick);

    card.click();

    expect(onClick).toHaveBeenCalledWith('evt_12345');
  });

  it('should render multiple detected objects', () => {
    const eventWithMultipleObjects = {
      ...mockEvent,
      detected_objects: [
        { label: 'person', confidence: 0.92, bbox: {} },
        { label: 'package', confidence: 0.87, bbox: {} }
      ]
    };

    const card = EventCard(eventWithMultipleObjects, vi.fn());

    expect(card.textContent).toContain('person (92%)');
    expect(card.textContent).toContain('package (87%)');
  });

  it('should lazy load images', () => {
    const card = EventCard(mockEvent, vi.fn());
    const img = card.querySelector('img');

    expect(img.getAttribute('loading')).toBe('lazy');
    expect(img.getAttribute('src')).toContain('/api/v1/events/evt_12345/image');
  });
});
```

---

## Backend API Test

```python
# tests/integration/test_api_integration.py
"""Integration tests for FastAPI endpoints (Phase 2)."""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from api.server import app
from core.database import DatabaseManager
from core.models import Event, DetectedObject, BoundingBox


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def db_with_events(tmp_path):
    """Create test database with sample events."""
    db_path = tmp_path / "test_events.db"
    db = DatabaseManager(str(db_path))
    db.init_database()

    # Insert test events
    for i in range(5):
        event = Event(
            event_id=f"evt_test_{i}",
            timestamp=datetime.utcnow() - timedelta(hours=i),
            camera_id="test_camera",
            motion_confidence=0.8 + (i * 0.01),
            detected_objects=[
                DetectedObject(
                    label="person",
                    confidence=0.9,
                    bbox=BoundingBox(x=100, y=50, width=200, height=350)
                )
            ],
            llm_description=f"Test event {i}",
            image_path=f"data/test/evt_test_{i}.jpg",
            json_log_path="data/test/events.json"
        )
        db.insert_event(event)

    return db


def test_health_check(client):
    """Test health check endpoint returns 200."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data


def test_list_events_default(client, db_with_events):
    """Test listing events with default parameters."""
    response = client.get("/api/v1/events")

    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert "total" in data
    assert len(data["events"]) == 5
    assert data["total"] == 5


def test_list_events_with_limit(client, db_with_events):
    """Test pagination with limit parameter."""
    response = client.get("/api/v1/events?limit=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data["events"]) == 2
    assert data["limit"] == 2


def test_list_events_with_time_range(client, db_with_events):
    """Test filtering events by time range."""
    start = (datetime.utcnow() - timedelta(hours=3)).isoformat()
    end = (datetime.utcnow() - timedelta(hours=1)).isoformat()

    response = client.get(f"/api/v1/events?start={start}&end={end}")

    assert response.status_code == 200
    data = response.json()
    assert len(data["events"]) >= 1  # At least one event in range


def test_get_event_by_id(client, db_with_events):
    """Test retrieving single event by ID."""
    response = client.get("/api/v1/events/evt_test_0")

    assert response.status_code == 200
    event = response.json()
    assert event["event_id"] == "evt_test_0"
    assert event["llm_description"] == "Test event 0"
    assert len(event["detected_objects"]) == 1


def test_get_event_by_id_not_found(client, db_with_events):
    """Test 404 error for non-existent event."""
    response = client.get("/api/v1/events/evt_nonexistent")

    assert response.status_code == 404
    error = response.json()
    assert "detail" in error
    assert error["detail"] == "Event not found"


def test_get_metrics(client):
    """Test metrics endpoint returns valid data."""
    response = client.get("/api/v1/metrics")

    assert response.status_code == 200
    metrics = response.json()
    assert "frames_processed" in metrics
    assert "events_created" in metrics
    assert "coreml_inference_avg" in metrics


def test_cors_headers(client):
    """Test CORS headers are set correctly."""
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:3000"}
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
```

---

## E2E Test (Phase 3)

```javascript
// tests/e2e/test_dashboard_workflow.spec.js
import { test, expect } from '@playwright/test';

test.describe('Dashboard Workflow', () => {
  test('should display recent events on dashboard', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Wait for events to load
    await page.waitForSelector('.event-card');

    // Check that events are displayed
    const eventCards = await page.locator('.event-card').count();
    expect(eventCards).toBeGreaterThan(0);

    // Verify event card contains expected elements
    const firstCard = page.locator('.event-card').first();
    await expect(firstCard.locator('.event-card__description')).toBeVisible();
    await expect(firstCard.locator('.event-card__image img')).toBeVisible();
  });

  test('should filter events by date range', async ({ page }) => {
    await page.goto('http://localhost:3000/#/events');

    // Open filter bar
    await page.click('#filter-toggle');

    // Set date range
    await page.fill('#filter-start', '2025-11-01');
    await page.fill('#filter-end', '2025-11-08');
    await page.click('button[type="submit"]');

    // Wait for filtered results
    await page.waitForSelector('.event-card');

    // Verify results are within date range
    const firstEventTime = await page.locator('.event-card__time').first().textContent();
    expect(firstEventTime).toContain('Nov');
  });

  test('should navigate to event detail', async ({ page }) => {
    await page.goto('http://localhost:3000/#/events');

    // Click on first event card
    await page.click('.event-card:first-child');

    // Wait for detail view
    await page.waitForURL(/.*#\/event\/.*/);

    // Verify detail view elements
    await expect(page.locator('.event-detail__image')).toBeVisible();
    await expect(page.locator('.event-detail__description')).toBeVisible();
    await expect(page.locator('.event-detail__metadata')).toBeVisible();
  });

  test('should receive real-time event updates via WebSocket', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Wait for WebSocket connection
    await page.waitForTimeout(1000);

    // Simulate new event (would require triggering actual event in test environment)
    // This is a placeholder - actual implementation would need test event generator

    // Verify notification appears
    // await expect(page.locator('.notification')).toBeVisible();
    // await expect(page.locator('.notification')).toContainText('New event');
  });
});
```

---
