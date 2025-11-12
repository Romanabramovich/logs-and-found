"""
Log Parsers Package

Provides pluggable parsers for multiple log formats:
- JSON Lines (NDJSON)
- Apache/Nginx Common/Combined Log Format
- Syslog RFC 5424
- Custom Regex patterns
"""

from .base import LogParser
from .json_parser import JSONParser
from .apache_parser import ApacheParser
from .syslog_parser import SyslogParser
from .regex_parser import RegexParser
from .parser_factory import ParserFactory, detect_format

# Singleton factory instance
_factory_instance = None

def get_factory() -> ParserFactory:
    """
    Get the singleton ParserFactory instance.
    
    Returns:
        ParserFactory: Singleton parser factory instance
    """
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = ParserFactory()
    return _factory_instance

__all__ = [
    'LogParser',
    'JSONParser',
    'ApacheParser',
    'SyslogParser',
    'RegexParser',
    'ParserFactory',
    'detect_format',
    'get_factory'
]

