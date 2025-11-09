# Epic 3: Event Persistence & Data Management

**Epic Goal:** Implement SQLite database for event storage, dual-format logging (JSON + plaintext), and storage management to enable event querying and long-term data retention within disk constraints, providing the foundation for Phase 2 web dashboard.

## Story 3.1: SQLite Database Setup and Schema Implementation

**As a** developer,
**I want** to initialize a SQLite database with a schema for event storage,
**so that** events can be persisted, queried, and analyzed over time.

**Acceptance Criteria:**

1. Database module (core/database.py) implements DatabaseManager class with init_database(db_path) method
2. db_path from configuration specifies SQLite file location (default: "data/events.db")
3. Database schema matches Technical Assumptions specification:
   ```sql
   CREATE TABLE IF NOT EXISTS events (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       event_id TEXT UNIQUE NOT NULL,
       timestamp DATETIME NOT NULL,
       camera_id TEXT NOT NULL,
       motion_confidence REAL,
       detected_objects TEXT,
       llm_description TEXT,
       image_path TEXT,
       json_log_path TEXT,
       created_at DATETIME DEFAULT CURRENT_TIMESTAMP
   );
   CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
   CREATE INDEX IF NOT EXISTS idx_events_camera ON events(camera_id);
   CREATE INDEX IF NOT EXISTS idx_events_event_id ON events(event_id);
   ```
4. detected_objects stored as JSON TEXT (serialize list[dict] to JSON string for SQLite storage)
5. Database created automatically if file doesn't exist (no manual setup required)
6. Database connection pooling: Single connection reused throughout application lifetime
7. init_database() verifies schema on startup: Creates tables if missing, validates existing schema
8. Schema version tracking and migration strategy:
   - Create schema_version table: `CREATE TABLE schema_version (version INTEGER PRIMARY KEY, applied_at DATETIME)`
   - Current schema version: 1 (MVP baseline)
   - Migration approach: Manual migration scripts in migrations/ directory (e.g., migrations/001_initial.sql, migrations/002_add_confidence.sql)
   - On startup, check schema_version table and apply any pending migrations in sequence
   - Each migration script wrapped in transaction for atomicity
   - Migration failure logs ERROR and exits (prevents running with incompatible schema)
   - Alternative: Document that schema changes require backup → delete → recreate for MVP (acceptable for Phase 1)
9. Transaction support: insert_event() wrapped in transaction for atomicity
10. Unit tests verify: database creation, schema validation, index creation, transaction handling, schema_version initialization
11. Integration test: Initialize database, insert 100 test events, verify all persisted correctly
12. Error handling: Database corruption or permission errors logged with clear message and graceful exit
13. Documentation: migrations/README.md documents migration process and includes backup script (sqlite3 .dump)

---

## Story 3.2: Event Persistence to SQLite Database

**As a** developer,
**I want** to persist Event objects to the SQLite database,
**so that** events are permanently stored and queryable for historical analysis.

**Acceptance Criteria:**

1. DatabaseManager.insert_event(event: Event) method persists Event object to database
2. Event fields mapped to database columns: event_id → event_id, timestamp → timestamp, etc.
3. detected_objects list serialized to JSON TEXT before storage
4. INSERT statement uses parameterized queries to prevent SQL injection
5. Duplicate event_id handling: UNIQUE constraint prevents duplicate inserts, log WARNING if duplicate detected
6. insert_event() returns success boolean: True if inserted, False if duplicate or error
7. Database write errors (disk full, permission denied) logged and raised as DatabaseWriteError
8. Performance: Insert completes in <10ms (measured and logged if exceeds threshold)
9. Batch insert support: insert_events(events: list[Event]) for efficient bulk operations
10. Unit tests verify: single event insert, duplicate handling, batch insert, error scenarios
11. Integration test: Insert 1000 events via pipeline, query database, verify all present with correct data
12. Foreign key support prepared for Phase 2 multi-camera (camera_id references cameras table in future)

---

## Story 3.3: Event Query and Retrieval API

**As a** developer,
**I want** to query events from the database with filtering,
**so that** I can retrieve historical events for analysis and future web dashboard integration.

**Acceptance Criteria:**

1. DatabaseManager implements query methods:
   - get_event_by_id(event_id) → Event | None
   - get_events_by_timerange(start, end) → list[Event]
   - get_recent_events(limit=100) → list[Event]
   - count_events() → int
2. Query results deserialized to Event objects (JSON TEXT → list[dict] for detected_objects)
3. Timerange queries use indexed timestamp column for performance
4. get_events_by_timerange() accepts datetime objects with timezone awareness
5. Query results ordered by timestamp DESC (newest first) by default
6. Pagination support: offset and limit parameters for large result sets
7. Filter by camera_id: get_events_by_camera(camera_id, limit) for Phase 2 multi-camera
8. Performance: Simple queries (<100 results) complete in <50ms on database with 10,000 events
9. Unit tests verify: query by ID, timerange filtering, pagination, ordering, deserialization
10. Integration test: Insert 1000 events, query various timeranges, verify results match expected

