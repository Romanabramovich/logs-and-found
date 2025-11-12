# 📚 Documentation Index

Complete guide to all documentation for the Log Aggregation Platform.

---

## 🚀 Getting Started

Start here if you're new to the project:

| Document | Description | Time to Read |
|----------|-------------|--------------|
| **[README.md](README.md)** | Project overview, features, quick start | 10 min |
| **[QUICKSTART.md](QUICKSTART.md)** | Step-by-step setup guide | 15 min |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | System design and technical deep-dive | 30 min |

---

## 📖 Core Documentation

### System Design & Architecture

- **[ARCHITECTURE.md](ARCHITECTURE.md)**
  - Complete system architecture
  - Component descriptions
  - Data flow diagrams
  - Scaling strategies
  - Performance characteristics

### Features & Capabilities

- **[PARSER_GUIDE.md](PARSER_GUIDE.md)**
  - Multi-format log parsing
  - Auto-detection system
  - Adding custom parsers
  - Parser API reference

- **[WEBSOCKET_SETUP.md](WEBSOCKET_SETUP.md)**
  - Real-time log streaming
  - WebSocket client setup
  - Connection management
  - Testing WebSocket functionality

- **[PERFORMANCE_RESULTS.md](PERFORMANCE_RESULTS.md)**
  - Benchmark results
  - Performance optimizations
  - Before/after comparisons
  - Tuning recommendations

---

## 🛠️ Technical Guides

### Migration & Upgrades

- **[FASTAPI_MIGRATION.md](FASTAPI_MIGRATION.md)**
  - Flask → FastAPI migration notes
  - Breaking changes
  - Performance improvements
  - API endpoint changes

### Integration Guides

  - Data source configuration
  - Dashboard import
  - Custom panel creation

- **[docs/REDIS_QUICK_START.md](docs/REDIS_QUICK_START.md)**
  - Redis installation
  - Message queue setup
  - Worker configuration
  - Troubleshooting

---

## 📁 Directory-Specific Documentation

Each major directory contains its own README:

| Directory | README | Purpose |
|-----------|--------|---------|
| `src/` | [src/README.md](src/README.md) | Source code overview |
| `src/api/` | [src/api/README.md](src/api/README.md) | API layer documentation |
| `src/queue/` | [src/queue/README.md](src/queue/README.md) | Redis queue system |
| `src/shipper/` | [src/shipper/README.md](src/shipper/README.md) | Log collection agents |
| `src/web/` | [src/web/README.md](src/web/README.md) | Web UI templates |
| `src/tests/` | [src/tests/README.md](src/tests/README.md) | Test suites |
| `src/data/` | [src/data/README.md](src/data/README.md) | Database schemas |
| `docs/` | [docs/README.md](docs/README.md) | Additional documentation |


---

## 📊 API Documentation

### Interactive Documentation

- **Swagger UI:** http://127.0.0.1:5000/api/docs
  - Try endpoints interactively
  - See request/response schemas

### Endpoint Reference

**Ingestion:**
```
POST /logs           - High-performance Redis queue (all logs)
```

**Parsing:**
```
POST /parse/auto     - Auto-detect and parse
GET  /parse/formats  - List supported formats
GET  /parse/patterns - Get regex patterns
```

**Retrieval:**
```
GET  /logs/          - List logs (paginated)
GET  /logs/{id}      - Get specific log
```

**Real-time:**
```
WS   /ws/logs        - WebSocket streaming
```

**System:**
```
GET  /health         - Health check
GET  /queue/status   - Redis queue stats
```

---

## 🧪 Testing Documentation

### Test Suites

| Test File | Purpose | Runtime |
|-----------|---------|---------|
| `test_api.py` | API endpoint tests | < 1s |
| `test_parsers.py` | Parser functionality | < 1s |
| `test_redis_performance.py` | Redis integration | 2-5s |
| `test_redis_concurrent.py` | Performance benchmark | 2-5s |

### Running Tests

```bash
# All tests
python src/tests/test_api.py
python src/tests/test_parsers.py

# Performance
python src/tests/test_redis_concurrent.py
```

See: [src/tests/README.md](src/tests/README.md)

---

## 🔧 Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_URL` | ✅ Yes | - | PostgreSQL connection string |
| `REDIS_URL` | ⚠️ Recommended | `redis://127.0.0.1:6379` | Redis connection |
| `LOG_LEVEL` | No | `INFO` | Application log level |

### Configuration Files

- **`.env`** - Environment variables (create from `.env.example`)
- **`requirements.txt`** - Python dependencies
- **`src/data/schema.sql`** - Database schema

---

## 📦 Additional Resources

  - Import-ready JSON
  - Includes: log volume, error rates, sources

### Example Code

- **[src/shipper/log_generator.py](src/shipper/log_generator.py)** - Generate test logs
- **[src/shipper/log_shipper.py](src/shipper/log_shipper.py)** - Ship logs from files
- **[src/tests/](src/tests/)** - Test examples

---