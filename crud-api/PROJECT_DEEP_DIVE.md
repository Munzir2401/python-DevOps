# CRUD API - Complete End-to-End Project Guide

This document provides a complete explanation of the CRUD API project, covering every component, dependency, and flow to ensure you fully own and understand the project.

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Core Components](#core-components)
5. [Request/Response Flow](#requestresponse-flow)
6. [Authentication Flow](#authentication-flow)
7. [Database Layer](#database-layer)
8. [Data Validation](#data-validation)
9. [Error Handling](#error-handling)
10.[Deployment](#deployment)
11.[Troubleshooting](#troubleshooting)

## Project Overview

The CRUD API is a production-grade REST API for managing items. It provides secure Create, Read, Update, and Delete operations with the following key characteristics:

- **Type-Safe**: Full type hints throughout the codebase
- **Secure**: Auth0 JWT authentication with JWKS validation
- **Reliable**: Transaction management with automatic rollback on errors
- **Observable**: Comprehensive logging for debugging and monitoring
- **Maintainable**: Clean architecture with separation of concerns

### What the API Does

At its core, the API allows authenticated users to:

1. Create items with a name and description
2. Retrieve all items
3. Update existing items (partially or fully)
4. Delete items

All operations require authentication except for health checks and the root endpoint.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser/App)                 │
│                                                             │
│  Sends: HTTP Request with JWT Token in Authorization Header │
│  Receives: JSON Response with item data or error messages   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    HTTP (Port 8000)
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│                    FASTAPI APPLICATION                     │
│                                                            │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │   main.py        │  │   schemas.py     │                │
│  │  (Routes)        │  │  (Validation)    │                │
│  └──────────────────┘  └──────────────────┘                │
│         │                       │                          │
│         └───────────┬───────────┘                          │
│                     │                                      │
│         ┌───────────▼────────────┐                         │
│         │    JWT Verification    │                         │
│         │  (Auth0 + JWKS Cache)  │                         │
│         └───────────┬────────────┘                         │
│                     │                                      │
│         ┌───────────▼────────────┐                         │
│         │   crud.py (Business    │                         │
│         │    Logic Layer)        │                         │
│         └───────────┬────────────┘                         │
│                     │                                      │
└─────────────────────┼──────────────────────────────────────┘
                      │
              SQLAlchemy ORM
                      │
┌─────────────────────▼────────────────────────────────────┐
│                    DATABASE LAYER                        │
│                                                          │
│  ┌──────────────────┐  ┌──────────────────┐              │
│  │  database.py     │  │   models.py      │              │
│  │ (Connection Pool)│  │  (ORM Models)    │              │
│  └──────────────────┘  └──────────────────┘              │
│         │                       │                        │
│         └───────────┬───────────┘                        │
│                     │                                    │
└─────────────────────┼────────────────────────────────────┘
                      │
                  PostgreSQL
                      │
        ┌─────────────▼───────────────┐
        │  items Table                │
        │  - id (primary key)         │
        │  - name (string)            │
        │  - description (string)     │
        └─────────────────────────────┘
```

## Technology Stack

### Core Framework
- **FastAPI** - Modern Python web framework for building APIs
  - Built on Starlette for the web parts
  - Pydantic for data validation
  - Automatic OpenAPI/Swagger documentation
  - Async support (though not used here)

### Database
- **PostgreSQL** - Production-grade relational database
  - Reliable, ACID-compliant transactions
  - Connection pooling configured in database layer
  - Supports complex queries and constraints

- **SQLAlchemy** - ORM (Object-Relational Mapping) library
  - Models database tables as Python classes
  - Handles SQL generation and execution
  - Manages transactions and sessions

### Authentication & Security
- **Auth0** - Third-party authentication service
  - Manages user identity and credentials
  - Issues JWT tokens
  - Provides JWKS (JSON Web Key Set) for token verification

- **PyJWT (python-jose)** - JWT token handling
  - Decodes JWT tokens
  - Verifies token signatures using public keys
  - Extracts token payload and claims

### Data Validation
- **Pydantic** - Data validation and serialization library
  - Validates request data at schema level
  - Converts data types
  - Provides clear error messages
  - Used for request/response models

### Utilities
- **python-dotenv** - Environment variable management
  - Loads .env files for configuration
  - Keeps secrets out of code

- **requests** - HTTP client library
  - Fetches JWKS from Auth0
  - Handles HTTP requests with timeout

- **psycopg2-binary** - PostgreSQL adapter for Python
  - Enables SQLAlchemy to connect to PostgreSQL

## Core Components

### 1. main.py - The Entry Point

**Purpose**: Defines API routes and request handling

**Key Sections**:

#### Initialization
```python
# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create FastAPI app with metadata
app = FastAPI(
    title="CRUD API",
    version="1.1",
    description="..."
)

# Create database tables if they don't exist
models.Base.metadata.create_all(bind=engine)
```

**What happens**:
1. Environment variables (.env file) are loaded
2. Logging is configured to display all INFO and above messages
3. FastAPI app is created with metadata (used for Swagger documentation)
4. Tables in PostgreSQL are created if they don't exist

#### Dependency Injection

```python
def get_db():
    db = SessionLocal()
    try:
        yield db  # Provide session to route handler
    finally:
        db.close()  # Always close session after request
```

**What happens**:
- FastAPI calls this function before each protected route
- Provides a database session to the route
- Automatically closes the session after the response is sent
- Pattern: "yield" means it runs code before and after the request

#### Authentication Layer

```python
def verify_jwt(request: Request):
    # 1. Extract token from Authorization header
    # 2. Fetch JWKS from Auth0 (cached)
    # 3. Validate token structure and fields
    # 4. Verify token signature
    # 5. Return token payload or raise 401 error
```

**Flow**:
1. Client sends request with: `Authorization: Bearer <token>`
2. Token is extracted from header
3. JWKS (public keys) fetched from Auth0 (cached for 1 hour)
4. Token header is validated (no malformed tokens)
5. Token signature is verified using Auth0's public key
6. Token payload (user info) is extracted and passed to route

#### Routes

Each route follows this pattern:

```python
@app.post("/items")
def create_item(
    item: schemas.ItemCreate,           # Request body validation
    db: Session = Depends(get_db),      # Database session injection
    payload=Depends(verify_jwt)         # JWT validation
):
    try:
        return crud.create_item(db, item)  # Call business logic
    except Exception as e:
        logger.error("Error creating item", exc_info=True)  # Log full error
        raise HTTPException(status_code=500, detail="Failed to create item")  # Sanitized error
```

**What happens**:
1. Route decorator defines HTTP method and path
2. Function parameters are automatically validated and injected
3. Schema validator validates request JSON
4. JWT is verified (401 if invalid)
5. Database session is provided
6. Business logic is called
7. Errors are logged internally, sanitized error returned to client

### 2. schemas.py - Data Validation

**Purpose**: Defines expected request/response data structures

**Key Models**:

#### ItemBase - Common Fields
```python
class ItemBase(BaseModel):
    name: str
    description: str  # Required, non-optional
    
    @field_validator('description', mode='before')
    @classmethod
    def coerce_null_description_on_write(cls, v):
        # Coerce None to empty string
        if v is None:
            return ""
        # Validate it's a string
        if not isinstance(v, str):
            raise ValueError("description must be a string")
        return v
```

**What happens**:
- Validates that name and description are provided
- Ensures description is always a string (never NULL)
- If None is sent, it's coerced to empty string ""
- Invalid types raise a ValueError

#### ItemCreate - POST Requests
```python
class ItemCreate(ItemBase):
    pass  # Inherits all validation from ItemBase
```

**What it means**:
- Creating an item requires name and description
- Validator ensures no NULL descriptions are stored
- Client can send `description: null` and it becomes `""`

#### ItemUpdate - PUT Requests
```python
class ItemUpdate(BaseModel):
    name: str | None = None      # Optional: null means skip
    description: str | None = None  # Optional: null means skip
    
    @field_validator('description', mode='before')
    @classmethod
    def coerce_null_description_on_write(cls, v):
        if v is None:
            return None  # Don't update this field
        # ...validate type...
        return v
```

**What it means**:
- Both fields are optional in updates
- Omitting a field means "don't update that field"
- This enables partial updates

**Example**:
```json
// Update only the name, keep description unchanged
{
  "name": "Updated Name"
}

// Update only the description to empty string
{
  "description": ""
}

// Update both
{
  "name": "New Name",
  "description": "New description"
}
```

#### Item - Response Model
```python
class Item(ItemBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
```

**What it means**:
- When returning items, include the id field
- `from_attributes=True` means Pydantic can read from SQLAlchemy model objects

### 3. models.py - Database Schema

**Purpose**: Defines database table structure

```python
class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True, server_default='')
```

**What it means**:
- Creates a table called "items" in PostgreSQL
- `id`: Auto-incrementing integer primary key (indexed for fast lookups)
- `name`: String field, indexed for fast searches
- `description`: String field, can be NULL, defaults to empty string
- SQLAlchemy automatically generates SQL like:
  ```sql
  CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    description VARCHAR(255) DEFAULT ''
  );
  ```

### 4. crud.py - Business Logic

**Purpose**: Implements actual CRUD operations

#### get_items - Retrieve All
```python
def get_items(db: Session) -> list[models.Item]:
    return db.query(models.Item).all()
```

**What happens**:
```sql
-- SQL equivalent
SELECT * FROM items;
```

#### create_item - Create New
```python
def create_item(db: Session, item: schemas.ItemCreate) -> models.Item:
    db_item = models.Item(name=item.name, description=item.description)
    db.add(db_item)
    try:
        db.commit()
        db.refresh(db_item)
    except Exception:
        db.rollback()  # Undo changes if error
        logger.exception("Database error occurred while creating item")
        raise Exception("Failed to create item")
    return db_item
```

**Flow**:
1. Create Python object from validated data
2. Add it to the session (not yet saved)
3. Try to commit (save to database)
4. Refresh object to get auto-generated id from database
5. If error occurs, rollback (undo) changes
6. Return saved object

**SQL equivalent**:
```sql
INSERT INTO items (name, description) VALUES ('name', 'description');
-- Rollback if error
```

#### update_item - Update Existing
```python
def update_item(db: Session, item_id: int, item: schemas.ItemUpdate) -> Optional[models.Item]:
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        return None  # Item not found
    
    try:
        if item.name is not None:
            db_item.name = item.name
        if item.description is not None:
            db_item.description = item.description
        
        db.commit()
        db.refresh(db_item)
    except Exception:
        db.rollback()
        logger.exception("Database error occurred while updating item with id=%s", item_id)
        raise Exception("Failed to update item")
    return db_item
```

**Flow**:
1. Find item by id
2. If not found, return None
3. Update only the fields that were provided
4. Commit changes to database
5. Return updated object

**SQL equivalent**:
```sql
SELECT * FROM items WHERE id = 42;
-- If found:
UPDATE items SET name = 'new', description = 'new desc' WHERE id = 42;
```

#### delete_item - Delete
```python
def delete_item(db: Session, item_id: int) -> Optional[models.Item]:
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        return None
    
    try:
        db.delete(db_item)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Database error occurred while deleting item with id=%s", item_id)
        raise Exception("Failed to delete item")
    return db_item
```

**Flow**:
1. Find item by id
2. If not found, return None
3. Delete the item
4. Commit deletion to database
5. Return deleted item (for confirmation)

**SQL equivalent**:
```sql
DELETE FROM items WHERE id = 42;
```

### 5. database.py - Connection Management

**Purpose**: Manages database connections and pooling

```python
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
# Example: postgresql://user:password@localhost:5432/crud_api_db

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,           # Keep 10 connections ready
    max_overflow=20,        # Allow 20 extra when needed
    pool_pre_ping=True,     # Test before using
    pool_recycle=3600,      # Refresh after 1 hour
    echo=False
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
```

**What happens**:

1. **Connection Pool**: Creates a pool of 10 PostgreSQL connections
   - When a request needs a database connection, it gets one from the pool
   - Instead of creating a new connection (slow), reuses existing ones (fast)
   - If all 10 are in use, creates up to 20 more temporary ones

2. **pool_pre_ping**: Before using a connection, tests if it's still alive
   - PostgreSQL might close idle connections
   - This ensures the connection works before using it

3. **pool_recycle**: Closes and recreates connections after 1 hour
   - Prevents stale connections from lingering
   - PostgreSQL default connection timeout is 10 minutes

4. **SessionLocal**: Factory function to create database sessions
   - Each request gets its own session (thread-safe)
   - Session is cleaned up after response

## Request/Response Flow

### Complete Request Life Cycle

#### Request: `POST /items`
```json
{
  "Authorization": "Bearer eyJhbGc..."
}

{
  "name": "My Item",
  "description": null
}
```

#### Step-by-Step Processing

1. **FastAPI Receives Request**
   - Route handler is: `create_item(item, db, payload)`
   - FastAPI must inject these parameters

2. **Dependency 1: Extract Token**
   - `Depends(verify_jwt)` runs first
   - Extracts token from Authorization header
   - Validates it with Auth0

3. **Dependency 2: Get Database Session**
   - `Depends(get_db)` runs
   - Gets connection from pool
   - Creates database session

4. **Parameter 1: Validate Request Body**
   - Pydantic validates JSON against `ItemCreate` schema
   - Checks name is string (required)
   - Checks description and coerces null to ""
   - Returns validated `ItemCreate` object

5. **Call Handler**
   ```python
   try:
       return crud.create_item(db, item)
   ```
   - Passes validated data and session to CRUD layer

6. **CRUD Operation**
   - Creates new Item object
   - Adds to session (not yet saved)
   - Commits to database
   - Returns saved object with id

7. **Response Serialization**
   - FastAPI uses `Item` schema to convert object to JSON
   - Includes id, name, description
   - Returns 200 status code (or 201 Created)

8. **Clean Up**
   - Session is closed
   - Connection returned to pool

#### Response
```json
{
  "id": 42,
  "name": "My Item",
  "description": ""
}
```

## Authentication Flow

### Auth0 JWT Flow

#### 1. Client Gets Token (Outside This API)
```
User → Login to Auth0 website → Get JWT Token
```

The token looks like:
```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Imtlel9pZCJ9.
eyJzdWIiOiJ1c2VyMTIzIiwibmFtZSI6IkpvaG4gRG9lIiwiYXVkIjoibXktYXBpIiwiaWF0IjoxNjk0NjAwMDAwfQ.
[signature]
```

Structure: `[header].[payload].[signature]`

#### 2. Client Sends Token to API
```
curl -H "Authorization: Bearer eyJhbGc..." /items
```

#### 3. Server Verifies Token

**Step A: Extract Token**
```python
auth = request.headers.get("Authorization")
# Value: "Bearer eyJhbGc..."

parts = auth.split()
# parts[0] = "Bearer"
# parts[1] = "eyJhbGc..."

token = parts[1]
```

**Step B: Get JWKS from Auth0 (Cached)**
```python
def get_jwks():
    # First request: Fetch from Auth0
    # GET https://YOUR_AUTH0_DOMAIN/.well-known/jwks.json
    # Response:
    {
      "keys": [
        {
          "kid": "key_id_1",
          "kty": "RSA",
          "use": "sig",
          "n": "[modulus]",
          "e": "[exponent]"
        }
      ]
    }
    # Cache for 1 hour to avoid repeated requests
```

**Step C: Extract Token Header (Without Verification)**
```python
unverified_header = jwt.get_unverified_header(token)
# Returns: {"alg": "RS256", "typ": "JWT", "kid": "key_id_1"}
```

**Step D: Find Matching Public Key**
```python
# Look through JWKS keys for matching kid
# kid = "key_id_1" from token header matches a key in JWKS
# Extract RSA components: n (modulus), e (exponent)
```

**Step E: Verify Signature and Decode**
```python
payload = jwt.decode(
    token,
    rsa_key,  # Public key from JWKS
    algorithms=["RS256"],
    audience="my-api",  # Must match token claim
    issuer="https://auth0.com/"  # Must match token claim
)
# Returns: {"sub": "user123", "name": "John", "aud": "my-api", ...}
```

**What This Validates**:
1. Token wasn't tampered with (signature is valid)
2. Token was issued by Auth0 (signature proves it)
3. Token is for this API (audience matches)
4. Token is from Auth0 (issuer matches)
5. Token fields are properly formatted

#### 4. Request Proceeds or Fails
```python
if verification succeeds:
    payload is passed to route handler
    Request proceeds
else:
    raise HTTPException(status_code=401)
    Client gets error
```

## Database Layer

### Connection Pool Architecture

```
┌────────────────────────────────────────────────────────┐
│                   Connection Pool                      │
│                                                        │
│  [Active] [Active] [Idle] [Idle] [Idle] ... (10 total) │
│     ↑       ↑      ↑      ↑     ↑                      │
│     │       │      │      │     │                      │
│  Request  Request Gets   When   After 1hr              │
│  needs db needs db  one   needed recycle               │
└────────────────────────────────────────────────────────┘
                       │
            ┌──────────▼──────────┐
            │  PostgreSQL Database│
            │                     │
            │  items table        │
            │  - id               │
            │  - name             │
            │  - description      │
            └─────────────────────┘
```

### Transaction Management

**Explicit Transaction Control**:
```python
db.add(item)          # Stage changes
db.commit()           # Apply changes (creates transaction)
                      # Automatically commits on success
db.refresh(item)      # Reload object from database
                      # Gets auto-generated id

# If error occurs:
db.rollback()         # Undo pending changes
                      # Returns database to state before transaction
```

**What This Means**:
- Changes aren't final until commit
- If anything fails before commit, changes are abandoned
- Prevents partial/corrupted data in database

**Example**:
```python
# Initial state: Item with id=1, name="old", description="old"

db_item.name = "new"
db_item.description = "new"
db.add(db_item)

# At this point, changes are staged in memory only
# PostgreSQL database still has old values

try:
    db.commit()  # Now changes are permanent in PostgreSQL
    db.refresh(db_item)  # Reload from database
except Exception:
    db.rollback()  # Undo changes
    # PostgreSQL still has old values
```

## Data Validation

### Validation Layers

#### Layer 1: Schema Validation (Request Time)
```python
# Client sends
{
  "name": 123,  # Wrong type
  "description": "text"
}

# Pydantic validates against ItemCreate
# Expects:
#   name: str (not int)
#   description: str

# Result: 400 Bad Request
# Error message:
# "name: value_error.number.not_int"
```

#### Layer 2: Custom Validators
```python
@field_validator('description', mode='before')
def coerce_null_description_on_write(cls, v):
    if v is None:
        return ""
    if not isinstance(v, str):
        raise ValueError("description must be a string")
    return v

# Client sends:
{
  "name": "item",
  "description": null
}

# Validator runs:
# v = null
# return "" (coerced to empty string)

# Database receives:
{
  "name": "item",
  "description": ""  # Never NULL
}
```

#### Layer 3: Database Constraints
```python
Column(String, nullable=True, server_default='')
# In PostgreSQL:
# description VARCHAR(255) DEFAULT ''

# If somehow NULL gets to database, server_default ensures ''
# Multiple layers of protection
```

### Type Safety Benefits

```python
# Before: Optional[str]
description: Optional[str] = None
# Question: Is this None or ""? When?

# After: str with validator
description: str  # Always a string
@field_validator('description')
def coerce_null_on_write(v):
    return "" if v is None else v
# Answer: Always a string. If None sent, becomes ""
```

## Error Handling

### Error Handling Strategy

#### 1. Validation Errors (400)
```python
# Schema validation fails
POST /items
{
  "name": "item"  # Missing description
}

Response:
{
  "detail": [
    {
      "loc": ["body", "description"],
      "msg": "Field required",
      "type": "missing"
    }
  ]
}

Status: 400 Bad Request
```

#### 2. Authentication Errors (401)
```python
# No token
GET /items
# No Authorization header

Response:
{
  "detail": "Authorization header missing"
}

Status: 401 Unauthorized

---

# Invalid token
GET /items
Authorization: Bearer invalid_token

Response:
{
  "detail": "Malformed token: unable to read header"
}

Status: 401 Unauthorized
```

#### 3. Not Found Errors (404)
```python
# Item doesn't exist
PUT /items/999
{
  "name": "new"
}

Response:
{
  "detail": "Item not found"
}

Status: 404 Not Found
```

#### 4. Server Errors (500)
```python
# Database connection fails
POST /items
{
  "name": "item",
  "description": "desc"
}

# What client sees:
{
  "detail": "Failed to create item"
}

Status: 500 Internal Server Error

# What server logs internally:
2025-11-16 10:30:45 - crud - ERROR - Database error occurred while creating item
Traceback (most recent call last):
  File "crud.py", line 20, in create_item
    db.commit()
  File "sqlalchemy/orm/session.py", line 1234, in commit
    ...
psycopg2.OperationalError: could not connect to server

# Full error details are logged but never sent to client
# Client gets generic error message
```

**Key Principle**: 
- Sensitive information (database details, stack traces) logged internally
- Sanitized error messages sent to clients
- Prevents information leakage about system internals

## Deployment

### Development Setup

```bash
# 1. Environment
export DATABASE_URL="postgresql://user:pass@localhost:5432/db"
export AUTH0_DOMAIN="your-domain.auth0.com"
export AUTH0_API_AUDIENCE="your-api-id"

# 2. Start API
uvicorn main:app --reload

# 3. Visit Swagger
http://localhost:8000/docs
```

### Production Setup

```bash
# 1. PostgreSQL must be running on separate server
#    Not embedded like SQLite

# 2. Use environment variables (not .env file)
DATABASE_URL="postgresql://prod_user:secure_pass@prod.db.com:5432/prod_db"
AUTH0_DOMAIN="production.auth0.com"
AUTH0_API_AUDIENCE="production-api"

# 3. Use production ASGI server with multiple workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app

# 4. Use reverse proxy (nginx) with HTTPS
# API runs on port 8000 internally
# Nginx listens on port 443 (HTTPS)
# Forwards requests to API

# 5. Enable monitoring
# - Application logs go to central logging service
# - Database performance monitored
# - Auth0 token failures tracked

# 6. Set up backups
# - Database backups run daily
# - Can restore if data corruption

# 7. Configure connection pooling
# - pool_size = 10 for small deployments
# - Increase for high traffic
```

### Scaling Architecture

```
┌─────────────────────────────────────────┐
│          HTTPS (Port 443)               │
│          nginx Reverse Proxy            │
│          Load Balancer                  │
└────────────────┬────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
   ┌────▼────┐       ┌────▼────┐
   │Instance 1       │Instance 2
   │ Port 8000       │ Port 8000
   │ CRUD API        │ CRUD API
   └────┬────┘       └────┬────┘
        │                 │
        │   ┌─────────────┘
        │   │
        └───┼───────────────────────┐
            │                       │
      PostgreSQL Master        PostgreSQL Replica
      (Read/Write)            (Read-only)

1. Nginx distributes requests across multiple API instances
2. Each API instance connects to PostgreSQL
3. PostgreSQL replicates to read-only replicas
4. Multiple availability zones provide redundancy
```

## Troubleshooting

### Common Issues and Solutions

#### 1. "connection refused"
```
Error: could not connect to server: Connection refused

Solution:
- Check PostgreSQL is running
- Check DATABASE_URL is correct
- Check firewall allows connection
- Check PostgreSQL port (default 5432)

Test:
psql postgresql://user:pass@host:5432/db
```

#### 2. "401 Unauthorized"
```
Error: Authorization header missing

Causes:
- Request doesn't include Authorization header
- Token is invalid or expired
- Auth0_DOMAIN or AUTH0_API_AUDIENCE is wrong

Solution:
- Get fresh token from Auth0
- Verify AUTH0_DOMAIN and AUTH0_API_AUDIENCE
- Check token is in Authorization header

Test:
curl -H "Authorization: Bearer $(YOUR_TOKEN)" http://localhost:8000/items
```

#### 3. "Field validation error"
```
Error: 400 Bad Request with validation error

Cause:
- Request JSON doesn't match schema
- Missing required field
- Wrong data type

Solution:
- Check POST/PUT body matches expected schema
- name: string (required)
- description: string (can be null, will become "")

Test:
curl -X POST http://localhost:8000/items \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "test", "description": "test"}'
```

#### 4. "pool overflow"
```
Error: Too many connections

Cause:
- Sessions not being closed properly
- All pool connections are in use
- Slow queries holding connections

Solution:
- Increase pool_size in database.py
- Check for connection leaks in code
- Look for slow queries

Current settings:
pool_size = 10
max_overflow = 20
Total possible = 30 connections
```

#### 5. "token verification failed"
```
Error: Token verification failed: ...

Causes:
- JWKS can't be fetched from Auth0
- Token signature invalid
- Token is for wrong API (audience mismatch)

Solution:
- Check Auth0 credentials
- Check token is for this API (audience claim)
- Check Auth0 domain is reachable

Test:
curl https://YOUR_AUTH0_DOMAIN/.well-known/jwks.json
```

## Key Concepts to Remember

### 1. Dependency Injection
FastAPI automatically provides dependencies to route handlers:
```python
def create_item(
    item: schemas.ItemCreate,    # From request body (validated)
    db: Session = Depends(get_db),  # From get_db() function
    payload = Depends(verify_jwt)   # From verify_jwt() function
):
```

### 2. Validation Happens Twice
- Schema validation: Catches invalid input at request time
- Database constraints: Catches issues at database time
- Defense in depth: Multiple layers of protection

### 3. Transactions Ensure Consistency
- All changes applied together (commit) or none (rollback)
- Prevents partial updates corrupting data
- Safe even if server crashes during request

### 4. Connection Pooling Performance
- Reusing connections is much faster than creating new ones
- Pool maintains 10 ready connections
- Pre-ping ensures connections work before using

### 5. Error Handling Philosophy
- Log everything internally for debugging
- Return only safe information to clients
- Prevents information leakage about system details

### 6. Type Safety Throughout
- Type hints enable IDE autocomplete
- Type checkers (mypy) catch errors at development time
- Pydantic validates at runtime
- Combined: Very few bugs reach production

## File Dependencies Map

```
main.py (Routes)
  ├── imports models (Database schemas)
  ├── imports schemas (Validation)
  ├── imports crud (Business logic)
  ├── imports database (Session/Engine)
  └── uses Auth0 (JWT validation)

schemas.py (Validation)
  └── uses Pydantic

models.py (Database schemas)
  ├── uses SQLAlchemy
  └── uses database.py Base

crud.py (Business logic)
  ├── uses models (Database objects)
  ├── uses schemas (Type hints)
  ├── uses database (Session)
  └── uses logging

database.py (Connections)
  └── uses SQLAlchemy
  └── uses PostgreSQL
```

## Summary

This CRUD API represents a complete, production-grade backend application with:

1. **Security**: Auth0 authentication with JWT token verification
2. **Reliability**: Transaction management with automatic rollback
3. **Maintainability**: Clean separation of concerns (routes, validation, logic, data)
4. **Type Safety**: Full type hints with runtime validation
5. **Observability**: Comprehensive logging for debugging
6. **Scalability**: Connection pooling and database separation
7. **Performance**: Caching (JWKS), connection reuse, efficient queries
8. **Error Handling**: Proper HTTP status codes with sanitized messages

Understanding each component and how they work together is key to owning and maintaining this project.