---

## Story 3.4: JSON Event Log File Generation

**As a** developer,
**I want** to write event data to structured JSON log files,
**so that** events can be programmatically processed by external tools without database access.

**Acceptance Criteria:**

1. JSON logger module (core/json_logger.py) implements JSONEventLogger class with log_event(event) method
2. JSON files organized by date: data/events/YYYY-MM-DD/events.json (one file per day)
3. Each event appended as single JSON object on new line (JSON Lines format, not array)
4. Event serialization uses Event.to_json() method from Story 2.7
5. File rotation: New file created at midnight (based on event timestamp, not system time)
6. Atomic writes: Write to temp file, then rename to prevent corruption if process interrupted
7. Directory creation: Automatically create date directories (data/events/2025-11-08/) if missing
8. File permissions: Created with 0644 (user read/write, group/others read-only)
9. Concurrent writes: File locking or append-only mode to prevent corruption if multi-threaded (future-proofing)
10. Performance: Log write completes in <5ms
11. Unit tests verify: file creation, directory structure, JSON Lines format, atomic writes
12. Integration test: Log 100 events across 3 days, verify correct file structure and content

---

## Story 3.5: Plaintext Event Log File Generation

**As a** developer,
**I want** to write human-readable plaintext event logs,
**so that** I can quickly review events manually without parsing JSON or querying the database.

**Acceptance Criteria:**

1. Plaintext logger module (core/plaintext_logger.py) implements PlaintextEventLogger class
2. Plaintext files organized by date: data/events/YYYY-MM-DD/events.log (one file per day)
3. Log format matches Technical Assumptions specification:
   ```
   [2025-11-08 14:32:15] EVENT: Person detected at front door (confidence: 92%)
     - Objects: person (92%), package (87%)
     - Description: Person in blue shirt carrying brown package approaching front door
     - Image: data/events/2025-11-08/evt_12345.jpg
   ```
4. Timestamp in local timezone with format: YYYY-MM-DD HH:MM:SS
5. Event separator: Blank line between events for readability
6. Detected objects listed with confidence percentages
7. LLM description included on "Description:" line
8. Image path as relative path from project root
9. Metadata line (optional, at DEBUG level): Frame number, inference times
10. File rotation synchronized with JSON logger (same midnight boundary)
11. Performance: Write completes in <5ms
12. Unit tests verify: log format, multi-object display, timestamp formatting
13. Integration test: Generate logs for 50 events, manually inspect for readability and correctness

---

## Story 3.6: Storage Monitoring and Size Limits Enforcement

**As a** developer,
**I want** to monitor disk usage and enforce storage limits,
**so that** the system doesn't consume unlimited disk space (NFR10: <4GB for 30 days).

**Acceptance Criteria:**

1. Storage monitor module (core/storage_monitor.py) implements StorageMonitor class with check_usage() method
2. max_storage_gb configuration parameter specifies limit (default: 4GB)
3. check_usage() calculates total size of data/events directory (database + logs + images)
4. Size calculation uses os.path.getsize() recursively through all subdirectories
5. check_usage() returns StorageStats object: total_bytes, limit_bytes, percentage_used, is_over_limit
6. Storage check performed every 100 events (configurable via storage_check_interval)
7. If storage exceeds limit, log ERROR: "Storage limit exceeded: [X]GB / [Y]GB ([Z]%)"
8. Over-limit action (NFR28): Trigger graceful shutdown with exit code indicating storage full
9. Warning threshold: Log WARNING at 80% of limit ("Storage at 3.2GB / 4GB (80%), approaching limit")
10. Storage stats logged in runtime status display: "Storage: 1.2GB / 4GB (30%)"
11. Unit tests verify: size calculation, limit enforcement, warning thresholds
12. Integration test: Simulate storage growth to limit, verify warning and shutdown trigger

---

## Story 3.7: Log Rotation and Cleanup Strategy

**As a** developer,
**I want** to implement FIFO log rotation to manage disk space,
**so that** old logs are deleted when storage limit is approached.

**Acceptance Criteria:**

