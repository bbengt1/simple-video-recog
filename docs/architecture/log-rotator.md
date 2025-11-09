# Log Rotator

**Responsibility:** Implements FIFO log rotation to manage disk space by deleting oldest date directories when storage limit approached.

**Key Interfaces:**
- `rotate_logs() -> int`: Delete old logs, returns bytes freed
- `get_deletion_candidates() -> list[str]`: Identify date directories to delete

**Dependencies:**
- StorageMonitor (to check current usage)
- SystemConfig (for min_retention_days)

**Technology Stack:**
- Python 3.10+ (stdlib shutil for directory deletion)
- Module path: `core/log_rotation.py`
- Class: `LogRotator`

**Implementation Notes:**
- Deletion strategy: oldest first (by YYYY-MM-DD directory name)
- Continues deleting until storage <80% of limit
- Protection: never delete current day's directory
- Minimum retention: at least 7 days regardless of storage (configurable)
- Logs WARNING for each deleted directory with bytes freed

---
