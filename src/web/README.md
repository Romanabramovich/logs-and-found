# src/web/ - Web UI

Web interface for visualizing and filtering logs.

## Structure

```
web/
├── templates/
│   ├── base.html              # Base layout with inline CSS
│   ├── logs.html              # Main logs page
│   └── components/            # Reusable UI components
│       ├── navbar.html        # Navigation bar
│       ├── stats_cards.html   # Statistics cards
│       ├── filter_panel.html  # Filter form
│       ├── logs_table.html    # Logs table
│       └── pagination.html    # Pagination controls
```

## Components

**base.html** - Base layout with navigation and inline CSS styles

**logs.html** - Main page that composes all components

**navbar.html** - Top navigation bar

**stats_cards.html** - ERROR/WARN/INFO/DEBUG count cards

**filter_panel.html** - Filter form (level, source, application, search)

**logs_table.html** - Table displaying log entries

**pagination.html** - Previous/Next page controls

## Features

- View logs in a color-coded table
- Filter by level, source, application
- Search log messages
- Pagination for large result sets
- Statistics dashboard

## Usage

Start the Flask server:
```bash
python -m src.api.app
```

Open browser to `http://127.0.0.1:5000/`

## Adding New Components

1. Create new file in `templates/components/`
2. Include it in your page: `{% include 'components/your_component.html' %}`
3. Pass required variables from the Flask route
