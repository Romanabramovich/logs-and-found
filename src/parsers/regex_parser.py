"""
Custom Regex Parser

Allows users to define custom regex patterns for parsing proprietary log formats.
Provides flexibility for edge cases and legacy systems.

Example pattern:
(?P<timestamp>\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}) \\[(?P<level>\\w+)\\] (?P<message>.+)
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from .base import LogParser


class RegexParser(LogParser):
    """
    Parser for custom regex-based log formats.
    Users provide a regex pattern with named groups for each field.
    """
    
    # Required named groups in user regex
    REQUIRED_GROUPS = ['message']
    
    # Optional but recommended groups
    OPTIONAL_GROUPS = ['timestamp', 'level', 'source', 'application']
    
    def __init__(self, pattern: str = None, name: str = "Custom Regex"):
        """
        Initialize custom regex parser.
        
        Args:
            pattern: Regex pattern with named groups
            name: Parser name for identification
        """
        super().__init__(name)
        self.pattern_str = pattern
        self.pattern = None
        
        if pattern:
            try:
                self.pattern = re.compile(pattern)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}")
    
    def set_pattern(self, pattern: str):
        """
        Set or update the regex pattern.
        
        Args:
            pattern: Regex pattern with named groups
        """
        try:
            self.pattern = re.compile(pattern)
            self.pattern_str = pattern
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
    
    def can_parse(self, raw_log: str) -> bool:
        """Check if log matches the custom pattern"""
        if not self.pattern:
            return False
        return self.pattern.match(raw_log.strip()) is not None
    
    def parse(self, raw_log: str) -> Optional[Dict[str, Any]]:
        """
        Parse log using custom regex pattern.
        
        Example pattern:
        (?P<timestamp>\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}) \\[(?P<level>\\w+)\\] (?P<source>\\S+) - (?P<message>.+)
        
        Example log:
        2025-11-11T16:00:00 [INFO] web-server - Request processed successfully
        """
        if not self.pattern:
            return None
        
        try:
            match = self.pattern.match(raw_log.strip())
            
            if not match:
                return None
            
            data = match.groupdict()
            
            # Ensure required fields exist
            if 'message' not in data:
                # Use entire log as message if not captured
                data['message'] = raw_log.strip()
            
            # Build parsed log with defaults
            parsed = {
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'level': self.normalize_level(data.get('level', 'INFO')),
                'source': data.get('source', 'custom-log'),
                'application': data.get('application', 'unknown'),
                'message': data['message'],
                'metadata': {}
            }
            
            # Add any extra captured groups to metadata
            standard_fields = {'timestamp', 'level', 'source', 'application', 'message'}
            for key, value in data.items():
                if key not in standard_fields and value is not None:
                    parsed['metadata'][key] = value
            
            return parsed
            
        except Exception as e:
            print(f"Custom regex parsing error: {e}")
            return None
    
    def validate_pattern(self) -> tuple[bool, List[str]]:
        """
        Validate the regex pattern.
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        if not self.pattern:
            issues.append("No pattern set")
            return False, issues
        
        # Check for named groups
        if not self.pattern.groupindex:
            issues.append("Pattern must contain at least one named group")
            return False, issues
        
        # Check for message group (most important)
        if 'message' not in self.pattern.groupindex:
            issues.append("Pattern should include 'message' named group")
        
        # Warn about missing optional groups
        missing_optional = [
            g for g in self.OPTIONAL_GROUPS 
            if g not in self.pattern.groupindex
        ]
        
        if missing_optional:
            issues.append(f"Consider adding these groups: {', '.join(missing_optional)}")
        
        return len([i for i in issues if 'must' in i]) == 0, issues
    
    def get_pattern_info(self) -> Dict[str, Any]:
        """
        Get information about the current pattern.
        
        Returns:
            Dictionary with pattern info
        """
        if not self.pattern:
            return {'pattern': None, 'groups': []}
        
        return {
            'pattern': self.pattern_str,
            'groups': list(self.pattern.groupindex.keys()),
            'required_groups_present': 'message' in self.pattern.groupindex,
            'optional_groups_present': [
                g for g in self.OPTIONAL_GROUPS 
                if g in self.pattern.groupindex
            ]
        }


# Predefined regex patterns for common formats
PREDEFINED_PATTERNS = {
    'simple': {
        'pattern': r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}) \[(?P<level>\w+)\] (?P<message>.+)',
        'description': 'Simple format: 2025-11-11T16:00:00 [INFO] message'
    },
    'with_source': {
        'pattern': r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(?P<level>\w+)\] (?P<source>\S+) - (?P<message>.+)',
        'description': 'With source: 2025-11-11 16:00:00 [INFO] app-name - message'
    },
    'java_style': {
        'pattern': r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) (?P<level>\w+)\s+\[(?P<application>[^\]]+)\] (?P<message>.+)',
        'description': 'Java/Log4j style: 2025-11-11 16:00:00,123 INFO [AppName] message'
    },
    'python_style': {
        'pattern': r'(?P<level>\w+):(?P<application>[^:]+):(?P<message>.+)',
        'description': 'Python logging: INFO:app_name:message'
    }
}

