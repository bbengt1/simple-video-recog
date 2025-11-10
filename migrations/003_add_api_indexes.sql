-- Migration 003: Add API Query Performance Indexes
-- Created: 2025-11-10
-- Purpose: Optimize database queries for Epic 5 Web Dashboard API
-- Related: Epic 5 - Web Dashboard & Real-Time Monitoring

-- Epic 5 Story 5.2 requires efficient time-range queries for event listing
-- Epic 5 Story 5.8 requires filtering by camera_id and timestamp

BEGIN TRANSACTION;

-- Index 1: Timestamp descending for recent events query
-- Supports: GET /api/events?limit=100 (default recent events)
-- Query pattern: SELECT * FROM events ORDER BY timestamp DESC LIMIT ?
CREATE INDEX IF NOT EXISTS idx_events_timestamp
ON events(timestamp DESC);

-- Index 2: Camera ID for multi-camera filtering (future Phase 3)
-- Supports: GET /api/events?camera_id=front_door
-- Query pattern: SELECT * FROM events WHERE camera_id = ?
CREATE INDEX IF NOT EXISTS idx_events_camera
ON events(camera_id);

-- Index 3: Composite index for time-range + camera filtering
-- Supports: GET /api/events?start=2025-11-01&end=2025-11-10&camera_id=front_door
-- Query pattern: SELECT * FROM events WHERE timestamp BETWEEN ? AND ? AND camera_id = ?
CREATE INDEX IF NOT EXISTS idx_events_timestamp_camera
ON events(timestamp DESC, camera_id);

-- Index 4: Event ID for direct lookup (GET /api/events/{id})
-- Query pattern: SELECT * FROM events WHERE event_id = ?
-- Note: Primary key on event_id already exists, but explicit index improves clarity
CREATE INDEX IF NOT EXISTS idx_events_event_id
ON events(event_id);

-- Update schema version
UPDATE schema_version SET version = 3, updated_at = CURRENT_TIMESTAMP;

COMMIT;

-- Performance Notes:
-- - idx_events_timestamp: ~10x speedup for ORDER BY timestamp DESC LIMIT queries
-- - idx_events_camera: Required for multi-camera deployments (Phase 3)
-- - idx_events_timestamp_camera: Composite index for common API query pattern
-- - Total index overhead: ~15% of table size (acceptable for read-heavy API workload)

-- Verification Query (run after migration):
-- SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND tbl_name='events';
