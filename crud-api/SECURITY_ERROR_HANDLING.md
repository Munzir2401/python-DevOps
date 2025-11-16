# Security Improvements: Exception Handling and Error Message Sanitization

## Overview

Improved exception handling across CRUD operations to prevent information leakage through error messages while maintaining comprehensive internal logging for debugging and monitoring.

## Problem: Information Leakage

### Before (Unsafe)
```python
except Exception as e:
    db.rollback()
    raise Exception(f"Failed to create item: {str(e)}")
```

**Risks**:
- Raw database error messages leaked to clients
- Reveals database schema, table structure, constraints
- Exposes internal implementation details
- Could reveal credential info or sensitive queries
- Attackers can use to fingerprint database type
- Compliance issues (GDPR, PCI-DSS, HIPAA)

**Example Leaked Information**:
```
Foreign key constraint violated: items.user_id not found in users.id
Duplicate entry '12345' for key 'items.unique_email'
Column 'description' cannot be null in table 'items'
PostgreSQL error: connection timeout after 30s
Password_hash field too long for VARCHAR(64) in MySQL
```

## Solution: Sanitized Errors with Internal Logging

### After (Secure)

#### CRUD Layer (crud.py)
```python
try:
    db.commit()
    db.refresh(db_item)
except Exception:
    db.rollback()
    # Log full exception internally with stack trace
    logger.exception("Database error occurred while creating item")
    # Raise generic error to caller
    raise Exception("Failed to create item")
```

#### HTTP Layer (main.py)
```python
try:
    return crud.create_item(db, item)
except Exception as e:
    # Log the error with full context
    logger.error("Error creating item", exc_info=True)
    # Return generic error to client
    raise HTTPException(status_code=500, detail="Failed to create item")
```

**Benefits**:
- ✓ No sensitive details exposed to clients
- ✓ Full error context available in logs for debugging
- ✓ Stack traces preserved internally
- ✓ Contextual logging with request parameters
- ✓ Audit trail for security investigations

## Implementation Details

### Logging Configuration (main.py)

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

**Log Levels Used**:
- `logger.error()` - Operational errors (route level)
- `logger.exception()` - Exception details with stack trace (CRUD layer)

### CRUD Layer Exception Handling (crud.py)

```python
logger = logging.getLogger(__name__)

def create_item(db: Session, item: schemas.ItemCreate) -> models.Item:
    db_item = models.Item(...)
    db.add(db_item)
    try:
        db.commit()
        db.refresh(db_item)
    except Exception:
        db.rollback()
        # Full stack trace logged automatically
        logger.exception("Database error occurred while creating item")
        # Generic error raised to caller
        raise Exception("Failed to create item")
    return db_item
```

**Key Points**:
- Don't capture exception variable if not used
- Use `logger.exception()` to auto-include stack trace
- Generic message contains no implementation details
- db.rollback() ensures session consistency

### HTTP Layer Exception Handling (main.py)

```python
@app.post("/items")
def create_item(item: schemas.ItemCreate,
                db: Session = Depends(get_db),
                payload=Depends(verify_jwt)):
    try:
        return crud.create_item(db, item)
    except Exception as e:
        # Log with request context
        logger.error("Error creating item", exc_info=True)
        # Return generic HTTP error
        raise HTTPException(status_code=500, detail="Failed to create item")

@app.put("/items/{item_id}")
def update_item(item_id: int, item: schemas.ItemUpdate, ...):
    try:
        result = crud.update_item(db, item_id, item)
        if result is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return result
    except HTTPException:
        # Re-raise HTTP exceptions without catching them
        raise
    except Exception as e:
        # Log with item ID for context
        logger.error("Error updating item with id=%s", item_id, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update item")

@app.delete("/items/{item_id}")
def delete_item(item_id: int, ...):
    try:
        result = crud.delete_item(db, item_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"message": "Item deleted", "item": result}
    except HTTPException:
        # Re-raise HTTP exceptions (404, etc.)
        raise
    except Exception as e:
        # Log with item ID for context
        logger.error("Error deleting item with id=%s", item_id, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete item")
```

**Key Patterns**:
- HTTPExceptions (404, 401) are re-raised as-is
- Unexpected exceptions caught, logged, and converted to 500 errors
- Contextual information (item_id) included in logs, not responses
- `exc_info=True` captures full stack trace

## Error Message Examples

### Before (Information Leak)
```json
{
  "detail": "Failed to create item: (psycopg2.errors.ForeignKeyViolation) insert or update on table \"items\" violates foreign key constraint \"items_user_id_fkey\"\nDETAIL:  Key (user_id)=(123) is not present in table \"users\"."
}
```

### After (Sanitized)
```json
{
  "detail": "Failed to create item"
}
```

