# 🏗️ System Architecture

## Overview

This document provides a detailed explanation of the log aggregation system's architecture, design decisions, and data flow.

---

## System Components

### 1. **Ingestion Layer** (FastAPI)

**Purpose:** High-performance log ingestion with multiple endpoints

**Key Features:**
- **Async/await** - Non-blocking I/O for concurrent request handling
- **Redis-based ingestion** - All logs queued for async processing
- **Auto-parsing** - Intelligent format detection
- **WebSocket support** - Real-time log streaming

**Endpoints:**
```
POST /logs        → Redis queue (async, high-performance)
POST /parse/auto  → Auto-detect and parse
WS   /ws/logs     → Real-time streaming
GET  /queue/status → Redis queue metrics
```

**Performance:**
- 1000+ logs/sec with 12 Uvicorn workers
- ~3ms average API latency
- Handles traffic spikes via Redis buffering
- Batch window: 500 logs or 2 seconds

---

### 2. **Message Queue Layer** (Redis Streams)

**Purpose:** Decouple ingestion from processing, handle traffic spikes

**Architecture:**

```mermaid
graph TB
    subgraph Redis["Redis Streams"]
        Stream["Stream: 'log_queue'"]
        
        subgraph Message["Message Format"]
            MsgFields["timestamp: ISO8601<br/>level: INFO|WARN|ERROR<br/>source: service-name<br/>application: app-name<br/>message: log message<br/>metadata: {...}"]
        end
        
        subgraph Consumers["Consumer Group: 'workers'"]
            W1[worker-1]
            W2[worker-2]
            W3[worker-N]
        end
        
        Stream --> Consumers
    end
    
    style Redis fill:#ffe6e6,stroke:#cc0000,stroke-width:2px,color:#000000
    style Stream fill:#fff4e6,stroke:#ff9900,stroke-width:2px,color:#000000
    style Message fill:#e6f3ff,stroke:#0066cc,stroke-width:2px,color:#000000
    style Consumers fill:#e6ffe6,stroke:#00cc00,stroke-width:2px,color:#000000
```

**Benefits:**
- **Buffering** - Absorbs traffic spikes
- **Crash recovery** - Messages persist until acknowledged
- **Horizontal scaling** - Add more workers dynamically
- **Ordering** - Maintains log sequence

---

### 3. **Processing Layer** (Worker Pool)

**Purpose:** Async log processing and batch database writes

**Architecture:**

```mermaid
graph TB
    subgraph WorkerPool["Worker Pool (Multiprocessing)"]
        W1["Process 1<br/>Consumer worker-1<br/>Batch: 100"]
        W2["Process 2<br/>Consumer worker-2<br/>Batch: 100"]
        W3["Process N<br/>Consumer worker-N<br/>Batch: 100"]
    end
    
    DB[("PostgreSQL<br/>Database")]
    
    W1 -->|Batch Insert| DB
    W2 -->|Batch Insert| DB
    W3 -->|Batch Insert| DB
    
    style WorkerPool fill:#e6f3ff,stroke:#0066cc,stroke-width:2px,color:#000000
    style W1 fill:#fff4e6,stroke:#ff9900,stroke-width:2px,color:#000000
    style W2 fill:#fff4e6,stroke:#ff9900,stroke-width:2px,color:#000000
    style W3 fill:#fff4e6,stroke:#ff9900,stroke-width:2px,color:#000000
    style DB fill:#e6ffe6,stroke:#00cc00,stroke-width:3px,color:#000000
```

**Configuration:**
```bash
# Launch with custom settings
python -m src.queue.worker_pool \
  --workers 5 \
  --batch-size 500
```

**Performance Optimization:**
- **Batch writes** - Inserts 500 logs per transaction (2s window)
- **Connection pooling** - Reuses DB connections
- **Parallel processing** - Multiple workers consume concurrently
- **Graceful shutdown** - Completes in-flight batches

---

### 4. **Storage Layer** (PostgreSQL)

**Purpose:** Durable, queryable log storage

**Schema:**
```sql
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    level VARCHAR(20) NOT NULL,
    source VARCHAR(50) NOT NULL,
    application VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_logs_timestamp ON logs(timestamp DESC);
CREATE INDEX idx_logs_level ON logs(level);
CREATE INDEX idx_logs_source ON logs(source);
CREATE INDEX idx_logs_application ON logs(application);
CREATE INDEX idx_logs_metadata_gin ON logs USING gin(metadata);
```

