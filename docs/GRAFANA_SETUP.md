# Grafana Integration Guide

Integrate your log aggregation system with Grafana for professional dashboards and alerting.

## Why Grafana?

- Industry-standard observability platform
- Real-time dashboards with auto-refresh
- Advanced querying and filtering
- Alerting (email, Slack, PagerDuty)
- Time-series visualizations
- Multiple dashboard views

## Prerequisites

- Log aggregation system running (Flask API + PostgreSQL)
- Docker installed (recommended) OR Grafana installed locally

## Installation

### Option 1: Docker (Recommended)

```bash
# Run Grafana in Docker
docker run -d \
  -p 3000:3000 \
  --name grafana \
  grafana/grafana-oss:latest
```

### Option 2: Local Installation

**Windows:**
```bash
# Download from grafana.com/grafana/download
# Or use Chocolatey:
choco install grafana
```

**Mac:**
```bash
brew install grafana
```

**Linux:**
```bash
sudo apt-get install -y grafana
```

## Configure PostgreSQL Data Source

1. **Access Grafana:**
   - Open `http://localhost:3000`
   - Default login: `admin` / `admin`
   - Change password when prompted

2. **Add PostgreSQL Data Source:**
   - Go to: Configuration → Data Sources → Add data source
   - Select "PostgreSQL"
   - Configure:
     ```
     Name: LogAggregation
     Host: localhost:5433
     Database: log_aggregation
     User: log_user
     Password: log_password
     SSL Mode: disable (for local dev)
     ```
   - Click "Save & Test" (should show green checkmark)

## Create Dashboards

### Dashboard 1: Overview Dashboard

**Panels to create:**

1. **Total Logs (Stat Panel)**
   - Query: `SELECT COUNT(*) FROM logs`
   - Shows total log count

2. **Logs by Level (Pie Chart)**
   - Query:
     ```sql
     SELECT 
       level as metric,
       COUNT(*) as value
     FROM logs
     GROUP BY level
     ```

3. **Logs Over Time (Time Series)**
   - Query:
     ```sql
     SELECT 
       $__timeGroup(timestamp, '5m') as time,
       level,
       COUNT(*) as count
     FROM logs
     WHERE $__timeFilter(timestamp)
     GROUP BY time, level
     ORDER BY time
     ```

4. **Error Rate (Gauge)**
   - Query:
     ```sql
     SELECT 
       (COUNT(*) FILTER (WHERE level='ERROR') * 100.0 / COUNT(*)) as error_rate
     FROM logs
     WHERE timestamp > NOW() - INTERVAL '1 hour'
     ```

5. **Recent Logs (Table)**
   - Query:
     ```sql
     SELECT 
       timestamp,
       level,
       source,
       application,
       message
     FROM logs
     ORDER BY timestamp DESC
     LIMIT 100
     ```

### Dashboard 2: Error Tracking

1. **Error Count Over Time**
   ```sql
   SELECT 
     $__timeGroup(timestamp, '1m') as time,
     COUNT(*) as errors
   FROM logs
   WHERE level = 'ERROR' AND $__timeFilter(timestamp)
   GROUP BY time
   ORDER BY time
   ```

2. **Top Error Messages**
   ```sql
   SELECT 
     message,
     COUNT(*) as count
   FROM logs
   WHERE level = 'ERROR' AND timestamp > NOW() - INTERVAL '1 hour'
   GROUP BY message
   ORDER BY count DESC
   LIMIT 10
   ```

3. **Errors by Source**
   ```sql
   SELECT 
     source,
     COUNT(*) as error_count
   FROM logs
   WHERE level = 'ERROR' AND timestamp > NOW() - INTERVAL '24 hours'
   GROUP BY source
   ORDER BY error_count DESC
   ```

### Dashboard 3: Per-Service View

1. **Service Selector (Variable)**
   - Name: `service`
   - Query: `SELECT DISTINCT source FROM logs ORDER BY source`
   - Multi-value: enabled

2. **Service Logs**
   ```sql
   SELECT 
     timestamp,
     level,
     application,
     message
   FROM logs
   WHERE source = '$service' AND $__timeFilter(timestamp)
   ORDER BY timestamp DESC
   LIMIT 100
   ```

## Configure Alerts

### Alert 1: High Error Rate

**Condition:** More than 10 errors in 5 minutes

1. Create alert in panel
2. Query:
   ```sql
   SELECT COUNT(*) as errors
   FROM logs
   WHERE level = 'ERROR' 
     AND timestamp > NOW() - INTERVAL '5 minutes'
   ```
3. Condition: `errors > 10`
4. Notification channel: Email/Slack

### Alert 2: Service Down

**Condition:** No logs from a service in 10 minutes

```sql
SELECT 
  source,
  MAX(timestamp) as last_seen
FROM logs
GROUP BY source
HAVING MAX(timestamp) < NOW() - INTERVAL '10 minutes'
```

## Advanced Features

### Log Drill-Down

Add data links to navigate from dashboard to log details:

```
URL: http://localhost:5000/?source=${__data.fields.source}&level=ERROR
```

### Time Range Selector

Grafana automatically adds time range controls:
- Last 5 minutes
- Last 1 hour
- Last 24 hours
- Custom range

### Auto-Refresh

Set dashboard to auto-refresh every 5 seconds for real-time monitoring.

### Annotations

Mark deployments or incidents on graphs:

```sql
SELECT 
  timestamp as time,
  'Deployment' as text,
  message as tags
FROM logs
WHERE message LIKE '%deployed%'
```

## Dashboard JSON Export

Once you create dashboards, export them as JSON:
- Dashboard settings → JSON Model → Copy
- Save to `docs/grafana/dashboards/`
- Share with team or version control

## Best Practices

1. **Use variables** for dynamic filtering (service, level, time range)
2. **Create dashboard folders** (Overview, Errors, Per-Service)
3. **Set appropriate refresh intervals** (5s for live, 1m for historical)
4. **Configure retention** in PostgreSQL (old logs impact query performance)
5. **Use Grafana alerting** instead of building custom alerts

## Comparison: Custom UI vs Grafana

| Feature | Custom Flask UI | Grafana |
|---------|----------------|---------|
| Setup Time | Already built | 15 minutes |
| Time Series Graphs | No | Yes |
| Auto-Refresh | Manual | Configurable |
| Alerting | Custom code | Built-in |
| Mobile | Basic | Optimized |
| Learning Curve | Your code | Standard tool |
| Resume Value | Shows you can build | Shows you know tools |

## Recommended Approach

**Keep both:**

1. **Flask UI** - For log ingestion API and custom features
2. **Grafana** - For visualization and monitoring

**Why?**
- Flask API: Ingestion endpoint, custom processing
- Grafana: Professional dashboards for operations team
- Shows you can build AND integrate industry tools

## Next Steps

1. Install Grafana (5 minutes)
2. Connect to PostgreSQL (5 minutes)
3. Create Overview Dashboard (15 minutes)
4. Set up error alerts (10 minutes)
5. Export dashboard JSON and save to repo

Total time: ~45 minutes to professional observability platform!

## Troubleshooting

**Connection Failed:**
- Check PostgreSQL is running: `psql -U log_user -d log_aggregation`
- Verify credentials in Grafana match your `.env`
- Check firewall allows port 5433

**Queries Slow:**
- Add indexes to frequently queried columns
- Use time range filters (`$__timeFilter(timestamp)`)
- Consider table partitioning for millions of logs

**No Data:**
- Verify logs exist: `SELECT COUNT(*) FROM logs;`
- Check time range in Grafana (top right)
- Ensure timezone matches between PostgreSQL and Grafana

