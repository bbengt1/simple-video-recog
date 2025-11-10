-- Migration 001: Initial schema for video recognition events
-- Creates events table, indexes, and schema version tracking

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    timestamp DATETIME NOT NULL,
    camera_id TEXT NOT NULL,  -- Future: FOREIGN KEY REFERENCES cameras(id)
    motion_confidence REAL,
    detected_objects TEXT,  -- JSON array of detected objects
    llm_description TEXT,
    image_path TEXT,
    json_log_path TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_camera ON events(camera_id);  -- Supports multi-camera queries
CREATE INDEX IF NOT EXISTS idx_events_event_id ON events(event_id);

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO schema_version (version) VALUES (1);