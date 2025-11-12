import requests
from datetime import datetime, timezone

BASE_URL = 'http://localhost:5000'

def test_successful_insert():
    """Test 1: Valid log insertion"""
    print("\n=== Test 1: Valid Log Insertion ===")
    
    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "ERROR",
        "source": "web-server-01",
        "application": "user-api",
        "message": "Database connection timeout",
        "metadata": {
            "user_id": "12345",
            "request_id": "abc-def"
        }
    }
    
    response = requests.post(f'{BASE_URL}/logs', json=log_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 202, "Should return 202 Accepted"
    assert "message_id" in response.json(), "Should return message_id"
    print("PASSED")


def test_missing_required_field():
    """Test 2: Missing required field (should fail)"""
    print("\n=== Test 2: Missing Required Field ===")
    
    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "ERROR",
        # Missing 'source' field!
        "application": "user-api",
        "message": "Some error"
    }
    
    response = requests.post(f'{BASE_URL}/logs', json=log_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 422, "Should return 422 Unprocessable Entity"
    print("PASSED")


def test_invalid_metadata_type():
    """Test 3: Invalid metadata type (should fail)"""
    print("\n=== Test 3: Invalid Metadata Type ===")
    
    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "WARN",
        "source": "web-server-01",
        "application": "user-api",
        "message": "Warning message",
        "metadata": "this should be a dict, not a string!"
    }
    
    response = requests.post(f'{BASE_URL}/logs', json=log_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 422, "Should return 422 Unprocessable Entity"
    print("PASSED")


def test_without_metadata():
    """Test 4: Log without metadata (should succeed - metadata is optional)"""
    print("\n=== Test 4: Log Without Metadata ===")
    
    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "INFO",
        "source": "worker-02",
        "application": "background-job",
        "message": "Job completed successfully"
        # No metadata field - should be fine!
    }
    
    response = requests.post(f'{BASE_URL}/logs', json=log_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 202, "Should return 202 Accepted"
    print("PASSED")


if __name__ == "__main__":
    print("Starting API Tests...")
    print("Make sure Flask app is running on http://localhost:5000")
    
    try:
        test_successful_insert()
        test_missing_required_field()
        test_invalid_metadata_type()
        test_without_metadata()
        
        print("\n" + "="*50)
        print("ALL TESTS PASSED!")
        print("="*50)
    
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to Flask app.")
        print("Make sure the Flask app is running: python -m src.api.app")