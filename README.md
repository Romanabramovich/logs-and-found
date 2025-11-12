# 📊 Distributed Log Aggregation Platform

<div align="center">

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7.0+-red.svg)](https://redis.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**High-performance, distributed log aggregation system with real-time streaming and intelligent parsing**

[Features](#-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [Documentation](#-documentation)

</div>

---

## 🎯 Overview

Enterprise-grade log aggregation platform designed for **high throughput**, **real-time processing**, and **multi-format support**. Built with modern async Python, this system can ingest, parse, store, and visualize logs from diverse sources with intelligent format detection.

### 📈 Key Metrics

| Metric | Value | Description |
|--------|-------|-------------|
| **Ingestion Rate** | 568 logs/sec | Production mode with 12 workers |
| **API Latency** | 3ms | Average response time |
| **Formats Supported** | 4 | JSON, Apache, Syslog (RFC 5424/3164) |
| **Auto-Detection** | 100% | Accuracy on supported formats |
| **Real-time Streaming** | < 100ms | WebSocket update latency |
| **Performance Gain** | 23.6x | vs. Flask development server |

---

## ✨ Features

### Core Capabilities
- ✅ **High-Performance Ingestion** - FastAPI + Uvicorn async processing
- ✅ **Redis Message Queue** - Traffic spike buffering with Redis Streams
- ✅ **Multi-Format Support** - JSON Lines, Apache/Nginx, Syslog RFC 5424/3164
- ✅ **Intelligent Auto-Detection** - Automatic log format recognition
- ✅ **Real-Time Streaming** - WebSocket-powered live dashboard updates
- ✅ **Horizontal Scaling** - Multi-process worker pools
- ✅ **Rich Metadata** - JSONB storage for flexible log enrichment

### Observability
- 📊 **Grafana Integration** - Pre-built dashboards for metrics
- 🎨 **Modern Web UI** - Bootstrap-powered log viewer with filters
- 📖 **Interactive API Docs** - Auto-generated Swagger/OpenAPI documentation
- 🔍 **Advanced Filtering** - Search by level, source, application, timerange

### Developer Experience
- 🔌 **Pluggable Parsers** - Extensible architecture for custom formats
- 🧪 **Comprehensive Tests** - Parser, performance, and integration test suites
- 📝 **Complete Documentation** - Setup guides, architecture docs, examples
- 🐳 **Production Ready** - Multi-worker deployment with health checks

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.13+**
- **PostgreSQL 15+**
- **Redis 7.0+**
- **pip** package manager

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/log-aggregation.git
cd log-aggregation
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the project root:

```env
# Database Configuration
DB_URL=postgresql://log_user:log_password@localhost:5433/log_aggregation

# Redis Configuration (optional but recommended)
REDIS_URL=redis://localhost:6379
```

### 4. Setup PostgreSQL

```bash
# Option A: Using psql directly
psql postgresql://log_user:log_password@localhost:5433/log_aggregation -f src/data/schema.sql

# Option B: From psql prompt
psql postgresql://log_user:log_password@localhost:5433/log_aggregation
\i src/data/schema.sql
```

### 5. Start Redis (Optional but Recommended)

```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or install locally and start
redis-server
```

### 6. Start the System

#### Option A: Development Mode (Auto-reload)
```bash
# Terminal 1: Start API
python run_dev.py

# Terminal 2: Start worker pool (if using Redis)
python -m src.queue.worker_pool --workers 3
```

#### Option B: Production Mode (Multi-worker)
```bash
# Terminal 1: Start API with 12 workers
python run_production.py

# Terminal 2: Start worker pool
python -m src.queue.worker_pool --workers 3
```

### 7. Access the System

- **Web Dashboard:** http://127.0.0.1:5000
- **API Documentation:** http://127.0.0.1:5000/api/docs
- **Health Check:** http://127.0.0.1:5000/health

---

## 🏗️ Architecture

```mermaid
graph TB
    Sources["📱 LOG SOURCES<br/>Applications, Services, Servers, Containers"]
    
    Sources -->|HTTP POST<br/>JSON/Text| API
    
    subgraph FastAPI["🚀 FASTAPI INGESTION API"]
        Endpoints["POST /data/fast - Redis queue<br/>POST /data/ - Direct DB<br/>POST /parse/auto - Auto-detect<br/>WS /ws/logs - Real-time"]
    end
    
    API[FastAPI] --> Endpoints
    
    API -->|Fast Path| Redis
    API -->|Direct Path| PostgresDB
    
    Redis["🔴 REDIS<br/>• Streams (Queue)<br/>• Pub/Sub"]
    
    Redis -->|Async Processing| Workers
    
    subgraph WorkerPool["⚙️ WORKER POOL"]
        W1[Worker 1]
        W2[Worker 2]
        W3[Worker N]
    end
    
    Workers[Workers] --> W1
    Workers --> W2
    Workers --> W3
    
    W1 -->|Batch Insert| DB
    W2 -->|Batch Insert| DB
    W3 -->|Batch Insert| DB
    
    PostgresDB[Direct Write] --> DB
    
    DB[("🗄️ POSTGRESQL<br/>• logs table<br/>• JSONB metadata<br/>• Indexed queries")]
    
    DB --> Dashboard
    DB --> Grafana
    
    Redis -.->|Pub/Sub| Dashboard
    
    Dashboard["📊 WEB DASHBOARD<br/>• Live updates<br/>• Filtering<br/>• Search<br/>• WebSocket"]
    
    Grafana["📈 GRAFANA<br/>• Time-series<br/>• Alerts<br/>• Analytics<br/>• Custom panels"]
    
    style Sources fill:#e6f3ff,stroke:#0066cc,stroke-width:2px
    style API fill:#e6ffe6,stroke:#00cc00,stroke-width:3px
    style FastAPI fill:#f0ffe6,stroke:#66cc00,stroke-width:2px
    style Redis fill:#ffe6e6,stroke:#cc0000,stroke-width:3px
    style WorkerPool fill:#fff4e6,stroke:#ff9900,stroke-width:2px
    style DB fill:#e6ffe6,stroke:#00cc00,stroke-width:3px
    style Dashboard fill:#f0e6ff,stroke:#9900cc,stroke-width:2px
    style Grafana fill:#ffe6f0,stroke:#cc0099,stroke-width:2px
```

### Data Flow

1. **Ingestion** - FastAPI receives logs via HTTP POST (568 logs/sec)
2. **Queuing** - Redis Streams buffer logs for async processing
3. **Parsing** - Auto-detect format (JSON/Apache/Syslog) and normalize
4. **Storage** - Worker pool batch-writes to PostgreSQL
5. **Broadcasting** - Redis Pub/Sub notifies WebSocket clients
6. **Visualization** - Real-time dashboard updates + Grafana metrics

---

## 💡 Usage Examples

### Send Logs via API

```bash
# Using curl
curl -X POST http://127.0.0.1:5000/data/fast \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2025-11-11T16:00:00",
    "level": "ERROR",
    "source": "web-server",
    "application": "api",
    "message": "Database connection failed",
    "metadata": {"user_id": 12345}
  }'
```

```python
# Using Python requests
import requests

log_entry = {
    "timestamp": "2025-11-11T16:00:00",
    "level": "INFO",
    "source": "app-server",
    "application": "auth",
    "message": "User logged in successfully"
}

response = requests.post(
    "http://127.0.0.1:5000/data/fast",
    json=log_entry
)
print(response.json())
```

### Auto-Parse Different Log Formats

```bash
# JSON log
curl -X POST http://127.0.0.1:5000/parse/auto \
  -H "Content-Type: application/json" \
  -d '{"raw_log": "{\"timestamp\":\"2025-11-11T16:00:00\",\"level\":\"ERROR\",\"message\":\"Failed\"}"}'

# Apache/Nginx log
curl -X POST http://127.0.0.1:5000/parse/auto \
  -H "Content-Type: application/json" \
  -d '{"raw_log": "192.168.1.1 - - [11/Nov/2025:16:00:00 +0000] \"GET /api/health HTTP/1.1\" 200 45"}'

# Syslog
curl -X POST http://127.0.0.1:5000/parse/auto \
  -H "Content-Type: application/json" \
  -d '{"raw_log": "<34>1 2025-11-11T16:00:00Z server1 sshd 1234 - - Login attempt"}'
```

### Ship Logs from Files

```bash
# Generate test logs
python -m src.shipper.log_generator

# Ship logs to API (with position tracking)
python -m src.shipper.log_shipper src/shipper/test_logs.log
```

---

## 🧪 Testing

### Run Test Suites

```bash
# API tests
python src/tests/test_api.py

# Parser tests
python src/tests/test_parsers.py

# Performance benchmarks
python src/tests/test_redis_concurrent.py

# Redis integration tests
python src/tests/test_redis_performance.py
```

### Performance Benchmarks

```bash
# Test concurrent load (1000 logs with 10 concurrent workers)
python src/tests/test_redis_concurrent.py

# Expected output:
# ✓ All logs successfully ingested
# ✓ Performance: 568 logs/sec
# ✓ Average latency: 3ms
```

---

## 📖 Documentation

- **[Parser Guide](PARSER_GUIDE.md)** - Multi-format parsing system
- **[WebSocket Setup](WEBSOCKET_SETUP.md)** - Real-time streaming configuration
- **[Performance Results](PERFORMANCE_RESULTS.md)** - Benchmark analysis
- **[FastAPI Migration](FASTAPI_MIGRATION.md)** - Flask → FastAPI upgrade notes
- **[Grafana Setup](docs/GRAFANA_SETUP.md)** - Dashboard configuration
- **[Redis Quick Start](docs/REDIS_QUICK_START.md)** - Message queue setup

---

## 🛠️ Technology Stack

### Backend
- **FastAPI 0.115** - Modern async web framework
- **Uvicorn** - ASGI server with multi-worker support
- **Pydantic** - Data validation and serialization
- **SQLAlchemy 2.0** - ORM with async support

### Storage
- **PostgreSQL 15+** - Primary data store with JSONB
- **Redis 7.0+** - Message queue (Streams) and Pub/Sub

### Frontend
- **Jinja2** - Server-side templating
- **Bootstrap 5** - Responsive UI framework
- **WebSocket API** - Real-time log streaming

### Monitoring
- **Grafana** - Time-series visualization and alerting
- **Custom Metrics** - Log volume, error rates, latency

---

## 📁 Project Structure

```
log-aggregation/
├── src/
│   ├── api/              # FastAPI application
│   │   ├── app.py        # Main API with endpoints
│   │   ├── models.py     # SQLAlchemy ORM models
│   │   └── schemas.py    # Pydantic validation schemas
│   ├── parsers/          # Log format parsers
│   │   ├── base.py       # Abstract parser interface
│   │   ├── json_parser.py
│   │   ├── apache_parser.py
│   │   ├── syslog_parser.py
│   │   ├── regex_parser.py
│   │   └── parser_factory.py
│   ├── queue/            # Redis integration
│   │   ├── redis_producer.py
│   │   ├── redis_consumer.py
│   │   └── worker_pool.py
│   ├── shipper/          # Log collection
│   │   ├── log_shipper.py
│   │   └── log_generator.py
│   ├── web/              # Web UI templates
│   │   └── templates/
│   ├── tests/            # Test suites
│   ├── data/             # Database schemas
│   └── database.py       # DB connection utilities
├── docs/                 # Documentation
│   ├── grafana/          # Grafana dashboards
│   └── *.md              # Guides and specs
├── run_dev.py            # Development server
├── run_production.py     # Production server
├── requirements.txt      # Python dependencies
└── README.md
```

---

## 🎨 Web Dashboard Features

- **Real-Time Updates** - Live log streaming with WebSocket
- **Advanced Filtering** - By level (INFO/WARN/ERROR), source, application
- **Search** - Full-text search across log messages
- **Pagination** - Efficient browsing of large datasets
- **Statistics Cards** - Total logs, error rate, recent activity
- **Responsive Design** - Works on desktop, tablet, mobile

---

## 📊 API Endpoints

### Log Ingestion
- `POST /data/` - Direct PostgreSQL write
- `POST /data/fast` - High-speed Redis queue (recommended)
- `POST /data/batch` - Batch ingestion (multiple logs)

### Log Parsing
- `POST /parse/auto` - Auto-detect and parse log format
- `GET /parse/formats` - List supported formats
- `GET /parse/patterns` - Get predefined regex patterns

### Log Retrieval
- `GET /logs/` - Paginated log list with filters
- `GET /logs/{id}` - Get specific log entry

### Real-Time
- `WS /ws/logs` - WebSocket endpoint for live streaming

### System
- `GET /health` - Health check and system status
- `GET /queue/status` - Redis queue statistics

**Interactive API Documentation:** http://127.0.0.1:5000/api/docs

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DB_URL` | PostgreSQL connection string | - | ✅ Yes |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` | ⚠️ Recommended |
| `LOG_LEVEL` | Application log level | `INFO` | No |

### Performance Tuning

**Development Mode:**
```bash
# Single worker, auto-reload
python run_dev.py
```

**Production Mode:**
```bash
# Multi-worker (CPU count), optimized
python run_production.py
```

**Worker Pool:**
```bash
# Adjust worker count based on load
python -m src.queue.worker_pool --workers 5 --batch-size 100
```

---

## 📈 Performance Optimization

### Achieved Improvements

| Optimization | Before | After | Gain |
|--------------|--------|-------|------|
| Flask → FastAPI | 0.5 logs/sec | 24 logs/sec | **48x** |
| Dev → Production mode | 24 logs/sec | 568 logs/sec | **23.6x** |
| localhost → 127.0.0.1 | 2032ms latency | 3ms latency | **677x** |
| Direct DB → Redis Queue | Blocking | Non-blocking | ∞ |

### Recommendations

1. **Use Redis Queue** - Enables async processing and traffic buffering
2. **Production Mode** - Leverage all CPU cores with multi-worker setup
3. **Batch Inserts** - Worker pool uses batch writes for efficiency
4. **Use 127.0.0.1** - Avoid Windows DNS resolution delays
5. **Connection Pooling** - SQLAlchemy pools DB connections automatically

---

## 🐳 Docker Deployment (Coming Soon)

```bash
# Start all services
docker-compose up -d

# Includes: FastAPI, PostgreSQL, Redis, Grafana, Workers
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

### Adding Custom Parsers

```python
from src.parsers.base import LogParser
from src.api.schemas import LogCreate

class MyCustomParser(LogParser):
    def parse(self, raw_log: str) -> LogCreate:
        # Your parsing logic here
        return LogCreate(
            timestamp=...,
            level=...,
            source=...,
            application=...,
            message=...,
            metadata=...
        )
```

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

Built with modern Python async patterns and industry-standard tools:
- FastAPI for blazing-fast API performance
- PostgreSQL for reliable data persistence
- Redis for distributed message queuing
- Grafana for professional observability

---

## 📧 Contact

**Project Maintainer:** [Your Name]
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your Profile](https://linkedin.com/in/yourprofile)
- Email: your.email@example.com

---

<div align="center">

**⭐ Star this repo if you find it useful!**

[Report Bug](https://github.com/yourusername/log-aggregation/issues) • [Request Feature](https://github.com/yourusername/log-aggregation/issues)

</div>
