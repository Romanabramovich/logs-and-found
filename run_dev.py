"""
Development server runner.
Single worker with auto-reload for development.
"""

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Log Aggregation API (Development Mode)")
    print("=" * 60)
    print("Server:  Uvicorn ASGI (single worker)")
    print("Host:    127.0.0.1")
    print("Port:    5000")
    print("Reload:  Enabled (auto-restart on code changes)")
    print("=" * 60)
    print("\n📊 API:  http://localhost:5000")
    print("📖 Docs: http://localhost:5000/api/docs")
    print("\nPress Ctrl+C to stop\n")
    
    # Development mode with auto-reload
    uvicorn.run(
        "src.api.app:app",
        host="127.0.0.1",
        port=5000,
        reload=True,
        log_level="debug"
    )

