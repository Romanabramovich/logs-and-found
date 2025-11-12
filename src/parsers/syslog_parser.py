"""
Syslog RFC 5424 Parser

Parses syslog messages according to RFC 5424 standard.
Used by Linux systems, network devices, routers, and firewalls.

Format: <PRI>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID [STRUCTURED-DATA] MSG

Example:
<34>1 2025-11-11T16:00:00.000Z server1 app 1234 ID47 [exampleSDID@32473 iut="3" eventSource="Application"] An application event occurred
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime
from .base import LogParser


class SyslogParser(LogParser):
    """
    Parser for Syslog RFC 5424 format.
    """
    
    # RFC 5424 syslog pattern
    RFC5424_PATTERN = re.compile(
        r'<(?P<pri>\d+)>'  # Priority
        r'(?P<version>\d+)\s+'  # Version
        r'(?P<timestamp>\S+)\s+'  # Timestamp
        r'(?P<hostname>\S+)\s+'  # Hostname
        r'(?P<appname>\S+)\s+'  # Application name
        r'(?P<procid>\S+)\s+'  # Process ID
        r'(?P<msgid>\S+)\s+'  # Message ID
        r'(?P<structured>(?:\[.*?\]|-)+)\s*'  # Structured data
        r'(?P<message>.*)$'  # Message
    )
    
    # Legacy RFC 3164 pattern (for backwards compatibility)
    RFC3164_PATTERN = re.compile(
        r'<(?P<pri>\d+)>'  # Priority
        r'(?P<timestamp>\w+\s+\d+\s+\d+:\d+:\d+)\s+'  # Timestamp
        r'(?P<hostname>\S+)\s+'  # Hostname
        r'(?P<tag>[^\[:]+)(?:\[(?P<procid>\d+)\])?:\s*'  # Tag and PID
        r'(?P<message>.*)$'  # Message
    )
    
    # Severity levels (from syslog spec)
    SEVERITIES = {
        0: 'CRITICAL',  # Emergency
        1: 'CRITICAL',  # Alert
        2: 'CRITICAL',  # Critical
        3: 'ERROR',     # Error
        4: 'WARN',      # Warning
        5: 'INFO',      # Notice
        6: 'INFO',      # Informational
        7: 'DEBUG'      # Debug
    }
    
    # Facilities (for metadata)
    FACILITIES = {
        0: 'kern', 1: 'user', 2: 'mail', 3: 'daemon',
        4: 'auth', 5: 'syslog', 6: 'lpr', 7: 'news',
        8: 'uucp', 9: 'cron', 10: 'authpriv', 11: 'ftp',
        16: 'local0', 17: 'local1', 18: 'local2', 19: 'local3',
        20: 'local4', 21: 'local5', 22: 'local6', 23: 'local7'
    }
    
    def __init__(self):
        super().__init__("Syslog RFC 5424")
    
    def can_parse(self, raw_log: str) -> bool:
        """Check if log matches syslog format"""
        # Check for syslog priority at start
        return raw_log.strip().startswith('<') and '>' in raw_log[:10]
    
    def parse(self, raw_log: str) -> Optional[Dict[str, Any]]:
        """
        Parse syslog message into structured format.
        
        Supports both RFC 5424 and RFC 3164 (legacy) formats.
        """
        try:
            # Try RFC 5424 first
            match = self.RFC5424_PATTERN.match(raw_log.strip())
            
            if match:
                return self._parse_rfc5424(match)
            
            # Try legacy RFC 3164
            match = self.RFC3164_PATTERN.match(raw_log.strip())
            
            if match:
                return self._parse_rfc3164(match)
            
            return None
            
        except Exception as e:
            print(f"Syslog parsing error: {e}")
            return None
    
    def _parse_rfc5424(self, match) -> Dict[str, Any]:
        """Parse RFC 5424 format"""
        data = match.groupdict()
        
        # Parse priority to get facility and severity
        pri = int(data['pri'])
        facility = pri // 8
        severity = pri % 8
        
        # Parse timestamp
        timestamp = self._parse_syslog_timestamp(data['timestamp'])
        
        # Build metadata
        metadata = {
            'facility': self.FACILITIES.get(facility, f'unknown({facility})'),
            'severity': severity,
            'version': data['version'],
            'procid': data['procid'] if data['procid'] != '-' else None,
            'msgid': data['msgid'] if data['msgid'] != '-' else None,
        }
        
        # Parse structured data if present
        if data['structured'] != '-':
            metadata['structured_data'] = data['structured']
        
        return {
            'timestamp': timestamp,
            'level': self.SEVERITIES.get(severity, 'INFO'),
            'source': data['hostname'] if data['hostname'] != '-' else 'unknown',
            'application': data['appname'] if data['appname'] != '-' else 'syslog',
            'message': data['message'].strip(),
            'metadata': metadata
        }
    
    def _parse_rfc3164(self, match) -> Dict[str, Any]:
        """Parse legacy RFC 3164 format"""
        data = match.groupdict()
        
        # Parse priority
        pri = int(data['pri'])
        facility = pri // 8
        severity = pri % 8
        
        # Parse timestamp (format: Nov 11 16:00:00)
        timestamp = self._parse_legacy_timestamp(data['timestamp'])
        
        # Build metadata
        metadata = {
            'facility': self.FACILITIES.get(facility, f'unknown({facility})'),
            'severity': severity,
            'procid': data.get('procid', None),
        }
        
        return {
            'timestamp': timestamp,
            'level': self.SEVERITIES.get(severity, 'INFO'),
            'source': data['hostname'],
            'application': data['tag'],
            'message': data['message'].strip(),
            'metadata': metadata
        }
    
    def _parse_syslog_timestamp(self, timestamp_str: str) -> str:
        """Parse RFC 5424 timestamp (ISO 8601)"""
        try:
            if timestamp_str == '-':
                return datetime.now().isoformat()
            
            # Remove timezone info for simplicity (or handle properly)
            clean_ts = timestamp_str.replace('Z', '').split('+')[0].split('-', 3)[:3]
            clean_ts = '-'.join(clean_ts)
            
            # Parse ISO format
            if '.' in clean_ts:
                dt = datetime.strptime(clean_ts.split('.')[0], '%Y-%m-%dT%H:%M:%S')
            else:
                dt = datetime.strptime(clean_ts, '%Y-%m-%dT%H:%M:%S')
            
            return dt.isoformat()
        except Exception:
            return datetime.now().isoformat()
    
    def _parse_legacy_timestamp(self, timestamp_str: str) -> str:
        """Parse RFC 3164 timestamp (Nov 11 16:00:00)"""
        try:
            # Add current year since legacy format doesn't include it
            current_year = datetime.now().year
            full_timestamp = f"{timestamp_str} {current_year}"
            dt = datetime.strptime(full_timestamp, '%b %d %H:%M:%S %Y')
            return dt.isoformat()
        except Exception:
            return datetime.now().isoformat()

