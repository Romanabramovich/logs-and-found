"""
Log Shipper

Monitors log files and ships entries to the Flask API.
Tracks file position to avoid re-sending logs on restart.
"""

import re
import time
import requests
import sys
from pathlib import Path
from datetime import datetime


class LogShipper:
    """Ships log entries from a file to the API"""
    
    def __init__(self, log_file, api_url='http://localhost:5000/data/', 
                 batch_size=50, batch_timeout=5.0, position_save_interval=100):
        self.log_file = Path(log_file)
        self.api_url = api_url
        self.batch_api_url = api_url.rstrip('/') + '/batch'  # Batch endpoint
        self.position_file = Path(f"{log_file}.position")  # Track where we left off
        
        # Performance tuning parameters
        self.batch_size = batch_size  # Send logs in batches of this size
        self.batch_timeout = batch_timeout  # Max seconds to wait before sending partial batch
        self.position_save_interval = position_save_interval  # Save position every N logs
        
        # Batching state
        self.batch = []  # Current batch of logs to send
        self.last_batch_time = time.time()  # When we last sent a batch
        self.last_position_save = 0  # Track when we last saved position
        
        # HTTP Session with connection pooling - reuses TCP connections
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Regex to parse log lines
        # Format: TIMESTAMP [LEVEL] source:application - message
        self.log_pattern = re.compile(
            r'(?P<timestamp>\S+)\s+'           # Timestamp (no spaces)
            r'\[(?P<level>\w+)\]\s+'           # [LEVEL]
            r'(?P<source>[\w-]+):'              # source:
            r'(?P<application>[\w-]+)\s+-\s+'  # application -
            r'(?P<message>.+)'                  # message (rest of line)
        )
        
        self.stats = {
            'lines_processed': 0,
            'lines_sent': 0,
            'lines_failed': 0,
            'batches_sent': 0,
            'position_saves': 0
        }
    
    def parse_log_line(self, line):
        """
        Parse a log line into structured data
        
        Args:
            line: Raw log string
            
        Returns:
            dict with parsed fields, or None if parsing fails
        """
        match = self.log_pattern.match(line.strip())
        
        if not match:
            print(f"Failed to parse: {line[:50]}...")
            return None
        
        data = match.groupdict()
        
        # Convert timestamp to ISO format if needed
        # Our generator already creates ISO format, but handle edge cases
        try:
            # Validate timestamp can be parsed
            datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        except ValueError:
            print(f"Invalid timestamp: {data['timestamp']}")
            return None
        
        return {
            'timestamp': data['timestamp'],
            'level': data['level'],
            'source': data['source'],
            'application': data['application'],
            'message': data['message'],
            'metadata': {
                'shipper': 'python-log-shipper',
                'file': str(self.log_file)
            }
        }
    
    def add_to_batch(self, log_data):
        """
        Add log to current batch
        
        Args:
            log_data: Parsed log dictionary
        """
        self.batch.append(log_data)
    
    def should_flush_batch(self):
        """
        Check if batch should be flushed
        
        Returns:
            True if batch size reached or timeout expired
        """
        if len(self.batch) == 0:
            return False
        
        # Flush if batch is full
        if len(self.batch) >= self.batch_size:
            return True
        
        # Flush if timeout expired
        if time.time() - self.last_batch_time >= self.batch_timeout:
            return True
        
        return False
    
    def flush_batch(self):
        """
        Send current batch to API using bulk endpoint
        
        Returns:
            True if successful, False otherwise
        """
        if len(self.batch) == 0:
            return True
        
        try:
            response = self.session.post(
                self.batch_api_url,
                json=self.batch,
                timeout=10  # Longer timeout for batches
            )
            
            if response.status_code == 201:
                result = response.json()
                count = result.get('count', len(self.batch))
                self.stats['lines_sent'] += count
                self.stats['batches_sent'] += 1
                print(f"✓ Sent batch: {count} logs (Total: {self.stats['lines_sent']})")
                
                # Clear batch and reset timer
                self.batch = []
                self.last_batch_time = time.time()
                return True
            else:
                print(f"API Error {response.status_code}: {response.text[:100]}")
                self.stats['lines_failed'] += len(self.batch)
                self.batch = []  # Clear failed batch
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"Cannot connect to API at {self.batch_api_url}")
            self.stats['lines_failed'] += len(self.batch)
            self.batch = []
            return False
        except requests.exceptions.Timeout:
            print(f"API request timeout (batch size: {len(self.batch)})")
            self.stats['lines_failed'] += len(self.batch)
            self.batch = []
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            self.stats['lines_failed'] += len(self.batch)
            self.batch = []
            return False
    
    def get_last_position(self):
        """Read last file position from position file"""
        if self.position_file.exists():
            try:
                with open(self.position_file, 'r') as f:
                    position = int(f.read().strip())
                    print(f"Resuming from position: {position}")
                    return position
            except:
                pass
        return 0
    
    def save_position(self, position, force=False):
        """
        Save current file position (periodically, not every line)
        
        Args:
            position: File position to save
            force: If True, save immediately regardless of interval
        """
        # Only save if enough logs have been processed OR force=True
        if force or (self.stats['lines_processed'] - self.last_position_save >= self.position_save_interval):
            with open(self.position_file, 'w') as f:
                f.write(str(position))
            self.last_position_save = self.stats['lines_processed']
            self.stats['position_saves'] += 1
    
    def tail_file(self):
        """
        Tail the log file and process new lines
        
        This is the main loop - it continuously monitors the file
        """
        print("=" * 60)
        print("Log Shipper Started - High Performance Mode")
        print("=" * 60)
        print(f"Monitoring: {self.log_file}")
        print(f"Batch API: {self.batch_api_url}")
        print(f"Batch size: {self.batch_size} logs")
        print(f"Batch timeout: {self.batch_timeout}s")
        print(f"Position save interval: {self.position_save_interval} logs")
        print(f"Press Ctrl+C to stop")
        print("-" * 60)
        
        # Start from last known position
        last_position = self.get_last_position()
        
        with open(self.log_file, 'r') as f:
            # Seek to last position
            f.seek(last_position)
            
            try:
                while True:
                    # Read new line
                    line = f.readline()
                    
                    if line:
                        # New content available
                        self.stats['lines_processed'] += 1
                        
                        # Parse the line
                        log_data = self.parse_log_line(line)
                        
                        if log_data:
                            # Add to batch instead of sending immediately
                            self.add_to_batch(log_data)
                        
                        # Get current position
                        current_position = f.tell()
                        
                        # Check if we should flush the batch
                        if self.should_flush_batch():
                            self.flush_batch()
                            # Save position after successful batch send
                            self.save_position(current_position)
                    
                    else:
                        # No new content
                        # Check if we should flush partial batch due to timeout
                        if self.should_flush_batch():
                            current_position = f.tell()
                            self.flush_batch()
                            self.save_position(current_position)
                        
                        # Wait a bit before checking again
                        time.sleep(0.1)  # Reduced from 0.5s for better responsiveness
                        
            except KeyboardInterrupt:
                print("\n" + "-" * 60)
                print("Shutting down...")
                
                # Flush any remaining logs in batch
                if len(self.batch) > 0:
                    print(f"Flushing final batch of {len(self.batch)} logs...")
                    self.flush_batch()
                
                # Save final position
                current_position = f.tell()
                self.save_position(current_position, force=True)
                
                print(f"Stats: {self.stats['lines_sent']} sent, "
                      f"{self.stats['lines_failed']} failed, "
                      f"{self.stats['lines_processed']} total")
                print(f"Batches sent: {self.stats['batches_sent']}, "
                      f"Position saves: {self.stats['position_saves']}")
                print("Shipper stopped")


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python -m src.shipper.log_shipper <log_file file path>")
        sys.exit(1)
    
    log_file = sys.argv[1]
    
    if not Path(log_file).exists():
        print(f"Error: File not found: {log_file}")
        sys.exit(1)
    
    shipper = LogShipper(log_file)
    shipper.tail_file()


if __name__ == "__main__":
    main()

