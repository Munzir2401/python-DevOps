# Schema Validation Improvements: Write-Time Enforcement

## Overview

Moved description validation from read-time (database mapping) to write-time (schema validation), ensuring no new NULL descriptions can be stored while handling legacy database NULLs through migrations.

## Problem: Inconsistent Validation

### Before (Read-Time Coercion)
```python
class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None  # Allows None at input

class Item(ItemBase):
    id: int
    
    @field_validator('description', mode='before')
    @classmethod
    def coerce_null_description(cls, v):
        """Handle existing NULL description values on read"""
        if v is None:
            return ""
        return v
```

**Problems**:
- ❌ Allows None values at write time (ItemCreate, ItemUpdate)
- ❌ Only fixes NULLs when reading from database
- ❌ Doesn't prevent new NULLs from being inserted
- ❌ Inconsistent behavior: creation accepts None, read coerces it
- ❌ Legacy NULLs remain mixed with empty strings
- ❌ Type hint `Optional[str]` contradicts intended behavior

**Scenarios**:
```python
# Client sends:
POST /items {
  "name": "My Item",
  "description": null  # Accepted but shouldn't be
}

# Created with NULL in database
# Then when read, gets coerced to ""
# But original issue persists - NULL was accepted
```

## Solution: Write-Time Enforcement

### After (Schema Validation)

#### ItemBase (Create Input)
```python
class ItemBase(BaseModel):
    name: str
    description: str  # Non-optional - enforced at write time
    
    @field_validator('description', mode='before')
    @classmethod
    def coerce_null_description_on_write(cls, v):
        """
        Enforce non-null description at write time.
        Coerce None to empty string to handle optional input gracefully.
        """
        if v is None:
            return ""  # Convert None to empty string
        if not isinstance(v, str):
            raise ValueError("description must be a string")
        return v
```

#### ItemUpdate (Partial Update Input)
```python
class ItemUpdate(BaseModel):
    name: str | None = None      # Optional: None = don't update
    description: str | None = None  # Optional: None = don't update
    
    @field_validator('description', mode='before')
    @classmethod
    def coerce_null_description_on_write(cls, v):
        """
        For updates, explicit None means 'don't update this field'.
        If provided, coerce to empty string, never allow actual NULL storage.
        """
        if v is None:
            return None  # None = don't update
        if not isinstance(v, str):
            raise ValueError("description must be a string")
        return v
```

#### Item (Read Output)
```python
class Item(ItemBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
    
    # No read-time validator - legacy NULLs handled via migration
```

**Benefits**:
- ✓ Validation happens at schema input (write time)
- ✓ Type checker sees `description: str` (non-optional)
- ✓ Impossible to create/update with NULL description
- ✓ Legacy NULLs handled separately via migration
- ✓ Clear semantics: None in ItemUpdate = skip update

## Validation Flow

### Create Item Flow
```python
# Client request
POST /items {
  "name": "My Item",
  "description": null  # Or omitted
}

# Pydantic validation (ItemCreate -> ItemBase)
validator('description', mode='before') triggers:
  if v is None:
    return ""  # Convert None to empty string
  return v
# Result: description = ""

# CRUD layer
db_item = models.Item(name=item.name, description=item.description)
# description = "" (not NULL)

# Database
INSERT INTO items (name, description) VALUES ('My Item', '');
# ✓ Empty string, not NULL
```

### Update Item Flow
```python
# Client request
PUT /items/42 {
  "name": "Updated"
  // description omitted
}

# Pydantic validation (ItemUpdate)
validator('description', mode='before') triggers:
  if v is None:
    return None  # None = don't update
  return v
# Result: description = None

# CRUD layer
if item.description is not None:
    db_item.description = item.description  # Skipped
# Only name is updated

# Database
UPDATE items SET name = 'Updated' WHERE id = 42;
# ✓ description unchanged
```

### Update Item with Empty Description
```python
# Client request
PUT /items/42 {
  "description": ""  // Explicit empty string
}

# Pydantic validation
validator('description', mode='before') triggers:
  if v is None:
    return None
  return ""  # Empty string passes through
# Result: description = ""

# CRUD layer
if item.description is not None:
    db_item.description = item.description  # Updated
# description is updated to ""

# Database
UPDATE items SET description = '' WHERE id = 42;
# ✓ Empty string update applied
```

## Handling Legacy NULL Descriptions

### Migration Strategy (Two-Phase)

**Phase 1: Backfill NULLs**
```sql
-- migration_backfill_description.py
UPDATE items SET description = '' WHERE description IS NULL;
```

**Phase 2: Add Constraint**
```sql
-- After Phase 1 completes
ALTER TABLE items ALTER COLUMN description SET NOT NULL;
```

### CRUD Layer Integration

The CRUD layer no longer needs to handle NULL descriptions:

```python
def create_item(db: Session, item: schemas.ItemCreate) -> models.Item:
    # Schema validator guarantees item.description is a string
    db_item = models.Item(name=item.name, description=item.description)
    db.add(db_item)
    try:
        db.commit()
        db.refresh(db_item)
    except Exception:
        db.rollback()
        logger.exception("Database error occurred while creating item")
        raise Exception("Failed to create item")
    return db_item
```

