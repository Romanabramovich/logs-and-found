"""
Worker Pool - Parallel Log Processing

Manages multiple consumer workers for high throughput.
Scales horizontally - add more workers to process faster.
"""

import multiprocessing
import sys
import signal
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def worker_process_func(worker_id, batch_size):
    """
    Standalone worker process function (needed for Windows multiprocessing).
    
    Args:
        worker_id: Unique ID for this worker
        batch_size: Batch size for processing
    """
    # Import here to ensure clean process initialization
    from src.queue.redis_consumer import RedisConsumer
    
    consumer_name = f"worker-{worker_id}"
    
    try:
        consumer = RedisConsumer(
            consumer_name=consumer_name,
            batch_size=batch_size
        )
        
        # Run until stopped
        consumer.run()
        
    except KeyboardInterrupt:
        print(f"\n[{consumer_name}] Shutting down...")
    except Exception as e:
        print(f"[{consumer_name}] Error: {e}")


class WorkerPool:
    """
    Manages a pool of consumer workers.
    
    Each worker processes logs independently from Redis.
    No duplicates - Redis consumer groups handle distribution.
    """
    
    def __init__(self, num_workers=3, batch_size=1000):
        """
        Initialize worker pool.
        
        Args:
            num_workers: Number of parallel workers
            batch_size: Batch size for each worker
        """
        self.num_workers = num_workers
        self.batch_size = batch_size
        self.processes = []
        self.running = False
        
        print(f"Initializing worker pool with {num_workers} workers")
        print(f"Batch size: {batch_size} logs per batch")
    
    def start(self):
        """Start all worker processes"""
        print("\n" + "=" * 60)
        print("Starting Worker Pool")
        print("=" * 60)
        
        self.running = True
        
        # Create worker processes
        for i in range(self.num_workers):
            process = multiprocessing.Process(
                target=worker_process_func,
                args=(i + 1, self.batch_size),
                name=f"Worker-{i+1}"
            )
            process.start()
            self.processes.append(process)
            print(f"Started {process.name} (PID: {process.pid})")
        
        print("\nAll workers started. Press Ctrl+C to stop.")
        print("-" * 60)
        
        # Monitor workers
        try:
            while self.running:
                # Check if any worker died
                for process in self.processes:
                    if not process.is_alive():
                        print(f"WARNING: {process.name} died! Restarting...")
                        self._restart_worker(process)
                
                time.sleep(5)  # Check every 5 seconds
                
        except KeyboardInterrupt:
            print("\n\nShutting down worker pool...")
            self.stop()
    
    def _restart_worker(self, dead_process):
        """Restart a dead worker"""
        # Remove dead process
        self.processes.remove(dead_process)
        
        # Extract worker ID from name
        worker_id = int(dead_process.name.split('-')[1])
        
        # Start new process
        process = multiprocessing.Process(
            target=worker_process_func,
            args=(worker_id, self.batch_size),
            name=dead_process.name
        )
        process.start()
        self.processes.append(process)
        print(f"Restarted {process.name} (PID: {process.pid})")
    
    def stop(self):
        """Stop all workers gracefully"""
        self.running = False
        
        print("Stopping all workers...")
        
        # Send termination signal to all processes
        for process in self.processes:
            if process.is_alive():
                print(f"Stopping {process.name}...")
                process.terminate()
        
        # Wait for all to finish (with timeout)
        for process in self.processes:
            process.join(timeout=5)
            if process.is_alive():
                print(f"Force killing {process.name}...")
                process.kill()
        
        print("All workers stopped.")
        print("=" * 60)
    
    def get_status(self):
        """Get status of all workers"""
        status = {
            'total_workers': self.num_workers,
            'running_workers': sum(1 for p in self.processes if p.is_alive()),
            'workers': []
        }
        
        for process in self.processes:
            status['workers'].append({
                'name': process.name,
                'pid': process.pid,
                'alive': process.is_alive()
            })
        
        return status


def main():
    """CLI for worker pool"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Log Processing Worker Pool')
    parser.add_argument('--workers', type=int, default=3,
                        help='Number of worker processes (default: 3)')
    parser.add_argument('--batch-size', type=int, default=1000,
                        help='Batch size for each worker (default: 1000)')
    
    args = parser.parse_args()
    
    # Create and start pool
    pool = WorkerPool(
        num_workers=args.workers,
        batch_size=args.batch_size
    )
    
    pool.start()


if __name__ == "__main__":
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()
    main()

