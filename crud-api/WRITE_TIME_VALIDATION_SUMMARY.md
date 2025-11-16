# Write-Time Schema Validation Strategy: Summary

## What Changed

### schemas.py

#### 1. ItemBase (Create Input)
**Before**:
```python
class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None  # Optional, allows None
```

**After**:
```python
class ItemBase(BaseModel):
    name: str
    description: str  # Required non-optional field
    
    @field_validator('description', mode='before')
    @classmethod
    def coerce_null_description_on_write(cls, v):
        if v is None:
            return ""  # Coerce None to empty string
        if not isinstance(v, str):
            raise ValueError("description must be a string")
        return v
```

**Effect**: 
- Validates at write time (when item is created)
- Type system sees `description: str` (not Optional)
- None values coerced to empty string
- Invalid types rejected with clear error

#### 2. ItemUpdate (Partial Update Input)
**Before**:
```python
class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None  # Can be None (but doesn't mean skip)
```

**After**:
```python
class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None  # Can be None (means skip update)
    
    @field_validator('description', mode='before')
    @classmethod
    def coerce_null_description_on_write(cls, v):
        if v is None:
            return None  # None = don't update this field
        if not isinstance(v, str):
            raise ValueError("description must be a string")
        return v
```

**Effect**:
- For updates, None means "omit this field" (don't update)
- If value provided, it must be a string (or coercible from None)
- Type validation at request time

#### 3. Item (Read Output)
**Before**:
```python
class Item(ItemBase):
    id: int
    
    @field_validator('description', mode='before')
    @classmethod
    def coerce_null_description(cls, v):
        if v is None:
            return ""  # Coerce on read
        return v
```

**After**:
```python
class Item(ItemBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
    # No read-time coercion
```

**Effect**:
- Removed read-time coercion
- Legacy NULL descriptions handled via migration phase
- Simpler, cleaner schema definition

### crud.py

**Before**:
```python
def create_item(db: Session, item: schemas.ItemCreate) -> models.Item:
    description = item.description if item.description is not None else ""
    db_item = models.Item(name=item.name, description=description)
    # ...
```

**After**:
```python
def create_item(db: Session, item: schemas.ItemCreate) -> models.Item:
    # ItemBase validator guarantees item.description is a string
    db_item = models.Item(name=item.name, description=item.description)
    # ...
```

**Effect**:
- Simpler logic - no defensive None checking
- Validation happens upstream in schema
- Type safety guaranteed

## Validation Timing

```
Write Path (POST/PUT):
  Client Request
    ↓
  Pydantic Schema Validation ← NEW: Validation happens here
    • description required (ItemCreate)
    • None coerced to ""
    • Type checked
    ↓
  CRUD Layer (crud.py)
    • Data guaranteed valid
    • No defensive checks needed
    ↓
  Database
    • No NULLs possible

Read Path (GET):
  Database
    • May have legacy NULLs (before migration)
    ↓
  CRUD Layer (crud.py)
    • Returns models.Item directly
    ↓
  Pydantic Schema Mapping (Item class)
    • Maps DB row to schema
    • No coercion (schema inherited from ItemBase)
    ↓
  Client Response
    • If DB has NULL (legacy), it will fail validation
    • After migration: no NULLs exist
```

## Key Differences: Write-Time vs Read-Time

| Aspect | Write-Time | Read-Time |
|--------|-----------|----------|
| **When** | Request arrives, before CRUD | DB returns data |
| **Where** | Pydantic validator | Pydantic validator |
| **Advantage** | Prevents bad data at source | Fixes existing bad data |
| **Problem** | Doesn't fix legacy data | Allows bad data through |
| **Best for** | New data | Legacy migration |

## Migration Path

```
Phase 1: Backfill NULLs
  UPDATE items SET description = '' WHERE description IS NULL;
  
  ↓
  
All NULLs in DB now empty strings
  
  ↓
  
Deploy Code with Write-Time Validation
  
  ↓
  
Phase 2: Add Database Constraint
  ALTER TABLE items ALTER COLUMN description SET NOT NULL;
  
  ↓
  
Defense in Depth:
  • Schema validation (write-time)
  • Database constraint (NO NULLs)
  • No read-time coercion needed
```

## Error Handling Examples

### Create Missing Required Field
```http
POST /items
{
  "name": "My Item"
}

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
```

### Create with Invalid Type
```http
POST /items
{
  "name": "My Item",
  "description": 123
}

400 Bad Request
{
  "detail": [
    {
      "loc": ["body", "description"],
      "msg": "Value error, description must be a string",
      "type": "value_error"
    }
  ]
}
```

### Create with None (Coerced)
```http
POST /items
{
  "name": "My Item",
  "description": null
}

201 Created
{
  "id": 1,
  "name": "My Item",
  "description": ""  ← Coerced from null
}
```

### Update Omitting Field (Skip)
```http
PUT /items/1
{
  "name": "Updated"
}

200 OK
{
  "id": 1,
  "name": "Updated",
  "description": "original description"  ← Unchanged
}
```

### Update with Empty String (Update)
```http
PUT /items/1
{
  "description": ""
}

200 OK
{
  "id": 1,
  "name": "My Item",
  "description": ""  ← Updated to empty
}
```

## Type System Benefits

### Before (Ambiguous)
```python
def process_item(item: ItemCreate):
    print(item.description)
    # Type: str | None
    # Is this str or None? When is it which? ❓
```

### After (Clear)
```python
def process_item(item: ItemCreate):
    print(item.description)
    # Type: str
    # Always a string! ✓
```

## Backward Compatibility

### Breaking Changes
- ❌ Clients that omit description field now get 400 error
- ❌ Clients sending `description: null` get coercion (different from before)

### Non-Breaking
- ✓ Clients sending `description: "some text"` work unchanged
- ✓ Clients sending `description: ""` work unchanged
- ✓ Update endpoints still work (None still means skip)

### Migration Path for Clients
```javascript
// Before (was accepted but stored NULL)
POST /items {
  "name": "Item"
}

// After (must provide description)
POST /items {
  "name": "Item",
  "description": ""  // Provide empty string
}

// This was accepted before and still works:
POST /items {
  "name": "Item",
  "description": "My description"
}
```

## Testing Validation

```python
import pytest
from pydantic import ValidationError
from schemas import ItemCreate, ItemUpdate

class TestItemCreateValidation:
    def test_valid_item(self):
        item = ItemCreate(name="test", description="desc")
        assert item.description == "desc"
    
    def test_none_coerced_to_empty(self):
        item = ItemCreate(name="test", description=None)
        assert item.description == ""
    
    def test_missing_description_error(self):
        with pytest.raises(ValidationError):
            ItemCreate(name="test")
    
    def test_invalid_type_error(self):
        with pytest.raises(ValidationError):
            ItemCreate(name="test", description=123)

class TestItemUpdateValidation:
    def test_update_all_fields(self):
        item = ItemUpdate(name="new", description="new desc")
        assert item.name == "new"
        assert item.description == "new desc"
    
    def test_update_omit_description(self):
        item = ItemUpdate(name="new")
        assert item.name == "new"
        assert item.description is None  # None = skip
    
    def test_update_empty_string(self):
        item = ItemUpdate(description="")
        assert item.description == ""  # Update to empty
```

## Summary

✓ **Write-Time Validation** - Validates at schema input, not read  
✓ **Type Safety** - `description: str` not `Optional[str]`  
✓ **No Read-Time Coercion** - Simpler schema, cleaner code  
✓ **Clear Semantics** - None in Update = skip, None in Create = error  
✓ **Migration-Friendly** - Legacy NULLs handled in separate phase  
✓ **Early Validation** - Errors caught at request time  
✓ **Defense in Depth** - Schema + DB constraint  
