# src/api/ - FastAPI Application

High-performance REST API for log ingestion using FastAPI, SQLAlchemy, and Redis.

## Files

- `app.py` - FastAPI application and endpoints
- `models.py` - SQLAlchemy ORM models
- `schemas.py` - Pydantic validation schemas

## app.py

FastAPI application with async log ingestion via Redis queue.

**Main Endpoint: `POST /logs`**

Accepts log entries and queues them in Redis for async processing.

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

**Response (202 Accepted):**
```json
{
  "status": "success",
  "message_id": "1762894896750-0",
  "message": "Log queued for processing"
}
```

**Run the API:**
```bash
# Development mode
python run_dev.py

# Production mode (multi-worker)
python run_production.py
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
