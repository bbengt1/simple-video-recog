# Schema Migration Strategy

**Migration Table:**
```sql
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO schema_version (version) VALUES (1);
```

**Migration Files:**
```
migrations/
├── 001_initial.sql          # Initial schema (events table + indexes)
├── 002_add_camera_table.sql # Future: Add cameras table for multi-camera
├── 003_add_metadata.sql     # Future: Add event metadata JSON field
└── README.md                # Migration process documentation
```

**Migration Process:**
1. On startup, check current schema_version (SELECT MAX(version))
2. Find migrations with version > current version
3. Apply migrations in sequence within transaction
4. Update schema_version table after each successful migration
5. Log ERROR and exit if migration fails (prevents running with incompatible schema)

**Rollback Strategy:**
- For MVP Phase 1: Backup → delete → recreate (acceptable for single-user system)
- Backup script: `sqlite3 data/events.db .dump > backup.sql`
- Restore script: `sqlite3 data/events.db < backup.sql`

---
