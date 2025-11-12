"""
Apache/Nginx Log Format Parser

Supports:
- Common Log Format (CLF)
- Combined Log Format
- Custom Nginx formats

Example formats:
Common: 127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326
Combined: 127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326 "http://example.com" "Mozilla/4.08"
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime
from .base import LogParser


class ApacheParser(LogParser):
    """
    Parser for Apache/Nginx Common and Combined Log Format.
    """
    
    # Common Log Format regex
    CLF_PATTERN = re.compile(
        r'(?P<host>[\d\.]+)\s+'  # IP address
        r'(?P<ident>\S+)\s+'      # Identity (usually -)
        r'(?P<user>\S+)\s+'       # User (usually -)
        r'\[(?P<time>[^\]]+)\]\s+'  # Timestamp
        r'"(?P<request>[^"]+)"\s+'  # Request line
        r'(?P<status>\d{3})\s+'   # Status code
        r'(?P<size>\S+)'          # Response size
    )
    
    # Combined Log Format regex (adds referrer and user agent)
    COMBINED_PATTERN = re.compile(
        r'(?P<host>[\d\.]+)\s+'
        r'(?P<ident>\S+)\s+'
        r'(?P<user>\S+)\s+'
        r'\[(?P<time>[^\]]+)\]\s+'
        r'"(?P<request>[^"]+)"\s+'
        r'(?P<status>\d{3})\s+'
        r'(?P<size>\S+)\s+'
        r'"(?P<referrer>[^"]*)"\s+'  
        r'"(?P<agent>[^"]*)"'         # User agent
    )
    
    def __init__(self):
        super().__init__("Apache/Nginx")
    
    def can_parse(self, raw_log: str) -> bool:
        """Check if log matches Apache/Nginx format"""
        return (self.COMBINED_PATTERN.match(raw_log.strip()) is not None or
                self.CLF_PATTERN.match(raw_log.strip()) is not None)
    
    def parse(self, raw_log: str) -> Optional[Dict[str, Any]]:
        """
        Parse Apache/Nginx log into structured format.
        
        Example:
        192.168.1.1 - - [11/Nov/2025:16:00:00 +0000] "GET /api/health HTTP/1.1" 200 45
        """
        try:
            # Try combined format first (more specific)
            match = self.COMBINED_PATTERN.match(raw_log.strip())
            is_combined = True
            
            if not match:
                # Fall back to common format
                match = self.CLF_PATTERN.match(raw_log.strip())
                is_combined = False
            
            if not match:
                return None
            
            data = match.groupdict()
            
            # Parse request line
            request_parts = data['request'].split()
            method = request_parts[0] if len(request_parts) > 0 else 'GET'
            path = request_parts[1] if len(request_parts) > 1 else '/'
            protocol = request_parts[2] if len(request_parts) > 2 else 'HTTP/1.0'
            
            # Parse timestamp (Apache format: 10/Oct/2000:13:55:36 -0700)
            timestamp_str = data['time']
            timestamp = self._parse_apache_timestamp(timestamp_str)
            
            # Determine log level based on status code
            status_code = int(data['status'])
            level = self._status_to_level(status_code)
            
            # Build metadata
            metadata = {
                'ip': data['host'],
                'method': method,
                'path': path,
                'protocol': protocol,
                'status_code': status_code,
                'response_size': data['size'] if data['size'] != '-' else '0',
                'user': data['user'] if data['user'] != '-' else None,
            }
            
            # Add combined format fields if available
            if is_combined:
                metadata['referrer'] = data['referrer'] if data['referrer'] != '-' else None
                metadata['user_agent'] = data['agent'] if data['agent'] != '-' else None
            
            # Build message
            message = f"{method} {path} {status_code} {data['size']}"
            
            return {
                'timestamp': timestamp,
                'level': level,
                'source': data['host'],
                'application': 'web-server',
                'message': message,
                'metadata': metadata
            }
            
        except Exception as e:
            print(f"Apache/Nginx parsing error: {e}")
            return None
    
    def _parse_apache_timestamp(self, timestamp_str: str) -> str:
        """
        Parse Apache timestamp format to ISO format.
        
        Format: 10/Oct/2000:13:55:36 -0700
        """
        try:
            # Remove timezone for simplicity
            time_part = timestamp_str.split()[0]
            dt = datetime.strptime(time_part, '%d/%b/%Y:%H:%M:%S')
            return dt.isoformat()
        except Exception:
            return datetime.now().isoformat()
    
    def _status_to_level(self, status_code: int) -> str:
        """
        Convert HTTP status code to log level.
        
        2xx = INFO
        3xx = INFO
        4xx = WARN
        5xx = ERROR
        """
        if status_code < 400:
            return 'INFO'
        elif status_code < 500:
            return 'WARN'
        else:
            return 'ERROR'