**Design Decisions:**
- **JSONB for metadata** - Flexible, queryable key-value storage
- **TIMESTAMPTZ** - Timezone-aware timestamps
- **GIN index** - Fast JSONB queries
- **B-tree indexes** - Optimized filtering and sorting

---

### 5. **Real-Time Broadcasting** (Redis Pub/Sub)

**Purpose:** Notify WebSocket clients of new logs

**Flow:**

```mermaid
sequenceDiagram
    participant WP as Worker Pool
    participant DB as PostgreSQL
    participant Redis as Redis Pub/Sub
    participant WS as WebSocket Clients
    
    WP->>DB: 1. Insert logs
    activate DB
    DB-->>WP: Confirm insert
    deactivate DB
    
    WP->>Redis: 2. Publish to "new_logs" channel
    activate Redis
    
    Redis->>WS: 3. Broadcast to clients
    activate WS
    deactivate Redis
    
    WS->>WS: 4. Update UI (< 100ms)
    deactivate WS
    
    Note over WP,WS: Total latency: < 100ms
```

**Message Format:**
```json
{
  "id": 12345,
  "timestamp": "2025-11-11T16:00:00",
  "level": "ERROR",
  "source": "api-server",
  "application": "auth",
  "message": "Login failed",
  "metadata": {"user_id": 789}
}
```

---

### 6. **Parser System** (Pluggable Architecture)

**Purpose:** Multi-format log parsing with auto-detection

**Class Hierarchy:**

```mermaid
classDiagram
    class LogParser {
        <<abstract>>
        +parse(raw_log: str) LogCreate
    }
    
    class JSONParser {
        +parse(raw_log: str) LogCreate
        -_parse_json_fields()
        Note: JSON Lines, NDJSON
    }
    
    class ApacheParser {
        +parse(raw_log: str) LogCreate
        -COMMON_PATTERN: regex
        -COMBINED_PATTERN: regex
        Note: Common & Combined Log Format
    }
    
    class SyslogParser {
        +parse(raw_log: str) LogCreate
        -_parse_rfc5424()
        -_parse_rfc3164()
        Note: RFC 5424 (modern), RFC 3164 (legacy)
    }
    
    class RegexParser {
        +parse(raw_log: str) LogCreate
        -pattern: regex
        -field_mapping: dict
        Note: Custom patterns
    }
    
    LogParser <|-- JSONParser
    LogParser <|-- ApacheParser
    LogParser <|-- SyslogParser
    LogParser <|-- RegexParser
```

**Auto-Detection Flow:**

```mermaid
flowchart TD
    Start([Raw Log String]) --> Detect[detect_format]
    
    Detect --> TryJSON{Try JSON parse}
    TryJSON -->|Success| JSON[JSON Format]
    TryJSON -->|Fail| TrySyslog{Try Syslog RE}
    
    TrySyslog -->|Match| Syslog[Syslog Format]
    TrySyslog -->|No match| TryApache{Try Apache RE}
    
    TryApache -->|Match| Apache[Apache Format]
    TryApache -->|No match| TryCustom{Try Custom RE}
    
    TryCustom -->|Match| Custom[Custom Format]
    TryCustom -->|No match| Unknown[Unknown Format]
    
    JSON --> Factory[ParserFactory.parse]
    Syslog --> Factory
    Apache --> Factory
    Custom --> Factory
    Unknown --> Error[Return None]
    
    Factory --> LogCreate([LogCreate Object])
    
    style Start fill:#e6f3ff,stroke:#0066cc,stroke-width:2px,color:#000000
    style Detect fill:#fff4e6,stroke:#ff9900,stroke-width:2px,color:#000000
    style Factory fill:#e6ffe6,stroke:#00cc00,stroke-width:2px,color:#000000
    style LogCreate fill:#e6ffe6,stroke:#00cc00,stroke-width:3px,color:#000000
    style Error fill:#ffe6e6,stroke:#cc0000,stroke-width:2px,color:#000000
```

**Extensibility:**
```python
# Add custom parser
from src.parsers import get_factory, LogParser

class MyParser(LogParser):
    def parse(self, raw_log: str) -> LogCreate:
        # Custom logic
        return LogCreate(...)

# Register
factory = get_factory()
factory.add_parser(MyParser())
```

---

## Data Flow Diagrams

### Unified Async Path (Redis Queue)

