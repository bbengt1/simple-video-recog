# Events Table (SQLite)

```sql
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    timestamp DATETIME NOT NULL,
    camera_id TEXT NOT NULL,
    motion_confidence REAL,
    detected_objects TEXT,  -- JSON array: [{"label": "person", "confidence": 0.92, "bbox": {...}}, ...]
    llm_description TEXT,
    image_path TEXT,
    json_log_path TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_camera ON events(camera_id);
CREATE INDEX IF NOT EXISTS idx_events_event_id ON events(event_id);
```

**Field Details:**
- `id`: Auto-incrementing primary key (SQLite ROWID alias)
- `event_id`: Unique identifier for application use (e.g., `evt_1699459335_a7b3c`)
- `timestamp`: Event occurrence time (stored as ISO 8601 string in UTC)
- `camera_id`: Camera identifier (enables future multi-camera queries)
- `motion_confidence`: Motion detection score (0.0-1.0), NULL if not applicable
- `detected_objects`: JSON TEXT field storing array of DetectedObject instances
- `llm_description`: Natural language description from Ollama LLM
- `image_path`: Relative path to annotated image (e.g., `data/events/2025-11-08/evt_12345.jpg`)
- `json_log_path`: Relative path to JSON log file containing this event
- `created_at`: Database insertion timestamp (auto-generated)

**Indexes:**
- `idx_events_timestamp`: Descending order for efficient recent event queries
- `idx_events_camera`: Filter events by camera (Phase 2/3 multi-camera)
- `idx_events_event_id`: Unique lookup by event_id

---
