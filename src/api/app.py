"""
Log Aggregation API
"""

from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from datetime import datetime
from pathlib import Path
import math
import uvicorn
import asyncio
import json
from typing import List

from ..database import get_database_engine  
from .models import Log
from .schemas import (
    LogCreate, LogFastResponse, QueueStatusResponse, ErrorResponse
)

# Initialize FastAPI app
app = FastAPI(
    title="Log Aggregation API",
    description="High-performance distributed log aggregation system",
    version="2.0.0",
    docs_url="/api/docs",  # Swagger UI at /api/docs
    redoc_url="/api/redoc"  # ReDoc at /api/redoc
)

# Redis producer for high-performance ingestion
try:
    from ..queue.redis_producer import RedisProducer
    redis_producer = RedisProducer()
    REDIS_ENABLED = True
    print("Redis producer initialized - high-performance mode enabled")
except Exception as e:
    print(f"Redis not available: {e}")
    print("  Falling back to direct database writes")
    REDIS_ENABLED = False
    redis_producer = None  

# Setup Jinja2 templates for web UI
template_dir = Path(__file__).parent.parent / 'web' / 'templates'
templates = Jinja2Templates(directory=str(template_dir))

# Mount static files (images, css, js)
static_dir = template_dir / 'images'
app.mount("/static/images", StaticFiles(directory=str(static_dir)), name="static_images")

# Database setup
engine = get_database_engine()
Session = sessionmaker(bind=engine)


