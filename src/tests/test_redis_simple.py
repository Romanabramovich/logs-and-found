"""
Simple Redis Queue Test
Tests the Redis queue ingestion without comparing to direct DB writes.
"""

import requests
import time
from datetime import datetime


def create_test_log(i):
    """Generate a test log"""
    return {
        'timestamp': datetime.now().isoformat(),
        'level': 'INFO',
        'source': 'performance-test',
        'application': 'redis-queue',
        'message': f'Test log message #{i}',
        'metadata': {'test_id': i}
    }


def test_redis_queue(num_logs=1000):
    """
    Send logs to Redis queue and measure performance.
    """
    url = 'http://127.0.0.1:5000/logs'  
    
    print(f"\nSending {num_logs} logs to Redis queue...")
    print("-" * 60)
    
    start_time = time.time()
    success = 0
    errors = 0
    latencies = []
    
    for i in range(num_logs):
        log_data = create_test_log(i)
        
        request_start = time.time()
        
        try:
            response = requests.post(url, json=log_data, timeout=5)
            request_time = (time.time() - request_start) * 1000  # Convert to ms
            
            latencies.append(request_time)
            
            if response.status_code == 202:
                success += 1
            else:
                errors += 1
                if errors == 1:
                    print(f"Error: {response.status_code} - {response.text[:100]}")
        
        except Exception as e:
            errors += 1
            if errors == 1:
                print(f"Request failed: {str(e)[:100]}")
        
        # Progress indicator
        if (i + 1) % 100 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            print(f"  Sent {i+1}/{num_logs} logs ({rate:.0f} logs/sec)")
    
    total_time = time.time() - start_time
    
    # Calculate statistics
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
    p99_latency = sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0
    throughput = success / total_time if total_time > 0 else 0
    
    # Print results
    print("\n" + "=" * 60)
    print("REDIS QUEUE PERFORMANCE")
    print("=" * 60)
    print(f"Total logs sent:     {num_logs}")
    print(f"Successful:          {success}")
    print(f"Errors:              {errors}")
    print(f"Total time:          {total_time:.2f} seconds")
    print(f"Throughput:          {throughput:.0f} logs/sec")
    print(f"Average latency:     {avg_latency:.2f} ms")
    print(f"P95 latency:         {p95_latency:.2f} ms")
    print(f"P99 latency:         {p99_latency:.2f} ms")
    print("=" * 60)
    
    return {
        'success': success,
        'errors': errors,
        'total_time': total_time,
        'throughput': throughput,
        'avg_latency': avg_latency
    }


def check_queue_status():
    """Check Redis queue status"""
    try:
        response = requests.get('http://127.0.0.1:5000/queue/status')
        if response.status_code == 200:
            data = response.json()
            print("\nQueue Status:")
            print(f"  Messages in queue: {data.get('queue_length', 0)}")
            print(f"  Consumer groups:   {data.get('consumer_groups', 0)}")
            print(f"  Messages sent:     {data.get('messages_sent', 0)}")
        else:
            print(f"Could not get queue status: {response.status_code}")
    except Exception as e:
        print(f"Error checking queue: {e}")


def main():
    print("=" * 60)
    print("Redis Queue Performance Test")
    print("=" * 60)
    print("\nMake sure:")
    print("  1. Flask API is running (python -m src.api.app)")
    print("  2. Redis is running (docker ps | grep redis)")
    print("  3. Workers are running (python -m src.queue.worker_pool)")
    print()
    
    # Check initial queue status
    check_queue_status()
    
    input("\nPress Enter to start test...")
    
    # Test with 1000 logs
    test_redis_queue(1000)
    
    print("\nWaiting 5 seconds for workers to process...")
    time.sleep(5)
    
    # Check final queue status
    check_queue_status()
    
    print("\n✓ Test complete!")
    print("\nTip: Check your worker pool terminal to see processing statistics")


if __name__ == "__main__":
    main()