1. Log rotation module (core/log_rotation.py) implements LogRotator class with rotate_logs() method
2. Rotation strategy: Delete oldest date directories when storage >90% of limit
3. rotate_logs() identifies oldest directories by date (YYYY-MM-DD) in data/events/
4. Deletion order: Oldest first, continues until storage <80% of limit
5. Deletion includes: Date directory with all contents (JSON logs, plaintext logs, annotated images)
6. Rotation logged at WARNING level: "Storage limit approaching, deleting old logs: 2025-10-15 (freed [X]MB)"
7. Protection: Never delete events from current day (today's directory is protected)
8. Minimum retention: Keep at least 7 days of data regardless of storage (configurable via min_retention_days)
9. rotate_logs() called automatically when storage check detects >90% usage
10. Manual rotation support: rotate_logs(force=True) bypasses percentage check
11. Unit tests verify: oldest directory identification, deletion logic, protection rules
12. Integration test: Fill storage to 95%, trigger rotation, verify oldest logs deleted and storage reduced

---

## Story 3.8: Performance Metrics Collection and Logging

**As a** developer,
**I want** to collect and log system performance metrics,
**so that** I can monitor system health and validate NFR performance targets.

**Acceptance Criteria:**

1. Metrics collector module (core/metrics.py) implements MetricsCollector class with collect() method
2. Metrics collected (per NFR21, FR24-26):
   - frames_processed: total count
   - motion_detected: count and hit rate percentage
   - events_created: count
   - events_suppressed: count (de-duplication)
   - coreml_inference_time: average, min, max, p95
   - llm_inference_time: average, min, max, p95
   - cpu_usage: current and average (via psutil)
   - memory_usage: current in MB/GB (via psutil)
   - frame_processing_latency: end-to-end time from motion → event logged
   - system_availability: uptime percentage
3. Metrics stored in-memory with rolling window (last 1000 events for averages)
4. collect() returns MetricsSnapshot object with all current values
5. Metrics logged to dedicated file: logs/metrics.json (JSON Lines format)
6. Metrics logged periodically: Every 60 seconds (configurable via metrics_interval)
7. Metrics included in runtime status display (console output every 60s)
8. Performance: Metrics collection overhead <1% CPU (verified via profiling)
9. Unit tests verify: metric calculation, rolling window, percentile calculation
10. Integration test: Run system for 10 minutes, verify metrics logged correctly and match expected values

---

## Story 3.9: Pipeline Integration - Database and File Persistence

**As a** developer,
**I want** to integrate database and file logging into the processing pipeline,
**so that** all events are persisted to all three storage mechanisms (database, JSON, plaintext).

**Acceptance Criteria:**

1. ProcessingPipeline extended with persistence stage (after event creation in Epic 2):
   - Stage 7: Persist event to SQLite database
   - Stage 8: Write JSON log file
   - Stage 9: Write plaintext log file
   - Stage 10: Check storage limits
2. For each created event:
   - Insert into database via DatabaseManager.insert_event()
   - Append to JSON log via JSONEventLogger.log_event()
   - Append to plaintext log via PlaintextEventLogger.log_event()
   - Every 100 events, check storage via StorageMonitor.check_usage()
3. Error handling: Database write failure doesn't prevent file logging (graceful degradation)
4. Transaction semantics: All three writes attempted even if one fails (best-effort persistence)
5. Failed writes logged at ERROR level with specific failure reason
6. Pipeline metrics extended: events_persisted, db_write_errors, file_write_errors, storage_warnings
7. Startup initialization: DatabaseManager.init_database() called during health check
8. Shutdown cleanup: Flush all buffers, close database connection gracefully
9. Unit tests verify: all persistence mechanisms called, error handling, graceful degradation
10. Integration test: Run full pipeline for 5 minutes, verify events in database, JSON files, and plaintext files
11. Storage limit test: Run until storage limit reached, verify graceful shutdown triggered
12. Manual test: Review database content with sqlite3 CLI, verify data integrity and queryability

---

**Epic 3 Summary:**
- **9 Stories** delivering SQLite persistence, dual-format logging, storage management, and metrics collection
- **Vertical slices:** Each story delivers complete persistence layer functionality
- **Core value delivered:** Events are permanently stored, queryable, and managed within storage constraints
- **Deployable:** After Epic 3, system has complete data persistence and can be queried for historical analysis (ready for Phase 2 web dashboard)

---

## Rationale for Story Breakdown:

**Why 9 stories:**
- Database foundation (3.1-3.3): 3 stories for schema, persistence, querying
- File logging (3.4-3.5): 2 stories for JSON and plaintext formats
- Storage management (3.6-3.7): 2 stories for monitoring and rotation
- Metrics (3.8): 1 story for performance tracking
- Integration (3.9): 1 story tying everything together

**Story sequencing:**
- 3.1 (Schema) before 3.2 (Insert) - need database before writing to it
- 3.2 (Insert) before 3.3 (Query) - persistence before retrieval
- 3.4-3.5 (Logging) parallel - independent file formats
- 3.6 (Monitoring) before 3.7 (Rotation) - need to check before cleaning
- 3.8 (Metrics) parallel to storage - independent concern
- 3.9 (Integration) last - combines all persistence mechanisms

**Cross-cutting concerns:**
- Testing: Unit tests for logic, integration tests for database operations
- Performance: All write operations <10ms to avoid blocking pipeline
- Error handling: Graceful degradation if one persistence mechanism fails
- Storage: Consistent enforcement of 4GB limit across all data

---
