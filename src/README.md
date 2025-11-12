# src/ - Source Code

All source code for the Log Aggregation System.

## Structure

```
src/
├── database.py       # PostgreSQL connection management
├── api/              # Flask API and data models
├── data/             # Database schemas
└── tests/            # Test suite
```

## database.py

Database connection utilities using SQLAlchemy.

**Functions:**
- `get_database_engine()` - Returns SQLAlchemy engine
- `test_connection()` - Tests database connectivity

**Environment Variables:**
- `DB_URL` - PostgreSQL connection string (required)

**Usage:**
```python
from src.database import get_database_engine

engine = get_database_engine()
```

**Test connection:**
```bash
python -m src.database
```
