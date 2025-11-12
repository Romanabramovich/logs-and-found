"""
Performance Test - Redis Queue Ingestion

Tests the performance of the Redis-based log ingestion endpoint.
"""

import requests
import time
from datetime import datetime, timezone


BASE_URL = 'http://127.0.0.1:5000'  


def create_test_log(i):
    """Create a test log entry"""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "INFO",
        "source": "performance-test",
        "application": "redis-benchmark",
        "message": f"Performance test log #{i}",
        "metadata": {"test_id": i, "batch": "performance"}
    }


def test_endpoint(endpoint, num_logs=100):
    """
    Test the endpoint's performance.
    
    Args:
        endpoint: API endpoint (/logs)
        num_logs: Number of logs to send
        
    Returns:
        dict: Performance metrics
    """
    print(f"\nTesting {endpoint} with {num_logs} logs...")
    print("-" * 60)
    
    url = f"{BASE_URL}{endpoint}"
    
    latencies = []
    errors = 0
    
    start_time = time.time()
    
    for i in range(num_logs):
        log_data = create_test_log(i)
        
        request_start = time.time()
        
        try:
            response = requests.post(url, json=log_data, timeout=5)
            request_time = (time.time() - request_start) * 1000  # Convert to ms
            
            latencies.append(request_time)
            
            if response.status_code not in [201, 202]:
                errors += 1
                if errors == 1:  # Print first error
                    print(f"Error: {response.status_code} - {response.text[:100]}")
        
        except Exception as e:
            errors += 1
            if errors == 1:
                print(f"Request failed: {e}")
    
    total_time = time.time() - start_time
    
    # Calculate metrics
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
    else:
        avg_latency = min_latency = max_latency = p95_latency = 0
    
    throughput = num_logs / total_time if total_time > 0 else 0
    
    # Print results
    print(f"\nResults:")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Throughput: {throughput:.0f} logs/sec")
    print(f"  Latency (avg): {avg_latency:.1f}ms")
    print(f"  Latency (min): {min_latency:.1f}ms")
    print(f"  Latency (max): {max_latency:.1f}ms")
    print(f"  Latency (p95): {p95_latency:.1f}ms")
    print(f"  Errors: {errors}")
    
    return {
        'endpoint': endpoint,
        'total_time': total_time,
        'throughput': throughput,
        'avg_latency': avg_latency,
        'p95_latency': p95_latency,
        'errors': errors
    }


def check_queue_status():
    """Check Redis queue status"""
    try:
        response = requests.get(f"{BASE_URL}/queue/status")
        if response.status_code == 200:
            data = response.json()
            print(f"\nQueue Status:")
            print(f"  Queue length: {data['queue_length']}")
            print(f"  Messages sent: {data['messages_sent']}")
            print(f"  Consumer groups: {data['consumer_groups']}")
        else:
            print(f"Queue status unavailable: {response.status_code}")
    except Exception as e:
        print(f"Could not check queue status: {e}")


def main():
    """Run performance test"""
    print("=" * 60)
    print("Log Ingestion Performance Test")
    print("=" * 60)
    print("\nMake sure:")
    print("  1. FastAPI is running (python run_dev.py)")
    print("  2. Redis is running (docker ps | grep redis)")
    print("  3. Workers are running (python -m src.queue.worker_pool)")
    print()
    
    input("Press Enter to start test...")
    
    num_logs = 500
    
    # Test logs endpoint
    result = test_endpoint('/logs', num_logs)
    
    # Check queue
    time.sleep(1)
    check_queue_status()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    print(f"\nEndpoint: /logs")
    print(f"  Throughput: {result['throughput']:.0f} logs/sec")
    print(f"  Avg Latency: {result['avg_latency']:.1f}ms")
    print(f"  P95 Latency: {result['p95_latency']:.1f}ms")
    print(f"  Errors: {result['errors']}")
    
    print("\n" + "=" * 60)
    
    print("\nNote: All logs are processed asynchronously via Redis.")
    print("Workers batch insert logs to PostgreSQL in the background.")
    print("The API stays fast even under heavy load!")


if __name__ == "__main__":
    main()

