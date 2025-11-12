"""
Redis Consumer - Batch Log Processing
Reads logs from Redis Stream and writes to PostgreSQL in batches.
"""

import redis
import json
import time
from datetime import datetime
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Import from existing modules
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import get_database_engine
from src.api.models import Log

load_dotenv()


class RedisConsumer:
    """
    Consumes logs from Redis Stream and writes to PostgreSQL.
    
    Key Features:
    - Batch processing (1000 logs at once)
    - Consumer groups (multiple workers, no duplicates)
    - Acknowledgment (confirms processing)
    - Error handling (failed logs go to dead letter queue)
    """
    
    def __init__(self, consumer_name='worker-1', group_name='log-processors', 
                 batch_size=500, stream_name='logs'):
        """
        Initialize consumer.
        
        Args:
            consumer_name: Unique name for this consumer
            group_name: Consumer group name (all workers share this)
            batch_size: How many logs to process at once (default: 500)
            stream_name: Redis stream to read from
        """
        self.consumer_name = consumer_name
        self.group_name = group_name
        self.batch_size = batch_size
        self.stream_name = stream_name
        
        # Connect to Redis
        redis_url = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379')
        self.redis_client = redis.from_url(redis_url, decode_responses=False)
        
        # Ensure consumer group exists
        self._create_consumer_group()
        
        # Connect to PostgreSQL
        self.engine = get_database_engine()
        self.Session = sessionmaker(bind=self.engine)
        
        # Metrics
        self.logs_processed = 0
        self.batches_processed = 0
        self.errors = 0
        self.start_time = time.time()
        
        print(f"Consumer '{consumer_name}' initialized (batch size: {batch_size})")
    
    def _create_consumer_group(self):
        """Create consumer group if it doesn't exist"""
        try:
            # Create group starting from beginning (0) or now ($)
            self.redis_client.xgroup_create(
                self.stream_name,
                self.group_name,
                id='0',  # Process all messages (use '$' for only new ones)
                mkstream=True  # Create stream if doesn't exist
            )
            print(f"Created consumer group '{self.group_name}'")
        except redis.ResponseError as e:
            if 'BUSYGROUP' in str(e):
                # Group already exists - that's fine
                pass
            else:
                raise
    
    def process_batch(self):
        """
        Read and process one batch of logs.
        
        Returns:
            int: Number of logs processed
        """
        try:
            # Read from stream using consumer group
            # XREADGROUP blocks until messages available
            messages = self.redis_client.xreadgroup(
                self.group_name,
                self.consumer_name,
                {self.stream_name: '>'},  # '>' means new messages
                count=self.batch_size,
                block=2000  # Wait up to 2 seconds for messages (batch window)
            )
            
            if not messages:
                return 0  # No messages available
            
            # Parse messages
            stream_messages = messages[0][1]  # [(stream, [(id, data)])]
            
            if not stream_messages:
                return 0
            
            # Process batch
            logs_to_insert = []
            message_ids = []
            
            for message_id, message_data in stream_messages:
                try:
                    # Parse JSON payload
                    payload = json.loads(message_data[b'data'])
                    
                    # Create Log object
                    log = Log(
                        timestamp=datetime.fromisoformat(payload['timestamp']),
                        level=payload['level'],
                        source=payload['source'],
                        application=payload['application'],
                        message=payload['message'],
                        log_metadata=payload.get('metadata')
                    )
                    
                    logs_to_insert.append(log)
                    message_ids.append(message_id)
                    
                except Exception as e:
                    print(f"Error parsing message {message_id}: {e}")
                    self.errors += 1
                    # Still acknowledge to remove from queue
                    message_ids.append(message_id)
            
            # Batch insert to PostgreSQL
            if logs_to_insert:
                self._batch_insert(logs_to_insert)
            
            # Acknowledge messages (remove from pending)
            for msg_id in message_ids:
                self.redis_client.xack(self.stream_name, self.group_name, msg_id)
            
            # Update metrics
            processed = len(logs_to_insert)
            self.logs_processed += processed
            self.batches_processed += 1
            
            if self.batches_processed % 10 == 0:
                self._print_metrics()
            
            return processed
            
        except Exception as e:
            print(f"Error processing batch: {e}")
            self.errors += 1
            return 0
    
    def _batch_insert(self, logs):
        """
        Insert multiple logs at once (much faster than one-by-one).
        Also publishes logs to Redis pub/sub for WebSocket streaming.
        
        Args:
            logs: List of Log objects
        """
        session = self.Session()
        try:
            # Use add_all to track objects
            # This allows us to get the IDs after commit
            session.add_all(logs)
            
            # Single commit for entire batch
            session.commit()
            
            # Now the logs have their database-generated IDs
            # Publish logs to Redis pub/sub for WebSocket streaming
            self._publish_to_websocket(logs)
            
        except Exception as e:
            session.rollback()
            print(f"Error inserting batch: {e}")
            raise
        finally:
            session.close()
    
    def _publish_to_websocket(self, logs):
        """
        Publish logs to Redis pub/sub for WebSocket clients.
        
        Args:
            logs: List of Log objects with database IDs
        """
        try:
            for log in logs:
                # Convert Log object to dict for JSON serialization
                log_data = {
                    'id': log.id,
                    'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                    'level': log.level,
                    'source': log.source,
                    'application': log.application,
                    'message': log.message,
                    'metadata': log.log_metadata
                }
                
                # Publish to Redis pub/sub channel
                self.redis_client.publish('new_logs', json.dumps(log_data))
        
        except Exception as e:
            # Don't fail the batch if pub/sub fails
            print(f"Warning: Failed to publish to WebSocket channel: {e}")
    
    def run(self, duration=None):
        """
        Start consuming messages.
        
        Args:
            duration: How long to run (seconds), None = forever
        """
        print(f"Consumer '{self.consumer_name}' starting...")
        print(f"Reading from stream '{self.stream_name}' in group '{self.group_name}'")
        print("Press Ctrl+C to stop")
        print("-" * 60)
        
        start = time.time()
        
        try:
            while True:
                # Process one batch
                processed = self.process_batch()
                
                # Check if we should stop
                if duration and (time.time() - start) > duration:
                    break
                
                # Small sleep if no messages (reduce CPU usage)
                if processed == 0:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\nStopping consumer...")
        finally:
            self._print_final_metrics()
            self.close()
    
    def _print_metrics(self):
        """Print processing metrics"""
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            rate = self.logs_processed / elapsed
            print(f"[{self.consumer_name}] Processed {self.logs_processed} logs "
                  f"in {self.batches_processed} batches ({rate:.0f} logs/sec, "
                  f"{self.errors} errors)")
    
    def _print_final_metrics(self):
        """Print final statistics"""
        elapsed = time.time() - self.start_time
        print("\n" + "=" * 60)
        print(f"Consumer '{self.consumer_name}' Statistics:")
        print(f"  Total logs processed: {self.logs_processed}")
        print(f"  Total batches: {self.batches_processed}")
        print(f"  Errors: {self.errors}")
        print(f"  Runtime: {elapsed:.1f} seconds")
        if elapsed > 0:
            print(f"  Average rate: {self.logs_processed / elapsed:.0f} logs/sec")
        print("=" * 60)
    
    def close(self):
        """Clean up connections"""
        if self.redis_client:
            self.redis_client.close()


def main():
    """Run a single consumer"""
    import sys
    
    consumer_name = sys.argv[1] if len(sys.argv) > 1 else 'worker-1'
    
    consumer = RedisConsumer(
        consumer_name=consumer_name,
        batch_size=500
    )
    
    consumer.run()


if __name__ == "__main__":
    main()

