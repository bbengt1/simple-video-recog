# WebSocket Endpoint (Phase 2)

**Endpoint:** `ws://localhost:8000/ws/events`

**Purpose:** Real-time event streaming to web dashboard clients

**Message Format:**
```json
{
  "type": "event",
  "data": {
    "event_id": "evt_1699459335_a7b3c",
    "timestamp": "2025-11-08T14:32:15Z",
    "camera_id": "front_door",
    "motion_confidence": 0.87,
    "detected_objects": [
      {
        "label": "person",
        "confidence": 0.92,
        "bbox": {"x": 120, "y": 50, "width": 180, "height": 320}
      }
    ],
    "llm_description": "Person in blue shirt carrying brown package approaching front door",
    "image_path": "data/events/2025-11-08/evt_1699459335_a7b3c.jpg"
  }
}
```

**Connection Lifecycle:**
1. Client opens WebSocket connection to `/ws/events`
2. Server accepts connection and adds to subscriber list
3. When new event is created, server broadcasts to all connected clients
4. Client closes connection when navigating away
5. Server removes client from subscriber list

**Error Handling:**
- Connection failures: Client implements exponential backoff reconnection (1s, 2s, 4s, 8s max)
- Server errors: Server sends error message with `{"type": "error", "message": "..."}`
- Missed events: No message replay - clients should query REST API for historical data

---
