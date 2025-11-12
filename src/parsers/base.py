"""
Base Log Parser Interface

All parsers must implement this interface for consistency.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class LogParser(ABC):
    """
    Abstract base class for log parsers.
    
    All parsers must implement the parse() method to convert
    raw log strings into structured dictionaries.
    """
    
    def __init__(self, name: str):
        """
        Initialize parser.
        
        Args:
            name: Parser name for identification
        """
        self.name = name
    
    @abstractmethod
    def parse(self, raw_log: str) -> Optional[Dict[str, Any]]:
        """
        Parse a raw log string into structured data.
        
        Args:
            raw_log: Raw log string to parse
            
        Returns:
            Dictionary with parsed fields or None if parsing fails:
            {
                'timestamp': str (ISO format),
                'level': str (INFO, WARN, ERROR, DEBUG, etc.),
                'source': str,
                'application': str,
                'message': str,
                'metadata': dict (optional additional fields)
            }
        """
        pass
    
    @abstractmethod
    def can_parse(self, raw_log: str) -> bool:
        """
        Check if this parser can handle the given log format.
        
        Args:
            raw_log: Raw log string to check
            
        Returns:
            True if parser can handle this format, False otherwise
        """
        pass
    
    def normalize_level(self, level: str) -> str:
        """
        Normalize log level to standard format.
        
        Args:
            level: Raw log level string
            
        Returns:
            Normalized level (INFO, WARN, ERROR, DEBUG, CRITICAL)
        """
        level_upper = level.upper()
        
        # Map common variants
        level_map = {
            'WARNING': 'WARN',
            'FATAL': 'CRITICAL',
            'CRIT': 'CRITICAL',
            'ERR': 'ERROR',
            'NOTICE': 'INFO',
            'TRACE': 'DEBUG'
        }
        
        return level_map.get(level_upper, level_upper)
    
    def parse_timestamp(self, timestamp_str: str, formats: list = None) -> str:
        """
        Parse timestamp string to ISO format.
        
        Args:
            timestamp_str: Timestamp string to parse
            formats: List of datetime format strings to try
            
        Returns:
            ISO format timestamp string
        """
        if formats is None:
            # Common timestamp formats
            formats = [
                '%Y-%m-%dT%H:%M:%S',  # ISO format
                '%Y-%m-%d %H:%M:%S',  # Standard format
                '%d/%b/%Y:%H:%M:%S',  # Apache format
                '%b %d %H:%M:%S',     # Syslog format
                '%Y-%m-%dT%H:%M:%S.%f',  # ISO with microseconds
                '%Y-%m-%dT%H:%M:%S%z',   # ISO with timezone
            ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp_str.strip(), fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        # If all parsing fails, return current time
        return datetime.now().isoformat()
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"

