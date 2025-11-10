# Database Migrations

This directory contains SQL migration scripts for the video recognition system database.

## Migration Process

Migrations are applied automatically when the system starts. The `DatabaseManager.init_database()` method:

1. Checks the current schema version in the `schema_version` table
2. Applies any pending migrations in numerical order
3. Updates the schema version after successful migration

## Migration Files

- `001_initial.sql`: Initial database schema with events table, indexes, and schema versioning

## Creating New Migrations

When schema changes are needed:

1. Create a new migration file: `00N_description.sql`
2. Include all necessary DDL statements (CREATE, ALTER, etc.)
3. Update the schema version: `INSERT INTO schema_version (version) VALUES (N);`
4. Test the migration thoroughly before deployment

## Migration Safety

- All migrations are wrapped in transactions
- If a migration fails, the transaction is rolled back
- Failed migrations log errors and cause system startup to fail (prevents inconsistent state)

## Backup and Recovery

For production deployments, always backup the database before applying migrations:

```bash
# Backup
sqlite3 data/events.db .dump > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore if needed
sqlite3 data/events.db < backup_20251109_120000.sql
```

## Schema Versioning

The `schema_version` table tracks the current database schema version:

```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

- Version numbers are sequential integers starting from 1
- Each migration increments the version by 1
- The system expects the schema to be at the latest version

## Troubleshooting

### Migration Fails on Startup

- Check database file permissions
- Verify migration file exists and is readable
- Review application logs for specific error details
- Restore from backup if corruption occurred

### Schema Inconsistencies

- Compare actual schema with migration files
- Manually apply missing DDL statements
- Update schema_version table to correct version

### Performance Impact

- Migrations run only once per version
- Large migrations may temporarily impact startup time
- Consider breaking large changes into multiple smaller migrations