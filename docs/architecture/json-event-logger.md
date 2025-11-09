# JSON Event Logger

**Responsibility:** Writes events to date-organized JSON log files in JSON Lines format for programmatic processing by external tools.

**Key Interfaces:**
- `log_event(event: Event) -> None`: Append event to appropriate JSON file

**Dependencies:**
- Pydantic Event model (for .model_dump_json())
- SystemConfig (for log directory path)

**Technology Stack:**
- Python 3.10+ (stdlib json and pathlib)
- Module path: `core/json_logger.py`
- Class: `JSONEventLogger`

**Implementation Notes:**
- File organization: `data/events/YYYY-MM-DD/events.json`
- One file per day, new file created at midnight (based on event timestamp)
- JSON Lines format: one JSON object per line, not a JSON array
- Atomic writes: write to temp file, then os.rename() for atomicity
- Auto-creates date directories if missing
- File permissions: 0644 (user read/write, group/others read)

---
