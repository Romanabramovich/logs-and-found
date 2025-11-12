# src/shipper/ - Log Shipper

Monitors log files and sends entries to the Flask API.

## Files

- `log_shipper.py` - File monitoring and log shipping
- `log_generator.py` - Test log generator

## log_shipper.py

Watches a log file and ships new entries to the API.

**Features:**
- Tails log files for new entries
- Parses log lines into structured format
- POSTs to Flask API
- Tracks file position (resume on restart)
- Handles API errors with retries

**Configuration:**
```python
LogShipper(
    log_file='path/to/file.log',
    api_url='http://localhost:5000/data/',
    batch_size=50,              # Logs per batch (default: 50)
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

## API Requirements

The high-performance shipper requires the `/data/batch` endpoint in the Flask API for bulk inserts:

```python
@app.route('/data/batch', methods=['POST'])
def insert_logs_batch():
    # Accepts array of log objects
    # Uses bulk_insert_mappings() for fast DB inserts
```

This endpoint is already implemented in `src/api/app.py`.

