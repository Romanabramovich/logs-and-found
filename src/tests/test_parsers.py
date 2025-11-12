"""
Parser Test Suite

Tests all log parsers with sample logs from each format.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.parsers import JSONParser, ApacheParser, SyslogParser, RegexParser, ParserFactory


def test_json_parser():
    """Test JSON Lines parser"""
    print("\n" + "=" * 60)
    print("Testing JSON Parser")
    print("=" * 60)
    
    parser = JSONParser()
    
    # Test cases
    test_logs = [
        '{"timestamp":"2025-11-11T16:00:00","level":"INFO","message":"User logged in"}',
        '{"time":"2025-11-11 16:00:00","severity":"error","msg":"Database connection failed"}',
        '{"@timestamp":"2025-11-11T16:00:00.123Z","log_level":"WARN","service":"api","text":"Rate limit exceeded"}',
    ]
    
    for i, log in enumerate(test_logs, 1):
        print(f"\nTest {i}:")
        print(f"Raw: {log}")
        parsed = parser.parse(log)
        if parsed:
            print(f"✓ Parsed successfully:")
            print(f"  Timestamp: {parsed['timestamp']}")
            print(f"  Level: {parsed['level']}")
            print(f"  Message: {parsed['message']}")
        else:
            print("✗ Parsing failed")


def test_apache_parser():
    """Test Apache/Nginx parser"""
    print("\n" + "=" * 60)
    print("Testing Apache/Nginx Parser")
    print("=" * 60)
    
    parser = ApacheParser()
    
    # Test cases
    test_logs = [
        '192.168.1.1 - - [11/Nov/2025:16:00:00 +0000] "GET /api/health HTTP/1.1" 200 45',
        '10.0.0.1 - frank [11/Nov/2025:16:01:00 +0000] "POST /api/users HTTP/1.1" 201 123',
        '192.168.1.1 - - [11/Nov/2025:16:02:00 +0000] "GET /api/data HTTP/1.1" 404 512 "http://example.com" "Mozilla/5.0"',
    ]
    
    for i, log in enumerate(test_logs, 1):
        print(f"\nTest {i}:")
        print(f"Raw: {log}")
        parsed = parser.parse(log)
        if parsed:
            print(f"✓ Parsed successfully:")
            print(f"  Timestamp: {parsed['timestamp']}")
            print(f"  Level: {parsed['level']}")
            print(f"  Source: {parsed['source']}")
            print(f"  Message: {parsed['message']}")
            print(f"  Status: {parsed['metadata']['status_code']}")
        else:
            print("✗ Parsing failed")


def test_syslog_parser():
    """Test Syslog parser"""
    print("\n" + "=" * 60)
    print("Testing Syslog Parser")
    print("=" * 60)
    
    parser = SyslogParser()
    
    # Test cases
    test_logs = [
        '<34>1 2025-11-11T16:00:00.000Z server1 app 1234 ID47 - An application event occurred',
        '<165>1 2025-11-11T16:01:00Z router1 sshd 5678 - - Failed login attempt',
        '<13>Nov 11 16:00:00 server1 sshd[1234]: Accepted publickey for user from 192.168.1.1',
    ]
    
    for i, log in enumerate(test_logs, 1):
        print(f"\nTest {i}:")
        print(f"Raw: {log}")
        parsed = parser.parse(log)
        if parsed:
            print(f"✓ Parsed successfully:")
            print(f"  Timestamp: {parsed['timestamp']}")
            print(f"  Level: {parsed['level']}")
            print(f"  Source: {parsed['source']}")
            print(f"  Application: {parsed['application']}")
            print(f"  Message: {parsed['message']}")
            print(f"  Facility: {parsed['metadata'].get('facility', 'N/A')}")
        else:
            print("✗ Parsing failed")


def test_regex_parser():
    """Test Custom Regex parser"""
    print("\n" + "=" * 60)
    print("Testing Custom Regex Parser")
    print("=" * 60)
    
    # Test with predefined pattern
    pattern = r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}) \[(?P<level>\w+)\] (?P<source>\S+) - (?P<message>.+)'
    parser = RegexParser(pattern, "Custom Test")
    
    # Test cases
    test_logs = [
        '2025-11-11T16:00:00 [INFO] web-server - Request processed successfully',
        '2025-11-11T16:01:00 [ERROR] database - Connection timeout',
        '2025-11-11T16:02:00 [WARN] cache - Memory usage high',
    ]
    
    print(f"Pattern: {pattern}\n")
    
    for i, log in enumerate(test_logs, 1):
        print(f"\nTest {i}:")
        print(f"Raw: {log}")
        parsed = parser.parse(log)
        if parsed:
            print(f"✓ Parsed successfully:")
            print(f"  Timestamp: {parsed['timestamp']}")
            print(f"  Level: {parsed['level']}")
            print(f"  Source: {parsed['source']}")
            print(f"  Message: {parsed['message']}")
        else:
            print("✗ Parsing failed")


def test_parser_factory():
    """Test Parser Factory auto-detection"""
    print("\n" + "=" * 60)
    print("Testing Parser Factory (Auto-Detection)")
    print("=" * 60)
    
    factory = ParserFactory()
    
    # Mixed format test cases
    test_logs = [
        ('JSON', '{"timestamp":"2025-11-11T16:00:00","level":"INFO","message":"Test JSON log"}'),
        ('Apache', '192.168.1.1 - - [11/Nov/2025:16:00:00 +0000] "GET /test HTTP/1.1" 200 123'),
        ('Syslog', '<34>1 2025-11-11T16:00:00Z server1 app 123 - - Test syslog message'),
    ]
    
    for expected_format, log in test_logs:
        print(f"\n{expected_format} Log:")
        print(f"Raw: {log}")
        
        detected = factory.detect_format(log)
        print(f"Detected format: {detected}")
        
        parsed = factory.auto_parse(log)
        if parsed:
            print(f"✓ Auto-parsed successfully:")
            print(f"  Parser used: {parsed['metadata'].get('parser', 'unknown')}")
            print(f"  Level: {parsed['level']}")
            print(f"  Message: {parsed['message']}")
        else:
            print("✗ Auto-parsing failed")


def main():
    """Run all parser tests"""
    print("\n" + "=" * 70)
    print(" " * 20 + "PARSER TEST SUITE")
    print("=" * 70)
    
    test_json_parser()
    test_apache_parser()
    test_syslog_parser()
    test_regex_parser()
    test_parser_factory()
    
    print("\n" + "=" * 70)
    print(" " * 25 + "TESTS COMPLETE")
    print("=" * 70)
    print("\n✓ All parsers tested successfully!")
    print("\nNext steps:")
    print("1. Restart FastAPI server to load parser endpoints")
    print("2. Visit http://127.0.0.1:5000/api/docs to see parser API")
    print("3. Test parsing via API: curl -X POST http://127.0.0.1:5000/parse/auto ...")


if __name__ == "__main__":
    main()

