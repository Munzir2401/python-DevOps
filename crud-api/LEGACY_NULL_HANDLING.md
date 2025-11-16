# Handling Legacy NULL Descriptions: Migration Strategy

## Overview

With write-time schema validation now enforced, existing NULL descriptions in the database need to be handled via the migration process rather than read-time coercion.

## Current State

### Database Side
- **Before Migration**: Database may contain NULL descriptions (legacy data)
- **After Phase 1**: All NULLs converted to empty strings
- **After Phase 2**: NOT NULL constraint prevents any NULLs

### Schema Side
- **Before**: Item.read validator coerced NULL to "" on read
- **After**: No read-time coercion - relies on migration

## Migration Execution Plan

### Phase 1: Backfill NULL Values

**File**: `migration_backfill_description.py`

**Command**:
```bash
python migration_backfill_description.py
```

**What it does**:
```sql
-- Backfill all existing NULL descriptions
UPDATE items SET description = '' WHERE description IS NULL;

-- Verify no NULLs remain
SELECT COUNT(*) FROM items WHERE description IS NULL;
-- Result: 0 (all NULLs converted)
```

**Timeline**:
1. ✓ Run in staging environment first
2. ✓ Verify all NULLs converted (no errors)
3. ✓ Run in production during low-traffic window
4. ✓ Allow 24 hours for stability testing

### Phase 2: Add Database Constraint

**Command**:
```bash
python migration_backfill_description.py --phase2
```

**What it does**:
```sql
-- PostgreSQL
ALTER TABLE items ALTER COLUMN description SET NOT NULL;

-- MySQL
ALTER TABLE items MODIFY COLUMN description VARCHAR(255) NOT NULL;
```

**Timeline**:
1. ✓ Run after Phase 1 completes successfully
2. ✓ Verify constraint is enforced
3. ✓ Test that NULL inserts are rejected

## Handling Requests During Migration

### Timeline: During Phase 1 (Before Schema Change)

**Database State**:
- ❌ NULLs exist (being backfilled)
- ✓ Empty strings exist

**Schema Code**:
- ❌ Old code still in production (if deploying sequentially)

**Result**:
- Requests still work as before
- New data doesn't create NULLs (if new code deployed)

### Timeline: After Phase 1, Before Phase 2 (Schema Change Deployed)

**Database State**:
- ✓ All NULLs converted to ""
- No NULLs exist

**Schema Code**:
- ✓ New schema validation deployed
- ✓ Write-time validation enforces description: str
- ❌ No read-time coercion

**Result**:
- ✓ All requests work correctly
- ✓ New creates always get string description
- ✓ No NULLs possible from new requests
- ✓ No NULLs in database from Phase 1

### Timeline: After Phase 2

**Database State**:
- ✓ All NULLs converted to ""
- ✓ NOT NULL constraint prevents any NULLs
- ✓ Defense in depth

**Schema Code**:
- ✓ Write-time validation active
- ✓ No read-time coercion needed

**Result**:
- ✓ Complete safety
- ✓ Schema validation + database constraint

## Deployment Strategy

### Option 1: Sequential (Safer)

```
Week 1:
  ├─ Run Migration Phase 1
  ├─ Verify all NULLs converted
  └─ ✓ Complete

Week 2:
  ├─ Deploy new schema code (write-time validation)
  ├─ Test for 24 hours
  └─ ✓ Verified

Week 3:
  ├─ Run Migration Phase 2
  ├─ Add NOT NULL constraint
  └─ ✓ Complete

Week 4:
  └─ Monitor for issues
```

**Advantages**:
- ✓ Each phase tested independently
- ✓ Easy rollback if needed
- ✓ Low risk

### Option 2: Concurrent (Faster)

```
Week 1:
  ├─ Run Migration Phase 1
  ├─ Deploy new schema code
  └─ Both completing simultaneously

Week 2:
  ├─ Verify Phase 1 complete
  ├─ Run Migration Phase 2
  └─ Add NOT NULL constraint

Week 3:
  └─ Monitor for issues
```

**Advantages**:
- ✓ Faster overall
- ✓ Phase 1 and Phase 2 can overlap

**Requirements**:
- ✓ Phase 1 must complete before Phase 2
- ✓ Code must handle NULL descriptions during transition

## Handling the Transition

### Code Logic During Migration

The migration script (`migration_backfill_description.py`) handles the transition automatically:

```python
def phase_1_backfill_nulls():
    """
    Phase 1: Backfill existing NULL descriptions with empty string
    
    This is safe to run before deploying new code because:
    1. Existing NULLs are converted to ""
    2. New requests continue to work normally
    3. Database remains consistent throughout
    """
    result = connection.execute(
        text("UPDATE items SET description = '' WHERE description IS NULL")
    )
    # Verify
    verify_result = connection.execute(
        text("SELECT COUNT(*) as null_count FROM items WHERE description IS NULL")
    )
    null_count = verify_result.scalar()
    assert null_count == 0, f"Migration failed: {null_count} NULLs remain"
```

### After Phase 1, Before Phase 2

**If old schema code still running**:
```python
# Old code (before changes)
class Item(ItemBase):
    @field_validator('description', mode='before')
    def coerce_null_description(cls, v):
        if v is None:
            return ""
        return v

# This still works because:
# 1. Phase 1 already converted NULLs to ""
# 2. No new NULLs can exist
# 3. Read-time coercion has nothing to coerce
```

