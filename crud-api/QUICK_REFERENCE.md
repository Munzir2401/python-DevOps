# CRUD API - Quick Reference Guide

## Project at a Glance

**What It Is**: A REST API for managing items (Create, Read, Update, Delete)  
**Technology**: FastAPI + PostgreSQL + Auth0  
**Purpose**: Production-grade backend with security, validation, and reliability

## The Five Core Files

### 1. **main.py** - The Web Server
- Receives HTTP requests
- Validates authentication (Auth0 JWT)
- Routes requests to handlers
- Returns JSON responses

### 2. **schemas.py** - Request/Response Validation
- Defines what data looks like
- Validates incoming requests
- Transforms data (e.g., null → "")
- Serializes responses

### 3. **models.py** - Database Structure
- Defines database table structure
- One table: `items` with id, name, description
- SQLAlchemy converts this to SQL

### 4. **crud.py** - Business Logic
- get_items() - List all items
- create_item() - Create new item
- update_item() - Update existing item
- delete_item() - Delete item

### 5. **database.py** - Database Connection
- Manages PostgreSQL connection pool
- Provides sessions to routes
- Handles connection pooling and recycling

## Request Flow (Simple Version)

```
1. Client sends HTTP request with JWT token
2. FastAPI verifies the JWT with Auth0
3. Pydantic schema validates request body
4. Database session is created
5. CRUD function executes SQL
6. Data is committed to PostgreSQL
7. Response is serialized to JSON
8. Database session is closed
9. Response sent to client
```

## Key Technologies

| Technology | Purpose | Example |
|------------|---------|---------|
| FastAPI | Web framework | @app.post("/items") |
| PostgreSQL | Database | items table |
| SQLAlchemy | Database ORM | models.Item |
| Pydantic | Validation | ItemCreate schema |
| Auth0 | Authentication | JWT tokens |
| PyJWT | Token verification | jwt.decode() |

## Database Connection Pool

```
Pool Size: 10 connections ready
Max Overflow: 20 extra when needed
Pre-ping: Test connection before use
Recycle: Replace after 1 hour

Result: Fast, reliable database access
```

## Error Responses by Status Code

| Status | When | Example |
|--------|------|---------|
| 200 | Success GET  | Retrieved items    |
| 201 | Success POST | Created item       |
| 400 | Bad request  | Invalid JSON       |
| 401 | Auth failed  | Missing token      |
| 404 | Not found    | Item doesn't exist |
| 500 | Server error | Database down |

## Environment Variables Needed

```
DATABASE_URL=postgresql://user:pass@host:5432/db
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_API_AUDIENCE=your-api-id
```

## Common Operations

### Create Item
```bash
curl -X POST http://localhost:8000/items \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Item", "description": "Desc"}'
```

### Get Items
```bash
curl http://localhost:8000/items \
  -H "Authorization: Bearer TOKEN"
```

### Update Item
```bash
curl -X PUT http://localhost:8000/items/1 \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated"}'
```

### Delete Item
```bash
curl -X DELETE http://localhost:8000/items/1 \
  -H "Authorization: Bearer TOKEN"
```

## Validation Layers

1. **Schema Validation** - Pydantic checks JSON structure
2. **Custom Validators** - Coerce null to empty string
3. **Database Constraints** - SQL-level restrictions
4. **Application Logic** - Business rule enforcement

## Authentication Flow

1. User logs into Auth0 → Gets JWT token
2. Client sends token in Authorization header
3. API extracts token from header
4. API fetches JWKS (public keys) from Auth0 (cached 1 hour)
5. API verifies token signature with public key
6. API decodes token to get user info
7. Request proceeds or returns 401

## Transaction Safety

```python
db.add(item)       # Stage change
db.commit()        # Apply to database (or abort if error)
db.refresh(item)   # Reload updated data
                   # If error: db.rollback() (undo)
```

Result: Never partial updates, always consistent data

## Logging Strategy

**Client sees**: Generic error messages (e.g., "Failed to create item")  
**Server logs**: Full error details with stack traces

This prevents leaking system information to potential attackers.

## Type Safety

```python
# Before: Unclear types
result.description  # Is this str or None?

# After: Clear types
description: str    # Always a string
@field_validator
def validate(v):
    return "" if v is None else v
```

Type hints + Validators = No ambiguity

## Performance Optimizations

1. **Connection Pooling** - Reuse database connections
2. **JWKS Caching** - Cache public keys for 1 hour
3. **Database Indexes** - Fast lookups on id and name
4. **Query Efficiency** - Minimal database calls

## Security Measures

1. **JWT Authentication** - Only authenticated users can modify data
2. **JWKS Validation** - Token must be signed by Auth0
3. **Error Sanitization** - No sensitive data to clients
4. **Transaction Rollback** - Prevents corrupted data
5. **Input Validation** - Rejects invalid requests

## Deployment

### Development
```bash
uvicorn main:app --reload
# Single process, auto-restarts on code changes
# http://localhost:8000
```

### Production
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
# 4 processes for concurrent requests
# Behind nginx reverse proxy with HTTPS
```

## Quick Start Checklist

- [ ] PostgreSQL installed and running
- [ ] Environment variables set in .env file
- [ ] Auth0 account and credentials configured
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] API started: `uvicorn main:app --reload`
- [ ] Swagger documentation: http://localhost:8000/docs
- [ ] Test endpoints with valid JWT token

## If Something Goes Wrong

| Problem | First Check |
|---------|-------------|
| 401 Unauthorized | Token in Authorization header? Valid? |
| 400 Bad Request | Request JSON matches schema? |
| 404 Not Found | Item ID exists in database? |
| 500 Error | Is PostgreSQL running? Check logs |
| Slow requests | Check connection pool, database query performance |

## Documentation Files

- `README.md` - Setup and usage
- `PROJECT_DEEP_DIVE.md` - Complete explanation (this level)
- `MIGRATION_GUIDE.md` - Database migrations
- `SCHEMA_VALIDATION_IMPROVEMENTS.md` - Validation details
- `SECURITY_ERROR_HANDLING.md` - Error handling details
- `TYPE_SAFETY_IMPROVEMENTS.md` - Type system benefits

## Key Takeaways

1. **FastAPI** handles HTTP and automatic Swagger docs
2. **Pydantic** validates all data at request time
3. **SQLAlchemy** converts Python to SQL
4. **PostgreSQL** is the actual data storage
5. **Auth0** provides authentication
6. **Connection pooling** makes it fast
7. **Transactions** make it reliable
8. **Logging** makes it debuggable
