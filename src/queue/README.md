# src/queue/ - Redis Message Queue

High-performance message queue for decoupling log ingestion from processing.

## Components

**redis_producer.py** - Fast writes to Redis (API uses this)

**redis_consumer.py** - Reads and processes logs from Redis

**worker_pool.py** - Manages multiple consumer workers

## Architecture

```
Flask API → Redis Producer → Redis Stream
                                ↓
                         Consumer Workers → PostgreSQL
```

## Performance

- **API latency:** <10ms (just writes to Redis)
- **Throughput:** 100k+ logs/second
- **Batch processing:** 1000 logs per INSERT
- **Horizontal scaling:** Add more workers

## Usage

**Start workers:**
```bash
python -m src.queue.worker_pool --workers 5
```

**API integration:**
```python
from src.queue.redis_producer import RedisProducer

producer = RedisProducer()
producer.enqueue(log_data)
```