```mermaid
flowchart TD
    Client[Client/Shipper] -->|1. HTTP POST /logs<br/>JSON payload| API
    
    API["FastAPI API<br/>(Uvicorn x12)<br/>⚡ 1000+ logs/sec"]
    API -->|2. Push to Redis Stream<br/>non-blocking, ~3ms return| Redis
    
    Redis["Redis Streams<br/>Queue: 'logs'"]
    Redis -->|3. Workers pull batches<br/>batch_size = 500, timeout = 2s| Workers
    
    Workers["Worker Pool<br/>(Multi-Process)<br/>3-5 processes"]
    Workers -->|4. Batch INSERT| DB
    
    DB[("PostgreSQL<br/>logs table")]
    DB -->|5. Publish event| PubSub
    
    PubSub["Redis Pub/Sub<br/>Channel: 'new_logs'"]
    PubSub -->|6. Broadcast| WS
    
    WS["WebSocket Clients<br/>Live dashboard updates"]
    
    style Client fill:#e6f3ff,stroke:#0066cc,stroke-width:2px,color:#000000
    style API fill:#e6ffe6,stroke:#00cc00,stroke-width:3px,color:#000000
    style Redis fill:#ffe6e6,stroke:#cc0000,stroke-width:2px,color:#000000
    style Workers fill:#fff4e6,stroke:#ff9900,stroke-width:2px,color:#000000
    style DB fill:#e6ffe6,stroke:#00cc00,stroke-width:3px,color:#000000
    style PubSub fill:#ffe6e6,stroke:#cc0000,stroke-width:2px,color:#000000
    style WS fill:#f0e6ff,stroke:#9900cc,stroke-width:2px,color:#000000
```

**Latency Breakdown:**
- API response: ~3ms (instant queue push)
- Queue → DB: < 2s (batch window)
- DB → WebSocket: < 100ms (pub/sub)
- **Total end-to-end: < 3 seconds**

**Benefits:**
- **High throughput**: 1000+ logs/sec
- **Low API latency**: ~3ms response time
- **Traffic spike handling**: Redis buffers bursts
- **Horizontal scalability**: Add more workers independently

---

## Scaling Strategies

### Vertical Scaling

**API Layer:**
```bash
# Increase Uvicorn workers
python run_production.py  # Uses CPU count

# Or manually:
uvicorn src.api.app:app --workers 20 --host 0.0.0.0 --port 5000
```

**Worker Pool:**
```bash
# Add more worker processes
python -m src.queue.worker_pool --workers 10
```

### Horizontal Scaling

**Add More API Servers:**

```mermaid
graph TD
    LB[Load Balancer<br/>Nginx/HAProxy]
    
    API1[API Server 1<br/>Port 5000]
    API2[API Server 2<br/>Port 5001]
    API3[API Server 3<br/>Port 5002]
    
    Redis[(Redis<br/>Shared Queue)]
    DB[(PostgreSQL<br/>Shared Database)]
    
    LB --> API1
    LB --> API2
    LB --> API3
    
    API1 --> Redis
    API2 --> Redis
    API3 --> Redis
    
    API1 --> DB
    API2 --> DB
    API3 --> DB
    
    style LB fill:#e6f3ff,stroke:#0066cc,stroke-width:3px,color:#000000
    style API1 fill:#e6ffe6,stroke:#00cc00,stroke-width:2px,color:#000000
    style API2 fill:#e6ffe6,stroke:#00cc00,stroke-width:2px,color:#000000
    style API3 fill:#e6ffe6,stroke:#00cc00,stroke-width:2px,color:#000000
    style Redis fill:#ffe6e6,stroke:#cc0000,stroke-width:3px,color:#000000
    style DB fill:#fff4e6,stroke:#ff9900,stroke-width:3px,color:#000000
```

**Add More Workers:**
```bash
# Server 1
python -m src.queue.worker_pool --workers 5

# Server 2
python -m src.queue.worker_pool --workers 5

# Both consume from the same Redis Stream
```

**Database Scaling:**
- **Read replicas** - Route dashboard queries to replicas
- **Connection pooling** - SQLAlchemy handles this automatically
- **Partitioning** - Partition logs table by timestamp


---

## Monitoring & Observability

### Built-in Metrics

**API Health:**
```bash
curl http://127.0.0.1:5000/health

{
  "status": "healthy",
  "api": "online",
  "redis": "available",
  "websocket_connections": 3,
  "version": "2.0.0"
}
```

**Queue Status:**
```bash
curl http://127.0.0.1:5000/queue/status

{
  "status": "success",
  "queue_name": "log_queue",
  "pending_messages": 1250,
  "consumer_groups": 1,
  "consumers": 3,
  "last_message_id": "1699716234567-0"
}
```

