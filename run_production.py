"""
Production server runner using Uvicorn.

Uvicorn is a lightning-fast ASGI server that provides:
- Async/await support for high concurrency
- Multiple worker processes
- 10-100x better performance than Flask dev server
"""

import uvicorn
import multiprocessing

if __name__ == "__main__":
    # Calculate optimal worker count (CPU cores)
    workers = multiprocessing.cpu_count()
    
    print("=" * 60)
    print("Starting Log Aggregation API (Production Mode)")
    print("=" * 60)
    print("Server:  Uvicorn ASGI")
    print("Host:    0.0.0.0")
    print("Port:    5000")
    print(f"Workers: {workers}")
    print("=" * 60)
    print("\n📊 API:  http://localhost:5000")
    print("📖 Docs: http://localhost:5000/api/docs")
    print("\nPress Ctrl+C to stop\n")
    
    # Run with multiple workers for production
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=5000,
        workers=workers,
        log_level="info"
    )