### Internal Log (Full Details Preserved)
```
2025-11-15 10:23:45,123 - crud - ERROR - Database error occurred while creating item
Traceback (most recent call last):
  File "crud.py", line 20, in create_item
    db.commit()
  File ".../sqlalchemy/orm/session.py", line ..., in commit
    ...
sqlalchemy.exc.IntegrityError: (psycopg2.errors.ForeignKeyViolation) insert or update on table "items" 
violates foreign key constraint "items_user_id_fkey"
DETAIL:  Key (user_id)=(123) is not present in table "users".
```

## HTTP Response Examples

### Success: Create Item
```json
{
  "id": 42,
  "name": "My Item",
  "description": "Item description"
}
```

### Error: Item Not Found (404)
```json
{
  "detail": "Item not found"
}
```

### Error: Server Error (500)
```json
{
  "detail": "Failed to create item"
}
```

**Note**: No traceback, SQL details, or system information exposed.

## Logging Output Examples

### CRUD Layer Error (with full context)
```
2025-11-15 10:25:30,456 - crud - ERROR - Database error occurred while updating item with id=999
Traceback (most recent call last):
  File "/app/crud.py", line 42, in update_item
    db.commit()
  File "/usr/local/lib/python3.9/site-packages/sqlalchemy/orm/session.py", line 1234, in commit
    ...
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server: 
Connection refused. Is the server running on host "localhost" (127.0.0.1) and accepting TCP/IP 
connections on port 5432?
```

### HTTP Layer Error (with request context)
```
2025-11-15 10:25:30,789 - main - ERROR - Error deleting item with id=42
Traceback (most recent call last):
  File "/app/main.py", line 210, in delete_item
    result = crud.delete_item(db, item_id)
  File "/app/crud.py", line 62, in delete_item
    db.commit()
...
```

## Monitoring and Alerting

### Log Parsing for Alerts

Use ELK Stack, Datadog, or similar to alert on:

```python
# Alert on database errors
search: 'Database error occurred' AND 'ERROR'

# Alert on multiple failed operations
search: 'Error creating item' OR 'Error updating item' OR 'Error deleting item'
count > 5 in 5m

# Track error frequency by operation
search: 'Error \w+ item'
stats count by message
```

### Audit Trail Example

```
2025-11-15 10:25:00 - User 'user123' created item 42
2025-11-15 10:25:30 - Database error while deleting item 42 (connection timeout)
2025-11-15 10:26:15 - User 'user123' retried delete item 42 - Success
```

## Testing

### Unit Test for Error Sanitization

```python
import pytest
from sqlalchemy.exc import IntegrityError

def test_create_item_db_error_returns_generic_message(db, caplog):
    """Verify DB errors are logged but generic message returned"""
    item = ItemCreate(name="test", description="test")
    
    # Mock db.commit to raise IntegrityError
    with patch.object(db, 'commit', side_effect=IntegrityError("Constraint error", None, None)):
        with pytest.raises(Exception) as exc_info:
            crud.create_item(db, item)
        
        # Client sees generic message
        assert str(exc_info.value) == "Failed to create item"
        
        # Server logs contain full details
        assert "Constraint error" in caplog.text
        assert "IntegrityError" in caplog.text

def test_create_item_route_returns_500_with_generic_message(client, monkeypatch):
    """Verify HTTP route sanitizes CRUD errors"""
    # Mock CRUD to raise
    def mock_create(*args, **kwargs):
        raise Exception("Some internal error")
    
    monkeypatch.setattr(crud, 'create_item', mock_create)
    
    response = client.post("/items", json={"name": "test", "description": "test"})
    
    # No internal details exposed
    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to create item"
    assert "internal" not in response.json()["detail"].lower()
```

## Security Checklist

- [x] Raw exception text not in client responses
- [x] Stack traces logged internally, not exposed to client
- [x] Database errors converted to generic HTTP errors
- [x] Sensitive details (connection strings, SQL) not in error messages
- [x] Request context (IDs, parameters) logged but sanitized from response
- [x] Session properly rolled back on errors
- [x] Audit trail maintained in logs
- [x] Separate error handling for expected (404) vs unexpected (500) errors
- [x] HTTP exceptions (401, 404) not double-caught
- [x] Logging configured with appropriate levels

## Compliance

✓ **GDPR**: No sensitive data exposed in error messages  
✓ **PCI-DSS**: Error messages don't reveal system information  
✓ **OWASP**: Prevents information disclosure vulnerabilities  
✓ **CWE-209**: Improper error handling doesn't leak system details  
✓ **CWE-532**: Audit logs preserved for security analysis  

## References

- [OWASP: Information Disclosure](https://owasp.org/www-community/Information_Exposure_Through_Error_Messages)
- [CWE-209: Information Exposure Through an Error Message](https://cwe.mitre.org/data/definitions/209.html)
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)
- [FastAPI Exception Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
