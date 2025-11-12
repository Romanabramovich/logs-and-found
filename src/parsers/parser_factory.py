"""
Parser Factory

Manages parser instances and provides auto-detection of log formats.
"""

from typing import Dict, Any, Optional, List
from .base import LogParser
from .json_parser import JSONParser
from .apache_parser import ApacheParser
from .syslog_parser import SyslogParser
from .regex_parser import RegexParser, PREDEFINED_PATTERNS


class ParserFactory:
    """
    Factory for creating and managing log parsers.
    
    Provides auto-detection and manual selection of parsers.
    """
    
    def __init__(self):
        """Initialize factory with all available parsers"""
        self.parsers: List[LogParser] = [
            JSONParser(),
            ApacheParser(),
            SyslogParser(),
        ]
        
        # Custom regex parsers (can be added by users)
        self.custom_parsers: Dict[str, RegexParser] = {}
    
    def parse(self, raw_log: str, parser_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Parse a raw log string.
        
        Args:
            raw_log: Raw log string to parse
            parser_name: Optional parser name to use (auto-detects if None)
            
        Returns:
            Parsed log dictionary or None if parsing fails
        """
        if parser_name:
            # Use specific parser
            parser = self.get_parser(parser_name)
            if parser:
                return parser.parse(raw_log)
            return None
        
        # Auto-detect and parse
        return self.auto_parse(raw_log)
    
    def auto_parse(self, raw_log: str) -> Optional[Dict[str, Any]]:
        """
        Auto-detect format and parse log.
        
        Args:
            raw_log: Raw log string to parse
            
        Returns:
            Parsed log dictionary or None if no parser can handle it
        """
        # Try each parser in order (most specific first)
        for parser in self.parsers:
            if parser.can_parse(raw_log):
                result = parser.parse(raw_log)
                if result:
                    # Add parser info to metadata
                    result['metadata']['parser'] = parser.name
                    return result
        
        # Try custom parsers
        for name, parser in self.custom_parsers.items():
            if parser.can_parse(raw_log):
                result = parser.parse(raw_log)
                if result:
                    result['metadata']['parser'] = f'custom:{name}'
                    return result
        
        return None
    
    def detect_format(self, raw_log: str) -> Optional[str]:
        """
        Detect the format of a raw log without parsing.
        
        Args:
            raw_log: Raw log string to detect
            
        Returns:
            Parser name that can handle this format, or None
        """
        for parser in self.parsers:
            if parser.can_parse(raw_log):
                return parser.name
        
        for name, parser in self.custom_parsers.items():
            if parser.can_parse(raw_log):
                return f'custom:{name}'
        
        return None
    
    def get_parser(self, name: str) -> Optional[LogParser]:
        """
        Get a specific parser by name.
        
        Args:
            name: Parser name
            
        Returns:
            Parser instance or None if not found
        """
        # Check standard parsers
        for parser in self.parsers:
            if parser.name.lower() == name.lower():
                return parser
        
        # Remove custom prefix from parsers
        if name.startswith('custom:'):
            custom_name = name[7:]
            return self.custom_parsers.get(custom_name)
        
        return None
    
    def add_custom_parser(self, name: str, pattern: str) -> bool:
        """
        Add a custom regex parser.
        
        Args:
            name: Unique name for this parser
            pattern: Regex pattern with named groups
            
        Returns:
            True if added successfully, False on error
        """
        try:
            parser = RegexParser(pattern, f"Custom: {name}")
            
            # Validate pattern
            is_valid, issues = parser.validate_pattern()
            if not is_valid:
                print(f"Invalid pattern: {', '.join(issues)}")
                return False
            
            self.custom_parsers[name] = parser
            return True
        
        except Exception as e:
            print(f"Error adding custom parser: {e}")
            return False
    
    def remove_custom_parser(self, name: str) -> bool:
        """
        Remove a custom parser.
        
        Args:
            name: Name of custom parser to remove
            
        Returns:
            True if removed, False if not found
        """
        if name in self.custom_parsers:
            del self.custom_parsers[name]
            return True
        return False
    
    def list_parsers(self) -> List[Dict[str, str]]:
        """
        List all available parsers.
        
        Returns:
            List of parser info dictionaries
        """
        parsers_info = []
        
        # Standard parsers
        for parser in self.parsers:
            parsers_info.append({
                'name': parser.name,
                'type': 'standard'
            })
        
        # Custom parsers
        for name, parser in self.custom_parsers.items():
            parsers_info.append({
                'name': f'custom:{name}',
                'type': 'custom',
                'pattern': parser.pattern_str
            })
        
        return parsers_info
    
    def get_predefined_patterns(self) -> Dict[str, Dict[str, str]]:
        """
        Get predefined regex patterns that users can use.
        
        Returns:
            Dictionary of pattern definitions
        """
        return PREDEFINED_PATTERNS


# Global factory instance
_factory = None


def get_factory() -> ParserFactory:
    """Get global parser factory instance"""
    global _factory
    if _factory is None:
        _factory = ParserFactory()
    return _factory


def detect_format(raw_log: str) -> Optional[str]:
    """Convenience function to detect log format"""
    return get_factory().detect_format(raw_log)


def parse_log(raw_log: str, parser_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Convenience function to parse log"""
    return get_factory().parse(raw_log, parser_name)