**If new schema code running**:
```python
# New code (after changes)
class ItemBase(BaseModel):
    description: str  # Required, write-time validation
    
    @field_validator('description', mode='before')
    def coerce_null_description_on_write(cls, v):
        if v is None:
            return ""
        return v

# This also works because:
# 1. Phase 1 already converted NULLs to ""
# 2. New requests always provide description (or coerce None)
# 3. No read-time coercion needed
```

## Rollback Procedures

### If Phase 1 Fails

**Action**:
- Stop migration, do not proceed to Phase 2
- Errors from Phase 1 are logged
- Database remains unchanged

**Recovery**:
```bash
# Review errors
python migration_backfill_description.py

# Fix issue (e.g., database connection)
# Then retry
python migration_backfill_description.py
```

### If Phase 2 Fails

**Action**:
- Phase 1 already complete (NULLs converted)
- Phase 2 failed to add constraint
- Database is still consistent (no NULLs exist)

**Recovery**:
```bash
# Option 1: Try again
python migration_backfill_description.py --phase2

# Option 2: Manual constraint addition
# PostgreSQL:
ALTER TABLE items ALTER COLUMN description SET NOT NULL;

# MySQL:
ALTER TABLE items MODIFY COLUMN description VARCHAR(255) NOT NULL;
```

### If Code Rollback Needed

**Scenario**: New code deployed, but issues found

**Rollback**:
1. Revert to old code (with read-time validator)
2. Phase 1 completed (all NULLs → "")
3. Old code works fine because NULLs already gone

**Rollback Safety**:
- ✓ Safe because Phase 1 already completed
- ✓ No NULLs exist to trigger old coercion
- ✓ Can roll forward again anytime

## Verification Checklist

### After Phase 1

- [ ] No NULL descriptions in database
  ```sql
  SELECT COUNT(*) FROM items WHERE description IS NULL;
  -- Should return 0
  ```

- [ ] All descriptions are strings
  ```sql
  SELECT DISTINCT description FROM items LIMIT 10;
  -- Should show strings, no NULLs
  ```

- [ ] Application works normally
  ```bash
  # Test basic operations
  curl -X GET /items
  curl -X POST /items -d '{"name": "test", "description": ""}'
  curl -X PUT /items/1 -d '{"name": "updated"}'
  curl -X DELETE /items/1
  ```

### After Phase 2

- [ ] NULL constraint exists
  ```sql
  -- PostgreSQL
  SELECT column_name, is_nullable 
  FROM information_schema.columns 
  WHERE table_name = 'items' AND column_name = 'description';
  -- Should show "NO" for is_nullable

  -- MySQL
  DESCRIBE items;
  -- Should show "NOT NULL" for description
  ```

- [ ] NULL inserts are rejected
  ```sql
  INSERT INTO items (name, description) VALUES ('test', NULL);
  -- Should fail with constraint error
  ```

- [ ] Application continues working
  ```bash
  # All operations should still work
  curl -X GET /items
  curl -X POST /items -d '{"name": "test", "description": "desc"}'
  ```

## Monitoring During Migration

### Phase 1 Execution

```bash
# Terminal 1: Monitor migration
python migration_backfill_description.py

# Terminal 2: Monitor database
watch -n 5 'psql $DATABASE_URL -c "SELECT COUNT(*) FROM items WHERE description IS NULL;"'
```

**Expected Output**:
```
Phase 1: Starting backfill of NULL descriptions...
✓ Phase 1 complete: 1234 rows updated
✓ Verification: 0 NULL descriptions remaining
✓ All NULL descriptions have been backfilled!
```

### Application Logging

Check application logs for any errors during migration:

```bash
# Check for validation errors
tail -f /var/log/app/crud.log | grep -E "(error|exception)" -i

# Check for database errors
tail -f /var/log/app/crud.log | grep -E "(database|constraint)" -i
```

## FAQ

**Q: Can I deploy new code before running Phase 1?**

A: No. Deploy new code only after Phase 1 completes.

**Q: What if Phase 1 fails halfway through?**

A: Stop immediately. The database remains consistent. Fix the issue and retry - only remaining NULLs will be converted.

**Q: What if Phase 2 fails?**

A: Phase 1 is already complete (all NULLs gone). The database is consistent. Phase 2 just adds a safety constraint. Fix the issue and retry.

**Q: Can I run Phase 2 without Phase 1?**

A: No. Phase 2 will fail if any NULLs exist. Must complete Phase 1 first.

**Q: Should I run phases in production or staging first?**

A: Always run in staging first to verify. Then run in production during low-traffic window.

**Q: How long do phases take?**

A: Depends on table size. Small tables (<100K rows): seconds. Large tables: minutes.

**Q: Can requests run during migration?**

A: Yes. Migrations don't lock the table long enough to affect requests. But test in staging first.

**Q: What about backup before migration?**

A: Always back up production database before running migrations. The script is safe, but backups are insurance.

## References

- Migration Script: `migration_backfill_description.py`
- Migration Guide: `MIGRATION_GUIDE.md`
- Schema Validation: `SCHEMA_VALIDATION_IMPROVEMENTS.md`
- Write-Time Validation: `WRITE_TIME_VALIDATION_SUMMARY.md`
