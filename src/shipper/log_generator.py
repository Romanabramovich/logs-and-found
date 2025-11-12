"""
Test Log Generator

Generates realistic fake log entries for testing the shipper.
Writes logs in a standard format that the shipper can parse.
"""

import random
import time
from datetime import datetime, timezone
from pathlib import Path


# Log format: TIMESTAMP [LEVEL] source:application - message
# Example: 2025-11-11T18:30:00Z [ERROR] web-server-01:user-api - Database connection timeout

class LogGenerator:
    """Generates realistic fake log entries"""
    
    def __init__(self, output_file='test_logs.log'):
        self.output_file = Path(output_file)
        
        # Realistic log data
        self.levels = ['INFO', 'WARN', 'ERROR', 'DEBUG']
        self.sources = ['web-server-01', 'web-server-02', 'worker-01', 'worker-02', 'api-gateway']
        self.applications = ['user-api', 'payment-service', 'auth-service', 'background-job', 'email-service']
        
        self.messages = {
            'INFO': [
                'Request completed successfully',
                'User logged in',
                'Database query executed',
                'Cache hit for key',
                'Job completed successfully'
            ],
            'WARN': [
                'Slow query detected (>1s)',
                'Cache miss for key',
                'Rate limit approaching threshold',
                'High memory usage detected',
                'Connection pool running low'
            ],
            'ERROR': [
                'Database connection timeout',
                'Failed to connect to external API',
                'User authentication failed',
                'File not found',
                'Payment processing failed'
            ],
            'DEBUG': [
                'Processing request',
                'Cache lookup',
                'Database connection acquired',
                'Parsing request body',
                'Validating input parameters'
            ]
        }
    
    def generate_log_line(self):
        """Generate a single log line in standard format"""
        timestamp = datetime.now(timezone.utc).isoformat()
        level = random.choice(self.levels)
        source = random.choice(self.sources)
        application = random.choice(self.applications)
        message = random.choice(self.messages[level])
        
        # Format: TIMESTAMP [LEVEL] source:application - message
        log_line = f"{timestamp} [{level}] {source}:{application} - {message}"
        return log_line
    
    def generate_logs(self, count=10, interval=1):
        """
        Generate multiple log entries
        
        Args:
            count: Number of logs to generate
            interval: Seconds between each log (0 for instant)
        """
        print(f"Generating {count} log entries to {self.output_file}")
        print(f"Interval: {interval}s between logs")
        print("-" * 60)
        
        with open(self.output_file, 'a') as f: 
            for i in range(count):
                log_line = self.generate_log_line()
                f.write(log_line + '\n')
                f.flush()  #
                
                print(f"[{i+1}/{count}] {log_line}")
                
                if interval > 0 and i < count - 1:
                    time.sleep(interval)
        
        print("-" * 60)
        print(f"Generated {count} logs in {self.output_file}")


def main():
    """Interactive log generation"""
    print("=" * 60)
    print("Test Log Generator")
    print("=" * 60)
    print()
    
    generator = LogGenerator()
    
    # Generate initial batch
    print("Generating initial batch of logs...")
    generator.generate_logs(count=5, interval=0)
    
    print("\nContinuous mode: Generating 1 log every 2 seconds")
    print("Press Ctrl+C to stop")
    print()
    
    try:
        while True:
            generator.generate_logs(count=1, interval=2)
    except KeyboardInterrupt:
        print("\n\nStopped log generation")


if __name__ == "__main__":
    main()

