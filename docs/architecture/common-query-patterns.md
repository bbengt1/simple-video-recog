# Common Query Patterns

**Get recent events (dashboard):**
```sql
SELECT * FROM events
ORDER BY timestamp DESC
LIMIT 100;
```
Performance: <50ms with 10,000 events (uses idx_events_timestamp)

**Get events in time range (timeline view):**
```sql
SELECT * FROM events
WHERE timestamp BETWEEN '2025-11-08 00:00:00' AND '2025-11-08 23:59:59'
ORDER BY timestamp DESC;
```
Performance: <100ms with 10,000 events (uses idx_events_timestamp)

**Get events by camera (multi-camera):**
```sql
SELECT * FROM events
WHERE camera_id = 'front_door'
ORDER BY timestamp DESC
LIMIT 100;
```
Performance: <50ms with 10,000 events (uses idx_events_camera + idx_events_timestamp)

**Search events by object (future enhancement):**
```sql
SELECT * FROM events
WHERE detected_objects LIKE '%"label": "person"%'
ORDER BY timestamp DESC;
```
Performance: Slow (full table scan) - consider adding FTS5 virtual table in Phase 3

---
