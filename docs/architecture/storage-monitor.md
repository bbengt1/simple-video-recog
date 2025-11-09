# Storage Monitor

**Responsibility:** Monitors disk usage of data directory, enforces 4GB storage limit, triggers warnings and graceful shutdown when limit approached.

**Key Interfaces:**
- `check_usage() -> StorageStats`: Calculate total storage usage
- `is_over_limit() -> bool`: Check if storage exceeds max_storage_gb

**Dependencies:**
- SystemConfig (for max_storage_gb, storage_check_interval)

**Technology Stack:**
- Python 3.10+ (stdlib os and pathlib)
- Module path: `core/storage_monitor.py`
- Class: `StorageMonitor`

**Implementation Notes:**
- Calculates total size of data/events directory recursively
- Check frequency: every 100 events (configurable)
- Warning threshold: 80% of limit (logs WARNING)
- Critical threshold: 100% of limit (logs ERROR, triggers graceful shutdown)
- Returns StorageStats: total_bytes, limit_bytes, percentage_used, is_over_limit

---
