## Log Parser System - Complete Guide

# 🎯 Overview

Your log aggregation system now supports **multiple log formats** with automatic detection!

## Supported Formats

### ✅ Built-in Parsers

1. **JSON Lines (NDJSON)**

   - Modern microservices, Docker, Kubernetes
   - Example: `{"timestamp":"2025-11-11T16:00:00","level":"INFO","message":"User logged in"}`

2. **Apache/Nginx Common & Combined Log Format**

   - Web servers, proxies, CDNs
   - Example: `192.168.1.1 - - [11/Nov/2025:16:00:00 +0000] "GET /api HTTP/1.1" 200 45`

3. **Syslog RFC 5424 & RFC 3164**

   - Linux systems, network devices, routers
   - Example: `<34>1 2025-11-11T16:00:00Z server1 app 123 - - System event`

4. **Custom Regex Patterns**
   - Flexible parser for any format
   - User-defined patterns with named groups

---

## 🚀 Quick Start

### Test Parsers Locally

```bash
cd src/tests
python test_parsers.py
```

This runs comprehensive tests on all parsers with sample logs.

### Use Parser API

#### 1. Start the API (if not running)

```bash
python run_production.py
```

#### 2. List Supported Formats

```bash
curl http://127.0.0.1:5000/parse/formats
```

**Response:**

```json
{
  "status": "success",
  "formats": [
    { "name": "JSON Lines", "type": "standard" },
    { "name": "Apache/Nginx", "type": "standard" },
    { "name": "Syslog RFC 5424", "type": "standard" }
  ]
}
```

#### 3. Auto-Parse a Log

```bash
curl -X POST http://127.0.0.1:5000/parse/auto \
  -H "Content-Type: application/json" \
  -d '"192.168.1.1 - - [11/Nov/2025:16:00:00 +0000] \"GET /api/health HTTP/1.1\" 200 45"'
```

**Response:**

```json
{
  "status": "success",
  "detected_format": "Apache/Nginx",
  "parsed_log": {
    "timestamp": "2025-11-11T16:00:00",
    "level": "INFO",
    "source": "192.168.1.1",
    "application": "web-server",
    "message": "GET /api/health 200 45",
    "metadata": {
      "ip": "192.168.1.1",
      "method": "GET",
      "path": "/api/health",
      "status_code": 200,
      "response_size": "45"
    }
  }
}
```

---

## 📋 Format-Specific Examples

### JSON Lines

**Input:**

```json
{
  "timestamp": "2025-11-11T16:00:00",
  "level": "INFO",
  "source": "api",
  "application": "web-service",
  "message": "Request processed"
}
```

**Parsed:**

- Timestamp: `2025-11-11T16:00:00`
- Level: `INFO`
- Source: `api`
- Application: `web-service`
- Message: `Request processed`

**Field Mapping:**
The JSON parser recognizes multiple field name variations:

- Timestamp: `timestamp`, `time`, `@timestamp`, `ts`, `datetime`
- Level: `level`, `severity`, `loglevel`, `log_level`
- Source: `source`, `host`, `hostname`, `server`
- Application: `application`, `app`, `service`, `component`
- Message: `message`, `msg`, `text`, `log`

### Apache/Nginx

**Common Format:**

```
192.168.1.1 - frank [11/Nov/2025:16:00:00 +0000] "GET /api/users HTTP/1.1" 200 2326
```

**Combined Format (with referrer and user agent):**

```
192.168.1.1 - - [11/Nov/2025:16:00:00 +0000] "GET /api HTTP/1.1" 200 123 "http://example.com" "Mozilla/5.0"
```

**Parsed Fields:**

- Automatic level mapping based on HTTP status:
  - 2xx, 3xx → INFO
  - 4xx → WARN
  - 5xx → ERROR
- Extracts: IP, method, path, status code, response size, referrer, user agent

### Syslog

**RFC 5424 (Modern):**

```
<34>1 2025-11-11T16:00:00.000Z server1 myapp 1234 ID47 [exampleSDID@32473 iut="3"] Event occurred
```

**RFC 3164 (Legacy):**

```
<13>Nov 11 16:00:00 server1 sshd[1234]: Failed login attempt from 192.168.1.1
```

**Parsed Fields:**

- Priority decoded into facility and severity
- Automatic level mapping from syslog severity:
  - 0-2 → CRITICAL
  - 3 → ERROR
  - 4 → WARN
  - 5-6 → INFO
  - 7 → DEBUG

### Custom Regex

**Pattern:**

```regex
(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}) \[(?P<level>\w+)\] (?P<source>\S+) - (?P<message>.+)
```

**Matches:**

```
2025-11-11T16:00:00 [INFO] web-server - Request processed successfully
```

**Required Groups:**

- `message` - The log message (required)

**Optional Groups:**

- `timestamp` - Timestamp string
- `level` - Log level
- `source` - Source/hostname
- `application` - Application name

**Any additional captured groups go into `metadata`.**

---

## 🔧 Custom Regex Patterns

### Predefined Patterns

Get predefined patterns:

```bash
curl http://127.0.0.1:5000/parse/patterns
```

**Available patterns:**

- `simple` - Basic format with timestamp, level, message
- `with_source` - Includes source/hostname
- `java_style` - Log4j style logs
- `python_style` - Python logging module format

### Create Your Own Pattern

#### Pattern Guidelines:

1. **Use named groups** with `(?P<name>...)` syntax
2. **Required groups:**

   - `message` - The actual log message

3. **Optional but recommended:**

   - `timestamp` - Timestamp string
   - `level` - Log level (INFO, ERROR, etc.)
   - `source` - Source/hostname
   - `application` - Application/service name

4. **Example:**

   ```regex
   (?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(?P<level>\w+)\] (?P<application>[^\:]+): (?P<message>.+)
   ```

   Matches:

   ```
   2025-11-11 16:00:00 [INFO] MyApp: User authentication successful
   ```

---

## 🎯 Integration with Log Ingestion

### Option 1: Parse Then Ingest

Parse a log first, then send to `/logs`:

```python
import requests

# Step 1: Parse the log
raw_log = '192.168.1.1 - - [11/Nov/2025:16:00:00 +0000] "GET /api HTTP/1.1" 200 123'

response = requests.post('http://127.0.0.1:5000/parse/auto', json=raw_log)
parsed = response.json()['parsed_log']

# Step 2: Send to fast ingestion
requests.post('http://127.0.0.1:5000/logs', json=parsed)
```

### Option 2: Future Enhancement

In the future, we can add a `/parse-and-ingest` endpoint that:

1. Auto-detects format
2. Parses the log
3. Sends to Redis queue
4. Returns immediately

---

## 🧪 Testing

### Unit Tests

```bash
python src/tests/test_parsers.py
```

### API Tests

```bash
# Test JSON
curl -X POST http://127.0.0.1:5000/parse/auto \
  -H "Content-Type: application/json" \
  -d '"{\"timestamp\":\"2025-11-11T16:00:00\",\"level\":\"INFO\",\"message\":\"Test\"}"'

# Test Apache
curl -X POST http://127.0.0.1:5000/parse/auto \
  -H "Content-Type: application/json" \
  -d '"192.168.1.1 - - [11/Nov/2025:16:00:00 +0000] \"GET /test HTTP/1.1\" 200 123"'

# Test Syslog
curl -X POST http://127.0.0.1:5000/parse/auto \
  -H "Content-Type: application/json" \
  -d '"<34>1 2025-11-11T16:00:00Z server1 app 123 - - Test message"'
```
