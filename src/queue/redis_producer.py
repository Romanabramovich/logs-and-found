"""
Redis Producer
Writes logs to Redis Stream instantly for async processing.
"""

import redis
import json
import time
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class RedisProducer:
    """
    Writes logs to Redis Stream for async processing.
    """
    
    def __init__(self, redis_url=None, stream_name='logs'):
        """
        Initialize Redis connection.
        
        Args:
            redis_url: Redis connection string (default from env)
            stream_name: Name of Redis stream
        """
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.stream_name = stream_name
        
        # Connect to Redis
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=False 
            )

            # Test connection
            self.redis_client.ping()
            print(f"Connected to Redis at {self.redis_url}")

        except redis.ConnectionError as e:
            print(f"Failed to connect to Redis: {e}")
            raise
        
        # Metrics
        self.messages_sent = 0
        self.last_metric_time = time.time()
    
    def enqueue(self, log_data):
        """
        Add log to Redis Stream.
        
        Args:
            log_data: Dictionary with log fields
            
        Returns:
            message_id: Redis stream message ID
        """
        try:
            # Serialize to JSON
            payload = json.dumps(log_data)
            
            # Add to Redis Stream
            # XADD creates stream if it doesn't exist
            message_id = self.redis_client.xadd(
                self.stream_name,
                {'data': payload}
            )
            
            self.messages_sent += 1
            
            if self.messages_sent % 1000 == 0:
                self._print_metrics()
            
            return message_id
            
        except Exception as e:
            print(f"Error enqueuing log: {e}")
            raise
    
    def enqueue_batch(self, logs):
        """
        Add multiple logs at once.
        
        Args:
            logs: List of log dictionaries
            
        Returns:
            count: Number of logs enqueued
        """
        try:
            # Use pipeline for batch writes
            pipe = self.redis_client.pipeline()
            
            for log_data in logs:
                payload = json.dumps(log_data)
                pipe.xadd(self.stream_name, {'data': payload})
            
            # Execute all commands at once
            results = pipe.execute()
            
            self.messages_sent += len(logs)
            return len(results)
            
        except Exception as e:
            print(f"Error enqueuing batch: {e}")
            raise
    
    def get_stream_info(self):
        """
        Get information about the Redis stream.
        
        Returns:
            dict: Stream statistics
        """
        try:
            info = self.redis_client.xinfo_stream(self.stream_name)
            return {
                'length': info['length'],  # Messages in stream
                'first_entry': info.get('first-entry'),
                'last_entry': info.get('last-entry'),
                'groups': info['groups']  # Consumer groups
            }
        except redis.ResponseError:
            return {'length': 0, 'groups': 0}
    
    def _print_metrics(self):
        """Print metrics"""
        current_time = time.time()
        elapsed = current_time - self.last_metric_time
        
        if elapsed > 0:
            rate = 1000 / elapsed  # logs per second
            print(f"Producer: {self.messages_sent} messages sent ({rate:.0f} msgs/sec)")
        
        self.last_metric_time = current_time
    
    def close(self):
        """Close Redis connection"""
        if self.redis_client:
            self.redis_client.close()


def test_producer():
    """Test the producer"""
    print("Testing Redis Producer...")
    
    producer = RedisProducer()
    
    # Test single message
    test_log = {
        'timestamp': datetime.now().isoformat(),
        'level': 'INFO',
        'source': 'test',
        'application': 'redis-test',
        'message': 'Test message from Redis producer'
    }
    
    message_id = producer.enqueue(test_log)
    print(f"Enqueued log with ID: {message_id}")
    
    # Check stream info
    info = producer.get_stream_info()
    print(f"Stream info: {info}")
    
    producer.close()
    print("Producer test complete!")


if __name__ == "__main__":
    test_producer()

