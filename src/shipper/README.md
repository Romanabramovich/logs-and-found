# src/shipper/ - Log Shipper

Monitors log files and sends entries to the FastAPI ingestion endpoint.

## Files

- `log_shipper.py` - File monitoring and log shipping
- `log_generator.py` - Test log generator

## log_shipper.py

Watches a log file and ships new entries to the FastAPI `/logs` endpoint.

**Features:**
- Tails log files for new entries
- Parses log lines into structured format
- POSTs to FastAPI `/logs` (queued in Redis)
- Tracks file position (resume on restart)
- Batches logs locally for efficiency
- Handles API errors gracefully

**Configuration:**
```python
LogShipper(
    log_file='path/to/file.log',
    api_url='http://127.0.0.1:5000/logs',
    batch_size=50,              # Logs per local batch (default: 50)
    batch_timeout=5.0,          # Max seconds before sending partial batch (default: 5.0)
    position_save_interval=100  # Save position every N logs (default: 100)
)
```

**Usage:**
```bash
python -m src.shipper.log_shipper /path/to/logfile.log
```

## log_generator.py

Generates fake logs for testing the shipper.

**Usage:**
```bash
python -m src.shipper.log_generator
```

Creates `test_logs.log` with realistic log entries.

## Architecture

The shipper batches logs locally (default: 50), then sends each log individually to `/logs`. 
The API queues all logs in Redis, and workers batch insert them to PostgreSQL (default: 500 logs or 2s timeout).

**Flow:**
1. Shipper reads log file
2. Batches 50 logs locally
3. Sends each to `POST /logs` (3ms response)
4. API queues in Redis
5. Workers batch insert to DB

