# src/tests/ - Test Suite

API validation tests for the log ingestion endpoint.

## Files

- `test_api.py` - API endpoint tests

## test_api.py

Comprehensive test suite for the Flask API.

**Test Cases:**
1. Valid log insertion (success case)
2. Missing required field (validation)
3. Invalid metadata type (type checking)
4. Optional metadata (edge case)

**Run tests:**
```bash
python src/tests/test_api.py
```

**Prerequisites:**
- Flask app must be running: `python -m src.api.app`
- Database must be set up with schema

**Expected output:**
```
ALL TESTS PASSED!
```

**Adding new tests:**
1. Define test function in `test_api.py`
2. Add assertions for expected behavior
3. Call it in the `__main__` block

