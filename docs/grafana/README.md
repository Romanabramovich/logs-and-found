# Grafana Dashboards

Pre-built Grafana dashboards for the log aggregation system.

## Available Dashboards

### overview-dashboard.json
Main dashboard with:
- Total log count
- Error rate gauge
- Logs by level (pie chart)
- Time series graph
- Recent logs table

## Import Instructions

1. Open Grafana: `http://localhost:3000`
2. Go to: Dashboards → Import
3. Upload JSON file or paste contents
4. Select "LogAggregation" data source
5. Click "Import"

## Customize Dashboards

- Edit panels: Click title → Edit
- Add panels: Add panel button (top right)
- Change time range: Time picker (top right)
- Save changes: Save dashboard icon

## Query Examples

See `../GRAFANA_SETUP.md` for more SQL queries and configuration options.