No special handling needed - schema validation is upstream.

## Type Safety Improvements

### Before
```python
description: Optional[str] = None  # Confusing: says it's optional

# Type checker sees:
result = create_item(...)
result.description  # Is this str or None?  # Unclear
```

### After
```python
description: str  # Clear: always a string

# Type checker sees:
result = create_item(...)
result.description  # str  # Clear!
```

## Validation Examples

### Success Cases

```python
# Create with explicit description
ItemCreate(name="Item", description="A description")
# ✓ description = "A description"

# Create with None (coerced to empty string)
ItemCreate(name="Item", description=None)
# ✓ description = ""

# Create with omitted description (defaults to None, then coerced)
ItemCreate(name="Item")
# ✗ Error: description field required

# Update with description
ItemUpdate(name="Item", description="New desc")
# ✓ description = "New desc"

# Update without description (don't update field)
ItemUpdate(name="Item")
# ✓ description = None (don't update)

# Update with explicit empty string
ItemUpdate(description="")
# ✓ description = "" (update to empty string)
```

### Error Cases

```python
# Create with non-string description
ItemCreate(name="Item", description=123)
# ✗ ValueError: description must be a string

# Create with list
ItemCreate(name="Item", description=["list"])
# ✗ ValueError: description must be a string

# Create with dict
ItemCreate(name="Item", description={"key": "value"})
# ✗ ValueError: description must be a string
```

## API Behavior Changes

### Before
```http
POST /items
{
  "name": "My Item"
}
Response:
201 Created
{
  "id": 1,
  "name": "My Item",
  "description": null  // Problematic
}
```

### After
```http
POST /items
{
  "name": "My Item"
}
Response:
400 Bad Request
{
  "detail": [
    {
      "loc": ["body", "description"],
      "msg": "Field required",
      "type": "missing"
    }
  ]
}

// Correct usage:
POST /items
{
  "name": "My Item",
  "description": ""  // Required, can be empty
}
Response:
201 Created
{
  "id": 1,
  "name": "My Item",
  "description": ""  // Empty string, not null
}
```

## Client Migration Guide

### Scenario 1: Client sends description
**Before**: Works as-is  
**After**: Works as-is  
```json
{"name": "Item", "description": "My description"}
```

### Scenario 2: Client omits description
**Before**: Accepted, stored as NULL  
**After**: Error, must provide description field  
```json
{"name": "Item"}
// Error: description field required
```

### Fix
```json
{"name": "Item", "description": ""}  // Provide empty string
```

### Scenario 3: Client sends description: null
**Before**: Accepted, stored as NULL  
**After**: Coerced to empty string  
```json
{"name": "Item", "description": null}
// Now: coerced to "", stored as empty string
```

### Scenario 4: Update without changing description
**Before**: Omitting description would set it to NULL  
**After**: Omitting description leaves it unchanged  
```http
PUT /items/1
{"name": "Updated"}
// Before: description would be set to NULL
// After: description unchanged
```

## Testing

### Unit Tests for Validation

```python
import pytest
from schemas import ItemCreate, ItemUpdate

def test_item_create_with_description():
    item = ItemCreate(name="test", description="my desc")
    assert item.description == "my desc"

def test_item_create_with_none_description():
    """None is coerced to empty string"""
    item = ItemCreate(name="test", description=None)
    assert item.description == ""

def test_item_create_without_description():
    """Missing description raises error"""
    with pytest.raises(ValidationError) as exc_info:
        ItemCreate(name="test")
    assert "description" in str(exc_info.value).lower()

def test_item_create_with_non_string_description():
    """Non-string description raises error"""
    with pytest.raises(ValidationError) as exc_info:
        ItemCreate(name="test", description=123)
    assert "string" in str(exc_info.value).lower()

def test_item_update_with_description():
    item = ItemUpdate(name="test", description="new")
    assert item.description == "new"

def test_item_update_without_description():
    """Omitting description means None (don't update)"""
    item = ItemUpdate(name="test")
    assert item.description is None
    assert item.name == "test"

def test_item_update_with_none_description():
    """Explicit None means don't update"""
    item = ItemUpdate(description=None)
    assert item.description is None

def test_item_update_with_empty_string():
    """Empty string is a valid update"""
    item = ItemUpdate(description="")
    assert item.description == ""
```

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Validation** | Read-time (on mapping) | Write-time (on schema) |
| **Type hint** | `Optional[str] = None` | `str` |
| **None handling** | Stored as NULL | Coerced to empty string |
| **Enforcement** | Only on read | At write and database |
| **Legacy NULLs** | Handled on read | Handled via migration |
| **Type safety** | Unclear if NULL possible | Clear: never NULL |
| **API contract** | Ambiguous | Explicit: description required |

## Benefits

✓ **Write-time validation** - Prevents invalid state at source  
✓ **Type safety** - Type checker knows description is string  
✓ **No read-time surprises** - Schema always valid  
✓ **Clear semantics** - None in Update = skip update  
✓ **Migration-friendly** - Legacy NULLs handled separately  
✓ **Better errors** - Validation errors at request time  
✓ **Consistent behavior** - No special read-time coercion  
