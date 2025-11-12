# src/data/ - Database Schemas

PostgreSQL table definitions and SQL scripts.

## Files

- `schema.sql` - Table and index definitions

## schema.sql

Creates the `logs` table with performance indexes.

**Table: logs**
- `id` - Auto-incrementing primary key
- `timestamp` - Event timestamp (timezone-aware)
- `level` - Log level (VARCHAR 10)
- `source` - Source identifier (VARCHAR 100)
- `application` - Application name (VARCHAR 100)
- `message` - Log content (TEXT)
- `metadata` - Flexible JSON data (JSONB)
- `created_at` - Insertion timestamp (auto-set)

**Indexes:**
- `idx_timestamp` - Fast time-range queries
- `idx_level` - Filter by log level
- `idx_source` - Filter by source
- `idx_log_metadata` - Query metadata fields (GIN index)

**Run the schema:**
```bash
# From psql prompt
\i src/data/schema.sql

# Or from command line
psql your_db_url -f src/data/schema.sql
```

**Verify:**
```sql
\dt logs
\d logs
```
