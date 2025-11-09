# Plaintext Event Logger

**Responsibility:** Writes human-readable plaintext event logs for quick manual review without parsing JSON or querying database.

**Key Interfaces:**
- `log_event(event: Event) -> None`: Append formatted event to plaintext log

**Dependencies:**
- Pydantic Event model
- SystemConfig (for log directory path)

**Technology Stack:**
- Python 3.10+ (stdlib)
- Module path: `core/plaintext_logger.py`
- Class: `PlaintextEventLogger`

**Implementation Notes:**
- File organization: `data/events/YYYY-MM-DD/events.log`
- Log format:
  ```
  [2025-11-08 14:32:15] EVENT: Person detected at front door (confidence: 92%)
    - Objects: person (92%), package (87%)
    - Description: Person in blue shirt carrying brown package approaching front door
    - Image: data/events/2025-11-08/evt_12345.jpg
  ```
- Timestamp in local timezone (YYYY-MM-DD HH:MM:SS)
- Blank line between events for readability
- File rotation synchronized with JSON logger (same midnight boundary)

---