# WebSocket Connection Manager
class ConnectionManager:
    """Manages WebSocket connections for real-time log streaming"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.redis_pubsub = None
        self.listener_task = None
        
    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Start Redis listener if not already running
        if REDIS_ENABLED and self.listener_task is None:
            self.listener_task = asyncio.create_task(self._listen_to_redis())
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        if not self.active_connections:
            return
        
        # Convert to JSON
        json_message = json.dumps(message)
        
        # Send to all connections
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json_message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def _listen_to_redis(self):
        """Listen to Redis pub/sub for new logs"""
        if not REDIS_ENABLED:
            return
        
        try:
            import redis.asyncio as aioredis
            
            # Create async Redis client
            redis_client = await aioredis.from_url(
                redis_producer.redis_url,
                decode_responses=True
            )
            
            # Subscribe to log channel
            pubsub = redis_client.pubsub()
            await pubsub.subscribe('new_logs')
            
            print("WebSocket: Listening to Redis pub/sub channel 'new_logs'")
            
            # Listen for messages
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        log_data = json.loads(message['data'])
                        await self.broadcast(log_data)
                    except Exception as e:
                        print(f"Error processing Redis message: {e}")
        
        except Exception as e:
            print(f"Redis pub/sub listener error: {e}")
            self.listener_task = None


# Initialize WebSocket manager
ws_manager = ConnectionManager()


@app.get("/", response_class=HTMLResponse, tags=["Web UI"])
async def index(
    request: Request,
    level: str = Query("", description="Filter by log level"),
    source: str = Query("", description="Filter by source"),
    application: str = Query("", description="Filter by application"),
    search: str = Query("", description="Search in message"),
    page: int = Query(1, ge=1, description="Page number")
):
   
    session = Session()
    
    try:
        per_page = 25
        
        # Build query with filters
        query = session.query(Log)
        
        if level:
            query = query.filter(Log.level == level)
        if source:
            query = query.filter(Log.source == source)
        if application:
            query = query.filter(Log.application == application)
        if search:
            query = query.filter(Log.message.ilike(f'%{search}%'))
        
        # Get total count
        total = query.count()
        
        # Calculate total pages
        total_pages = math.ceil(total / per_page) if total > 0 else 1
        
        # Get logs for current page (most recent first)
        logs = query.order_by(Log.timestamp.desc()) \
                   .limit(per_page) \
                   .offset((page - 1) * per_page) \
                   .all()
        
        # Get stats (count by level)
        stats = dict(session.query(Log.level, func.count(Log.id))
                           .group_by(Log.level)
                           .all())
        
        # Get unique sources and applications for dropdowns
        sources = [s[0] for s in session.query(Log.source).distinct().all()]
        applications = [a[0] for a in session.query(Log.application).distinct().all()]
        
        return templates.TemplateResponse(
            "logs.html",
            {
                "request": request,
                "logs": logs,
                "stats": stats,
                "sources": sorted(sources),
                "applications": sorted(applications),
                "filters": {
                    'level': level, 
                    'source': source, 
                    'application': application, 
                    'search': search
                },
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages
            }
        )
    
    finally:
        session.close()


@app.post(
    "/logs", 
    response_model=LogFastResponse,
    status_code=202,
    tags=["Log Ingestion"],
    summary="Log ingestion via Redis queue",
    responses={
        202: {"description": "Log queued for processing"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Server error"},
        503: {"model": ErrorResponse, "description": "Redis unavailable"}
    }
)
async def insert_log(log: LogCreate):
    """
    **High-performance log ingestion using Redis queue.**
    
    All logs are processed asynchronously via Redis Stream.
    Workers batch insert logs to PostgreSQL for optimal throughput.
    """
    if not REDIS_ENABLED:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        # Convert Pydantic model to dict for Redis
        log_data = log.model_dump()
        
        # Enqueue to Redis (fast!)
        message_id = redis_producer.enqueue(log_data)
        
        return LogFastResponse(
            status="success",
            message_id=message_id.decode() if isinstance(message_id, bytes) else str(message_id),
            message="Log queued for processing"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Queue error: {str(e)}")


@app.get(
    "/queue/status", 
    response_model=QueueStatusResponse,
    tags=["Queue Management"],
    summary="Get Redis queue status"
)
async def queue_status():
    """
    **Check Redis queue status.**
    
    Returns:
    - Queue length (pending messages)
    - Number of consumer groups
    - Total messages sent since startup
    """
    if not REDIS_ENABLED:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        info = redis_producer.get_stream_info()
        return QueueStatusResponse(
            status="success",
            queue_length=info['length'],
            consumer_groups=info['groups'],
            messages_sent=redis_producer.messages_sent
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", tags=["System"])
async def health_check():
    """
    **Health check endpoint.**
    
    Returns API status and component availability.
    """
    return {
        "status": "healthy",
        "api": "online",
        "redis": "available" if REDIS_ENABLED else "unavailable",
        "websocket_connections": len(ws_manager.active_connections),
        "version": "2.0.0"
    }


# Parser endpoints
from ..parsers import get_factory, detect_format

parser_factory = get_factory()


@app.post("/parse/auto", tags=["Log Parsing"], summary="Auto-detect and parse log")
async def parse_log_auto(raw_log: str = Body(..., embed=True)):
    """
    **Auto-detect log format and parse.**
    
    Automatically detects the log format (JSON, Syslog, Apache, etc.) and parses it.
    
    **Example:**
    ```bash
    curl -X POST http://127.0.0.1:5000/parse/auto \\
      -H "Content-Type: application/json" \\
      -d '{"raw_log": "192.168.1.1 - - [11/Nov/2025:16:00:00 +0000] \\"GET /api/health HTTP/1.1\\" 200 45"}'
    ```
    """
    try:
        # Detect format
        detected_format = detect_format(raw_log)
        
        if not detected_format:
            return {
                "status": "error",
                "message": "Could not detect log format",
                "detected_format": None
            }
        
        # Parse
        parsed = parser_factory.parse(raw_log)
        
        if not parsed:
            return {
                "status": "error",
                "message": "Parsing failed",
                "detected_format": detected_format
            }
        
        return {
            "status": "success",
            "detected_format": detected_format,
            "parsed_log": parsed
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/parse/formats", tags=["Log Parsing"], summary="List supported formats")
async def list_formats():
    """
    **List all supported log formats.**
    
    Returns a list of all parsers including standard and custom ones.
    """
    return {
        "status": "success",
        "formats": parser_factory.list_parsers()
    }


@app.get("/parse/patterns", tags=["Log Parsing"], summary="Get predefined regex patterns")
async def get_patterns():
    """
    Get predefined regex patterns.
    Returns a list of predefined regex patterns that can be used for custom parsing.
    """
    return {
        "status": "success",
        "patterns": parser_factory.get_predefined_patterns()
    }


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """
    WebSocket endpoint for real-time log streaming.
    Connect to this endpoint to receive new logs in real-time as they're processed.
    """
    await ws_manager.connect(websocket)
    
    try:
        # Keep connection alive and handle client messages
        while True:
            # Wait for any message from client (ping/pong)
            data = await websocket.receive_text()
            
            # Echo back for ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        print("Client disconnected normally")
    except Exception as e:
        print(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


if __name__ == "__main__":
    print("=" * 60)
    print("Starting Log Aggregation API (FastAPI + Uvicorn)")
    print("=" * 60)
    print("API:      http://127.0.0.1:5000")
    print("Docs:     http://127.0.0.1:5000/api/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
