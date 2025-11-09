# Database Manager

**Responsibility:** Manages SQLite database connection, handles schema initialization and migrations, provides CRUD operations for events.

**Key Interfaces:**
- `init_database(db_path: str) -> None`: Initialize database, create schema, apply migrations
- `insert_event(event: Event) -> bool`: Persist event to database
- `get_event_by_id(event_id: str) -> Event | None`: Retrieve single event
- `get_events_by_timerange(start: datetime, end: datetime) -> list[Event]`: Query events by time
- `get_recent_events(limit: int) -> list[Event]`: Get N most recent events
- `count_events() -> int`: Total event count

**Dependencies:**
- sqlite3 (Python stdlib)
- Pydantic Event model
- SystemConfig (for db_path)

**Technology Stack:**
- Python 3.10+ (stdlib sqlite3 module)
- Module path: `core/database.py`
- Class: `DatabaseManager`

**Implementation Notes:**
- Single shared connection for entire application (no connection pooling needed)
- Schema version tracking in schema_version table
- Migration scripts in migrations/ directory (manual SQL files)
- Uses parameterized queries to prevent SQL injection
- Transaction wrapping for atomicity (insert_event wrapped in BEGIN/COMMIT)
- Index on timestamp DESC for efficient recent event queries

---
