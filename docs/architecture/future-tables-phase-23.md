# Future Tables (Phase 2/3)

**Cameras Table (Phase 2):**
```sql
CREATE TABLE IF NOT EXISTS cameras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    rtsp_url TEXT NOT NULL,
    location TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**System Metrics Table (Phase 3):**
```sql
CREATE TABLE IF NOT EXISTS system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_timestamp ON system_metrics(timestamp DESC);
```

---
