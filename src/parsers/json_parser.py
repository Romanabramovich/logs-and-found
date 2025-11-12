"""
JSON Lines (NDJSON) Parser

Parses JSON-formatted logs - one JSON object per line.
Most common format for modern microservices, Docker, and Kubernetes.
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime
from .base import LogParser


class JSONParser(LogParser):
    """
    Parser for JSON/NDJSON log format.
    
    Supports flexible field mapping for different JSON schemas.
    """
    
    def __init__(self):
        super().__init__("JSON Lines")
        
        # Common field name mappings
        self.timestamp_fields = ['timestamp', 'time', '@timestamp', 'ts', 'datetime', 'date']
        self.level_fields = ['level', 'severity', 'loglevel', 'log_level']
        self.source_fields = ['source', 'host', 'hostname', 'server', 'instance']
        self.app_fields = ['application', 'app', 'service', 'component', 'logger', 'name']
        self.message_fields = ['message', 'msg', 'text', 'log', 'event']
    
    def can_parse(self, raw_log: str) -> bool:
        """Check if log is valid JSON"""
        try:
            json.loads(raw_log.strip())
            return True
        except (json.JSONDecodeError, ValueError):
            return False
    
    def parse(self, raw_log: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON log into structured format.
        
        Example inputs:
        {"timestamp":"2025-11-11T16:00:00","level":"INFO","message":"Request received"}
        {"time":"2025-11-11 16:00:00","severity":"error","msg":"Failed to connect"}
        """
        try:
            data = json.loads(raw_log.strip())
            
            if not isinstance(data, dict):
                return None
            
            # Extract fields using flexible mapping
            parsed = {
                'timestamp': self._extract_field(data, self.timestamp_fields, 
                                                datetime.now().isoformat()),
                'level': self.normalize_level(
                    self._extract_field(data, self.level_fields, 'INFO')
                ),
                'source': self._extract_field(data, self.source_fields, 'json-log'),
                'application': self._extract_field(data, self.app_fields, 'unknown'),
                'message': self._extract_field(data, self.message_fields, str(data)),
                'metadata': {}
            }
            
            # Add remaining fields to metadata
            used_fields = set()
            for field_list in [self.timestamp_fields, self.level_fields, 
                             self.source_fields, self.app_fields, self.message_fields]:
                used_fields.update(field_list)
            
            for key, value in data.items():
                if key not in used_fields:
                    parsed['metadata'][key] = value
            
            return parsed
            
        except Exception as e:
            print(f"JSON parsing error: {e}")
            return None
    
    def _extract_field(self, data: dict, possible_keys: list, default: str) -> str:
        """
        Extract field from JSON using list of possible key names.
        
        Args:
            data: JSON data dictionary
            possible_keys: List of possible field names to check
            default: Default value if field not found
            
        Returns:
            Field value or default
        """
        for key in possible_keys:
            if key in data:
                value = data[key]
                # Convert to string if not already
                return str(value) if value is not None else default
        return default

