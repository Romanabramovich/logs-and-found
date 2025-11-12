"""
Pydantic models for API request/response validation.

FastAPI uses these for:
- Automatic request validation
- Auto-generated API documentation
- Type safety
- JSON schema generation
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime


class LogCreate(BaseModel):
    """
    Schema for creating a new log entry.
    
    Used by /data/ and /data/fast endpoints.
    """
    timestamp: str = Field(..., description="ISO format timestamp")
    level: str = Field(..., description="Log level (INFO, WARN, ERROR, DEBUG)")
    source: str = Field(..., description="Log source identifier")
    application: str = Field(..., description="Application name")
    message: str = Field(..., description="Log message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata as JSON object")
    
    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v):
        """Ensure timestamp can be parsed"""
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError('timestamp must be in ISO format (YYYY-MM-DDTHH:MM:SS)')
        return v
    
    @field_validator('level')
    @classmethod
    def validate_level(cls, v):
        """Validate log level"""
        valid_levels = {'DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL'}
        if v.upper() not in valid_levels:
            raise ValueError(f'level must be one of: {", ".join(valid_levels)}')
        return v.upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-11T16:00:00",
                "level": "INFO",
                "source": "web-server",
                "application": "api",
                "message": "User login successful",
                "metadata": {"user_id": 123, "ip": "192.168.1.1"}
            }
        }


class LogBatchCreate(BaseModel):
    """
    Schema for batch log creation.
    
    Used by /data/batch endpoint.
    """
    logs: List[LogCreate] = Field(..., description="List of log entries", min_length=1, max_length=10000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "logs": [
                    {
                        "timestamp": "2025-11-11T16:00:00",
                        "level": "INFO",
                        "source": "web-server",
                        "application": "api",
                        "message": "Request received"
                    },
                    {
                        "timestamp": "2025-11-11T16:00:01",
                        "level": "INFO",
                        "source": "web-server",
                        "application": "api",
                        "message": "Request processed"
                    }
                ]
            }
        }


class LogResponse(BaseModel):
    """Standard response for successful log insertion"""
    status: str = "success"
    log_id: Optional[int] = None
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "log_id": 12345,
                "message": "Log inserted successfully"
            }
        }


class LogFastResponse(BaseModel):
    """Response for Redis queue insertion"""
    status: str = "success"
    message_id: str
    message: str = "Log queued for processing"
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message_id": "1762894896750-0",
                "message": "Log queued for processing"
            }
        }


class QueueStatusResponse(BaseModel):
    """Response for queue status endpoint"""
    status: str = "success"
    queue_length: int
    consumer_groups: int
    messages_sent: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "queue_length": 150,
                "consumer_groups": 1,
                "messages_sent": 5000
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    status: str = "error"
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "Missing required field: timestamp"
            }
        }

