# Event Manager

**Responsibility:** Creates Event objects from processed frame data, handles event de-duplication to suppress similar consecutive events, coordinates persistence across multiple loggers.

**Key Interfaces:**
- `create_event(frame, objects, description) -> Event | None`: Create event, returns None if suppressed
- `should_suppress(event: Event) -> bool`: Check if event is duplicate of recent event
- `reset_suppression() -> None`: Clear suppression cache

**Dependencies:**
- Pydantic Event model
- DatabaseManager, JSONEventLogger, PlaintextEventLogger
- SystemConfig (for suppression threshold and window)

**Technology Stack:**
- Python 3.10+
- Module path: `core/event_manager.py`
- Class: `EventManager`

**Implementation Notes:**
- De-duplication algorithm: Compare new event objects to last 5 events
- Suppression threshold: ≥80% overlap in detected object labels
- Generates event_id using format: `evt_{timestamp}_{random_suffix}`
- Delegates persistence to DatabaseManager and both loggers
- Tracks suppression count in metrics (events_suppressed)

---
