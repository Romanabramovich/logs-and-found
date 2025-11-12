# src/api/ - Flask API

REST API for log ingestion using Flask and SQLAlchemy.

## Files

- `app.py` - Flask application and endpoints
- `models.py` - SQLAlchemy ORM models

## app.py

Flask application with log ingestion endpoint.

**Endpoint: `POST /data/`**

Accepts log entries and stores them in PostgreSQL.

**Request:**
```json
{
  "timestamp": "2025-11-11T18:30:00Z",
  "level": "ERROR",
  "source": "web-server-01",
  "application": "user-api",
  "message": "Database connection timeout",
  "metadata": {"user_id": "123"}
}
```

**Response (201):**
```json
{
  "status": "success",
  "log_id": 1,
  "message": "Log inserted successfully"
}
```

**Run the API:**
```bash
python -m src.api.app
```

## models.py

SQLAlchemy ORM model for the logs table.

**Log Model:**
- `id` - Primary key
- `timestamp` - Event timestamp (timezone-aware)
- `level` - Log level (ERROR, WARN, INFO, DEBUG)
- `source` - Source server/service
- `application` - Application name
- `message` - Log message
- `log_metadata` - JSONB metadata (maps to `metadata` column in DB)
- `created_at` - Insertion timestamp (auto-set)

**Note:** Python uses `log_metadata` attribute, but it maps to the `metadata` column in PostgreSQL (to avoid SQLAlchemy's reserved `metadata` attribute).

**Usage:**
```python
from src.api.models import Log

log = Log(
    timestamp=datetime.now(timezone.utc),
    level="ERROR",
    source="web-server-01",
    application="api",
    message="Error message",
    log_metadata={"key": "value"}
)
```
