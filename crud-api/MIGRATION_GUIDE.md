# Database Migration Guide: Description Column NOT NULL

## Overview

This guide explains the two-phase migration for making the `items.description` column NOT NULL. This is a breaking change for existing databases with NULL description values.

## Migration Steps

### Phase 1: Backfill NULL Values

**When**: Before deploying code changes
**What**: Updates all existing rows with NULL descriptions to empty string

```bash
python migration_backfill_description.py
```

**What happens**:
1. ✓ Backfills all NULL descriptions with empty string (`''`)
2. ✓ Verifies no NULL descriptions remain
3. ✓ Applies `server_default=''` to handle new inserts during transition

**Database changes**:
- `ALTER TABLE items ALTER COLUMN description SET DEFAULT ''`
- `UPDATE items SET description = '' WHERE description IS NULL`

### Phase 2: Add NOT NULL Constraint

**When**: After Phase 1 completes successfully and testing is complete
**What**: Alters the column to enforce NOT NULL at database level

```bash
python migration_backfill_description.py --phase2
```

**What happens**:
1. ✓ Adds NOT NULL constraint to description column
2. ✓ Verifies constraint is enforced (tries to insert NULL, expects failure)

**Database changes**:
- PostgreSQL: `ALTER TABLE items ALTER COLUMN description SET NOT NULL`
- MySQL: `ALTER TABLE items MODIFY COLUMN description VARCHAR(255) NOT NULL`
- SQLite: Requires manual migration (table recreation)

### Full Migration (Both Phases)

```bash
python migration_backfill_description.py --full
```

## Code Changes

### 1. Models (models.py)

**Before**:
```python
description = Column(String)  # Nullable
```

**After**:
```python
description = Column(String, nullable=True, server_default='')  # Server default for safety
```

**After Phase 2**:
```python
description = Column(String, nullable=False)  # NOT NULL constraint
```

### 2. Schemas (schemas.py)

**ItemCreate**:
- Inherits from `ItemBase`
- `description: Optional[str] = None` (allows clients to omit field)
- Creates with empty string if None (see crud.py)

**ItemUpdate**:
- `name: str | None = None`
- `description: str | None = None`
- Enables true partial updates

### 3. CRUD Operations (crud.py)

**create_item**:
- Always provides a description (defaults to empty string if None)
- Example: `description = item.description if item.description is not None else ""`

**update_item**:
- Only updates fields that are explicitly provided (not None)
- Allows partial updates without affecting other fields

**delete_item**:
- No changes needed, but wrapped in try/except for safety

## Testing

### Pre-Migration Testing

```python
# Test 1: Verify current state
SELECT COUNT(*) as null_descriptions FROM items WHERE description IS NULL;

# Test 2: Create item without description
curl -X POST /items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item"}'

# Expected: description defaults to empty string or error (depending on client)
```

### Post-Migration Testing

```python
# Test 1: Verify constraint
SELECT * FROM items WHERE description IS NULL;
# Expected: Empty result set

# Test 2: Try to insert NULL (should fail)
INSERT INTO items (name, description) VALUES ('test', NULL);
# Expected: Error - "description cannot be NULL"

# Test 3: Create item with description
curl -X POST /items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "description": "A test item"}'
# Expected: Success

# Test 4: Create item without description (should use schema default)
curl -X POST /items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test"}'
# Expected: description set to empty string
```

## Rollback Plan

If issues occur during migration:

### Before Phase 2:
1. Simply don't run Phase 2
2. Code continues to work with `nullable=True`
3. New inserts get empty string default
4. Existing NULL values are already backfilled

### After Phase 2:
1. Manually run: `ALTER TABLE items ALTER COLUMN description DROP NOT NULL` (PostgreSQL)
2. Revert models.py to `nullable=True`
3. Redeploy code

## Database-Specific Notes

### PostgreSQL
- Supports both phases without issue
- Use `SET NOT NULL` syntax
- Can set server defaults easily

### MySQL
- Supports both phases without issue
- Use `MODIFY COLUMN` syntax
- Ensure character set is compatible

### SQLite
- **Does not support** `ALTER COLUMN NOT NULL` directly
- Requires table recreation
- Use Alembic for proper SQLite migrations:
  ```bash
  pip install alembic
  alembic revision --autogenerate -m "Make description NOT NULL"
  alembic upgrade head
  ```

## Deployment Timeline

### Week 1: Prepare
- [ ] Review this guide
- [ ] Deploy code with `nullable=True, server_default=''`
- [ ] Backup database

### Week 2: Phase 1 Migration
- [ ] Run Phase 1 in staging
- [ ] Test for 24+ hours
- [ ] Run Phase 1 in production (during low-traffic window)

### Week 3: Phase 2 Migration
- [ ] Run Phase 2 in staging
- [ ] Verify constraint works
- [ ] Run Phase 2 in production

### Week 4+: Monitor
- [ ] Watch logs for any errors
- [ ] Verify no new NULL descriptions appear
- [ ] Update documentation

## FAQ

**Q: Can I skip Phase 1?**
A: No. Phase 2 will fail if NULL values exist. You must backfill first.

**Q: What if Phase 1 fails?**
A: Check the error message. Common issues:
- Database connection: verify DATABASE_URL is correct
- Table doesn't exist: run `models.Base.metadata.create_all()`
- Permission denied: check database user permissions

**Q: Can I run Phase 2 without Phase 1?**
A: No. The script will refuse to proceed if Phase 1 hasn't completed.

**Q: What about existing API clients?**
A: They continue to work as before. Omitting description is still allowed (defaults to empty string).

**Q: Will this downtime?**
A: Minimal. Both phases take seconds on small tables (<1M rows).

## Support

For issues or questions:
1. Check MIGRATION_GUIDE.md (this file)
2. Review the migration_backfill_description.py script
3. Check database logs for constraint violations
4. Contact the DBA team
