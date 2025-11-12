"""
Concurrent Redis Queue Test
Uses threading to send multiple requests in parallel (realistic load test).
"""

import requests
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


def create_test_log(i):
    """Generate a test log"""
    return {
        'timestamp': datetime.now().isoformat(),
        'level': 'INFO',
        'source': 'concurrent-test',
        'application': 'redis-queue',
        'message': f'Test log message #{i}',
        'metadata': {'test_id': i}
    }


def send_log(i, url):
    """Send a single log (runs in thread)"""
    try:
        log_data = create_test_log(i)
        start = time.time()
        response = requests.post(url, json=log_data, timeout=5)
        latency = (time.time() - start) * 1000
        
        return {
            'success': response.status_code == 202,
            'latency': latency,
            'status': response.status_code
        }
    except Exception as e:
        return {
            'success': False,
            'latency': 0,
            'error': str(e)
        }


def test_concurrent(num_logs=1000, max_workers=50):
    """
    Send logs concurrently using thread pool.
    
    Args:
        num_logs: Total logs to send
        max_workers: Number of concurrent threads
    """
    url = 'http://127.0.0.1:5000/data/fast'  
    
    print(f"\nSending {num_logs} logs with {max_workers} concurrent threads...")
    print("-" * 60)
    
    start_time = time.time()
    results = []
    
    # Send requests concurrently
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = [executor.submit(send_log, i, url) for i in range(num_logs)]
        
        # Collect results as they complete
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            results.append(result)
            
            # Progress indicator
            if (i + 1) % 100 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                print(f"  Completed {i+1}/{num_logs} requests ({rate:.0f} req/sec)")
    
    total_time = time.time() - start_time
    
    # Calculate statistics
    successes = sum(1 for r in results if r['success'])
    errors = len(results) - successes
    latencies = [r['latency'] for r in results if r['success']]
    
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    p50_latency = sorted(latencies)[int(len(latencies) * 0.50)] if latencies else 0
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
    p99_latency = sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0
    throughput = successes / total_time if total_time > 0 else 0
    
    # Print results
    print("\n" + "=" * 60)
    print("CONCURRENT REDIS QUEUE PERFORMANCE")
    print("=" * 60)
    print(f"Total requests:      {num_logs}")
    print(f"Concurrent threads:  {max_workers}")
    print(f"Successful:          {successes}")
    print(f"Errors:              {errors}")
    print(f"Total time:          {total_time:.2f} seconds")
    print(f"Throughput:          {throughput:.0f} logs/sec")
    print("-" * 60)
    print(f"Average latency:     {avg_latency:.2f} ms")
    print(f"P50 latency:         {p50_latency:.2f} ms")
    print(f"P95 latency:         {p95_latency:.2f} ms")
    print(f"P99 latency:         {p99_latency:.2f} ms")
    print("=" * 60)


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
    print("Concurrent Redis Queue Performance Test")
    print("=" * 60)
    print("\nThis test simulates realistic concurrent load.")
    print("\nMake sure:")
    print("  1. Flask API is running (python -m src.api.app)")
    print("  2. Redis is running (docker ps | grep redis)")
    print("  3. Workers are running (python -m src.queue.worker_pool)")
    
    # Check initial queue status
    check_queue_status()
    
    input("\nPress Enter to start test...")
    
    # Test with 1000 logs, 50 concurrent threads
    test_concurrent(num_logs=1000, max_workers=50)
    
    print("\nWaiting 10 seconds for workers to process...")
    time.sleep(10)
    
    # Check final queue status
    check_queue_status()
    
    print("\n✓ Test complete!")
    print("\nCheck your worker pool terminal to see processing statistics")


if __name__ == "__main__":
    main()

