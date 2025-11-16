# CRUD API - Visual Architecture & Data Flow Diagrams

## Overall System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SERVICES                              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌────────────────────┐                    ┌─────────────────────┐     │
│  │   Auth0 Service    │                    │  PostgreSQL Server  │     │
│  │                    │                    │                     │     │
│  │ • Manages users    │                    │ • Stores items      │     │
│  │ • Issues JWT tokens│                    │ • ACID transactions │     │
│  │ • Provides JWKS    │                    │ • Connection pool   │     │
│  └────────────────────┘                    └─────────────────────┘     │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
         ▲                                              ▲
         │ 1. Fetch JWKS                                │ 4. SQL Queries
         │    (HTTP)                                    │
         │                                              │
┌────────┴──────────────────────────────────────────────┴────────────────┐
│                     YOUR APPLICATION                                   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        main.py                                  │   │
│  │                   (HTTP Endpoint Layer)                         │   │
│  │                                                                 │   │  
│  │  POST /items          GET /items          PUT /items/{id}       │   │
│  │  DELETE /items/{id}   GET /health         GET /                 │   │
│  │                                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│         ▲                       ▲                      ▲               │
│         │                       │                      │               │
│         │                       │                      │               │
│         │ 2. Verify JWT         │ Extract Headers      │ Return JSON   │
│         │    Extract Body       │ Database Session     │               │
│         │                       │                      │               │
│  ┌──────┴───────────────────────┴──────────────────────┴───────────┐   │
│  │                  DEPENDENCY INJECTION LAYER                     │   │
│  │                                                                 │   │
│  │  verify_jwt()              get_db()                             │   │
│  │  └─ Check Auth header      └─ Get pooled connection             │   │
│  │  └─ Verify token signature └─ Create session                    │   │
│  │  └─ Return user info       └─ Cleanup after request             │   │
│  │                                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│         ▲                                            ▲                 │
│         │                                            │                 │
│  ┌──────┴─────────────────────────────────────┬──────┴──────────── ┐   │
│  │          schemas.py                        │   database.py      │   │
│  │      (Data Validation Layer)               │  (Connection Layer)│   │
│  │                                            │                    │   │
│  │  ItemCreate                                │  Connection Pool   │   │
│  │  ├─ Validate name (required, string)       │  ├─ pool_size=10   │   │
│  │  ├─ Validate description (string)          │  ├─ max_overflow   │   │
│  │  ├─ Coerce null → ""                       │  └─ pool_pre_ping  │   │
│  │  └─ Return validated object                │                    │   │
│  │                                            │  SessionLocal      │   │
│  │  ItemUpdate                                │  └─ Create thread- │   │
│  │  ├─ name: optional (null = skip)           │     safe sessions  │   │
│  │  ├─ description: optional (null = skip)    │                    │   │
│  │  └─ Return partial update object           │                    │   │
│  │                                            │                    │   │
│  │  Item (Response Schema)                    │                    │   │
│  │  ├─ id (from database)                     │                    │   │
│  │  ├─ name (from database)                   │                    │   │
│  │  └─ description (from database)            │                    │   │
│  │                                            │                    │   │
│  └────────────────────────────────────────────┴─────────────────── ┘   │
│         ▲                                             ▲                │
│         │                                             │                │
│  ┌──────┴──────────────────────────────────────┬──────┴────────────┐   │
│  │           crud.py                           │   models.py       │   │
│  │    (Business Logic Layer)                   │  (Database Schema)│   │
│  │                                             │                   │   │ 
│  │  get_items()                                │  class Item(Base):│   │
│  │  └─ SELECT * FROM items                     │    __tablename__ =│   │
│  │                                             │      "items"      │   │
│  │  create_item()                              │                   │   │
│  │  ├─ Create Item object                      │    id = Column()  │   │
│  │  ├─ db.add()                                │    name = Column()│   │
│  │  ├─ db.commit()                             │    description =  │   │
│  │  └─ Return saved object                     │      Column()     │   │
│  │                                             │                   │   │
│  │  update_item()                              │                   │   │
│  │  ├─ Query by id                             │                   │   │
│  │  ├─ Update fields                           │                   │   │
│  │  ├─ db.commit()                             │                   │   │
│  │  └─ Return updated object                   │                   │   │
│  │                                             │                   │   │
│  │  delete_item()                              │                   │   │
│  │  ├─ Query by id                             │                   │   │
│  │  ├─ db.delete()                             │                   │   │
│  │  ├─ db.commit()                             │                   │   │
│  │  └─ Return deleted object                   │                   │   │
│  │                                             │                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
         ▲
         │ 3. HTTP Requests
         │
┌────────┴──────────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATION                                 │
│                                                                       │
│  Browser / Mobile App / Other Service                                 │
│                                                                       │
│  Sends JWT Token → API → Receives JSON Response                       │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

## Request Processing Pipeline

### POST /items Request

```
┌─────────────────────────────────────────────────────────────────┐
│  CLIENT: HTTP Request                                           │
│  ────────────────────────────────────────────────────────────   │
│  POST /items                                                    │
│  Authorization: Bearer eyJhbGc...                               │
│  Content-Type: application/json                                 │
│                                                                 │
│  {                                                              │
│    "name": "My Item",                                           │
│    "description": null                                          │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  FASTAPI: Route Handler Selection                               │
│  ────────────────────────────────────────────────────────────   │
│  Match: POST /items → create_item() handler                     │
│  Parse URL parameters: None                                     │
│  Parse headers: Content-Type, Authorization                     │
│  Parse body: JSON                                               │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  DEPENDENCY 1: verify_jwt(request)                              │
│  ────────────────────────────────────────────────────────────   │
│  1. Extract token from Authorization header                     │
│     "Bearer eyJhbGc..." → "eyJhbGc..."                          │
│                                                                 │
│  2. Fetch JWKS from Auth0 (or use cached version)               │
│     GET https://domain/.well-known/jwks.json                    │
│     ↓ Cache hit (within 1 hour)                                 │
│                                                                 │
│  3. Get unverified header from token                            │
│     Decode header without verifying: {"kid": "key_id_1", ...}   │
│                                                                 │
│  4. Find matching key in JWKS by kid                            │
│     Look for kid="key_id_1" in JWKS["keys"]                     │
│                                                                 │
│  5. Verify token signature                                      │
│     jwt.decode(token, public_key, ...)                          │
│     ↓ Signature valid                                           │
│                                                                 │
│  6. Validate token claims                                       │
│     audience matches, issuer matches, not expired               │
│     ↓ All claims valid                                          │
│                                                                 │
│  7. Return payload                                              │
│     {"sub": "user123", "name": "John", ...}                     │
│     ↓ Passed to handler                                         │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  DEPENDENCY 2: get_db()                                         │
│  ────────────────────────────────────────────────────────────   │
│  1. Get connection from pool (or create new)                    │
│     Pool has 10 ready connections                               │
│     ↓ Got one                                                   │
│                                                                 │
│  2. Create new Session                                          │
│     SessionLocal() wraps the connection                         │
│     ↓ Session created                                           │
│                                                                 │
│  3. Provide session to handler                                  │
│     yield db  (pauses function)                                 │
│     ↓ Handler runs                                              │
│                                                                 │
│  4. Close session after handler finishes                        │
│     db.close() (resumes function)                               │
│     ↓ Connection returned to pool                               │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  SCHEMA VALIDATION: ItemCreate                                  │
│  ────────────────────────────────────────────────────────────   │
│  Pydantic validates JSON against ItemCreate schema:             │
│                                                                 │
│  Input:                                                         │
│  {                                                              │
│    "name": "My Item",                                           │
│    "description": null                                          │
│  }                                                              │
│                                                                 │
│  Validation rules:                                              │
│  ├─ name: str → "My Item" ✓ Valid                                  
│  └─ description: str with validator                             │
│     ├─ Input: null                                              │
│     ├─ Validator: if v is None return ""                        │
│     └─ Output: ""                                               │
│                                                                 │
│  Result:                                                        │
│  ItemCreate(name="My Item", description="")                     │
│  ↓ Passed to handler                                            │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  HANDLER: create_item()                                         │
│  ────────────────────────────────────────────────────────────   │
│  Parameters injected:                                           │
│  ├─ item: ItemCreate (from validation above)                    │
│  ├─ db: Session (from get_db above)                             │
│  └─ payload: dict (from verify_jwt above)                       │
│                                                                 │
│  Call CRUD function:                                            │
│  return crud.create_item(db, item)                              │
│  ↓ Calls business logic                                         │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  BUSINESS LOGIC: crud.create_item()                             │
│  ────────────────────────────────────────────────────────────   │
│  1. Create Python object from validated data                    │
│     db_item = models.Item(                                      │
│       name="My Item",                                           │
│       description=""                                            │
│     )                                                           │
│                                                                 │
│  2. Add to session (not yet saved)                              │
│     db.add(db_item)                                             │
│     (Python object, no database change yet)                     │
│                                                                 │
│  3. Commit to database                                          │
│     db.commit()                                                 │
│     (Sends INSERT to PostgreSQL)                                │
│     (PostgreSQL generates id=42)                                │
│                                                                 │
│  4. Refresh object from database                                │
│     db.refresh(db_item)                                         │
│     (Object now has id=42 from database)                        │
│                                                                 │
│  5. Return saved object                                         │
│     Item(id=42, name="My Item", description="")                 │
│     ↓ Passed back to handler                                    │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  RESPONSE SERIALIZATION                                         │
│  ────────────────────────────────────────────────────────────   │
│  FastAPI uses Item schema to convert object to JSON:            │
│                                                                 │
│  Python object:                                                 │
│  Item(id=42, name="My Item", description="")                    │
│  ↓ Serialized using Item Pydantic model                         │
│  JSON response:                                                 │
│  {                                                              │
│    "id": 42,                                                    │
│    "name": "My Item",                                           │
│    "description": ""                                            │
│  }                                                              │
│  ↓ Sent to client                                               │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  HTTP RESPONSE                                                  │
│  ────────────────────────────────────────────────────────────   │
│  Status: 201 Created                                            │
│  Content-Type: application/json                                 │
│                                                                 │
│  {                                                              │
│    "id": 42,                                                    │
│    "name": "My Item",                                           │
│    "description": ""                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Authentication & Token Verification Flow

```
┌──────────────────────────────────────────────────────────────────┐
│  USER AUTHENTICATION (Outside this API)                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. User visits Auth0 login page                                 │
│     https://your-domain.auth0.com/login                          │
│                                                                  │
│  2. User enters credentials                                      │
│     Email: user@example.com                                      │
│     Password: ***                                                │
│                                                                  │
│  3. Auth0 validates and issues JWT token                         │
│     Token = Header.Payload.Signature                             │
│                                                                  │
│  Header (algorithm and key ID):                                  │
│  {                                                               │
│    "alg": "RS256",                                               │
│    "typ": "JWT",                                                 │
│    "kid": "key_id_1"                                             │
│  }                                                               │
│                                                                  │
│  Payload (user claims):                                          │
│  {                                                               │
│    "sub": "auth0|user123",                                       │
│    "name": "John Doe",                                           │
│    "email": "user@example.com",                                  │
│    "aud": "my-api-id",                                           │
│    "iss": "https://your-domain.auth0.com/",                      │
│    "iat": 1694600000,                                            │
│    "exp": 1694603600                                             │ 
│  }                                                               │
│                                                                  │
│  Signature (proves Auth0 issued this):                           │
│  HMACSHA256(                                                     │
│    base64url(header) + "." + base64url(payload),                 │  
│    private_key_at_auth0                                          │
│  )                                                               │
│                                                                  │
│  Full JWT: eyJhbGc....[header]....eyJzdWIi....[payload]....      │
│            [signature]                                           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  TOKEN TRANSMISSION                                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Client stores token and sends with requests:                    │
│                                                                  │
│  GET /items                                                      │
│  Authorization: Bearer eyJhbGc...[full token]...                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│  TOKEN VERIFICATION (In API)                                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Extract token from Authorization header                      │
│     Header: "Bearer eyJhbGc..."                                  │
│     Token: "eyJhbGc..."                                          │
│                                                                  │
│  2. Fetch JWKS from Auth0 (if not cached)                        │
│     URL: https://your-domain.auth0.com/.well-known/jwks.json     │
│     GET request                                                  │
│     Response:                                                    │
│     {                                                            │
│       "keys": [                                                  │
│         {                                                        │
│           "kid": "key_id_1",                                     │
│           "kty": "RSA",                                          │
│           "use": "sig",                                          │
│           "n": "[long modulus string]",                          │
│           "e": "AQAB"                                            │
│         },                                                       │
│         ... more keys ...                                        │
│       ]                                                          │
│     }                                                            │
│     Cache for 1 hour                                             │
│                                                                  │
│  3. Decode token header WITHOUT verification                     │
│     jwt.get_unverified_header(token)                             │
│     Returns: {"alg": "RS256", "typ": "JWT", "kid": "key_id_1"}   │
│     kid = "key_id_1" tells us which key to use                   │
│                                                                  │
│  4. Find matching key in JWKS by kid                             │
│     Loop through JWKS["keys"]                                    │
│     Find key where kid == "key_id_1"                             │
│     Found: RSA key with n and e parameters                       │
│                                                                  │
│  5. Verify token signature                                       │
│     Algorithm: RS256 (RSA with SHA-256)                          │
│     Steps:                                                       │
│     a. Extract signature from token (third part)                 │
│     b. Decode header and payload (first two parts)               │
│     c. Compute hash of header.payload with SHA-256               │
│     d. Decrypt signature using public key (n, e)                 │
│     e. Compare: computed hash == decrypted signature?            │
│     Result: Signature is valid → Token came from Auth0           │
│                                                                  │
│  6. Verify token claims                                          │
│     a. audience == "my-api-id" ✓                                 
│     b. issuer == "https://your-domain.auth0.com/" ✓              
│     c. exp (expiration) > current_time ✓                         
│     d. All claims valid → Token is trustworthy                   │
│                                                                  │
│  7. Decode payload                                               │ 
│     jwt.decode(token, public_key, audience="my-api-id", ...)     │
│     Returns:                                                     │
│     {                                                            │
│       "sub": "auth0|user123",                                    │
│       "name": "John Doe",                                        │
│       "email": "user@example.com",                               │
│       ... other claims ...                                       │
│     }                                                            │
│     Payload passed to route handler                              │
│                                                                  │
│  8. Request proceeds                                             │
│     Token is valid, user is authenticated                        │
│     Handler receives payload with user info                      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

If any step fails:
  - Malformed token → 401 "Malformed token: unable to read header"
  - Invalid signature → 401 "Token verification failed"
  - Expired token → 401 "Token verification failed"
  - Wrong audience → 401 "Token verification failed"
  - JWKS unavailable → 503 "Unable to fetch JWKS"
```

## Database Transaction Flow

```
┌────────────────────────────────────────────────────────────┐
│  TRANSACTION: Create Item                                  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Initial State:                                            │
│  PostgreSQL items table:                                   │
│  id | name  | description                                  │
│  ---|-------|-------------                                 │
│  1  | Item1 | Description1                                 │
│  2  | Item2 | Description2                                 │
│                                                            │
└────────────────────────────────────────────────────────────┘
                              ▼
┌────────────────────────────────────────────────────────────┐
│  Step 1: db.add(item)                                      │
│  ──────────────────────────────────────────────────────    │
│  Python object added to session                            │
│  Not yet sent to database                                  │
│                                                            │
│  Session memory:                                           │
│  - db_item (not in database yet)                           │
│  - name: "New Item"                                        │
│  - description: "New Description"                          │
│                                                            │
│  Database (unchanged):                                     │
│  id | name  | description                                  │
│  ---|-------|-------------                                 │
│  1  | Item1 | Description1                                 │
│  2  | Item2 | Description2                                 │
│                                                            │
└────────────────────────────────────────────────────────────┘
                              ▼
┌────────────────────────────────────────────────────────────┐
│  Step 2: db.commit()                                       │
│  ──────────────────────────────────────────────────────    │
│  Session sends changes to PostgreSQL                       │
│  PostgreSQL executes:                                      │
│  INSERT INTO items (name, description)                     │
│  VALUES ('New Item', 'New Description')                    │
│                                                            │
│  PostgreSQL generates id=3 (auto-increment)                │
│  Writes to disk (durable)                                  │
│                                                            │
│  Database (after commit):                                  │
│  id | name     | description                               │
│  ---|----------|-------------------                        │
│  1  | Item1    | Description1                              │
│  2  | Item2    | Description2                              │
│  3  | New Item | New Description                           │
│                                                            │
└────────────────────────────────────────────────────────────┘
                              ▼
┌────────────────────────────────────────────────────────────┐
│  Step 3: db.refresh(item)                                  │
│  ──────────────────────────────────────────────────────    │
│  Reload object from database                               │
│  Gets the auto-generated id                                │
│                                                            │
│  Python object now has:                                    │
│  - id: 3 (from database)                                   │
│  - name: "New Item"                                        │
│  - description: "New Description"                          │
│                                                            │
│  Return to client                                          │
│  ↓                                                         │
│  {                                                         │
│    "id": 3,                                                │
│    "name": "New Item",                                     │
│    "description": "New Description"                        │
│  }                                                         │
│                                                            │
└────────────────────────────────────────────────────────────┘

WHAT IF ERROR OCCURS BEFORE COMMIT?

┌────────────────────────────────────────────────────────────┐
│  Step 1: db.add(item)                                      │
│  Step 2 (ERROR): db.commit() fails                         │
│  ──────────────────────────────────────────────────────    │
│                                                            │
│  Exception caught:                                         │
│  except Exception:                                         │
│      db.rollback()  ← Undo everything                      │
│                                                            │
│  PostgreSQL rolls back transaction:                        │
│  - No INSERT executed                                      │
│  - No rows added                                           │
│  - Database unchanged                                      │
│                                                            │
│  Database (after rollback):                                │
│  id | name  | description                                  │
│  ---|-------|-------------                                 │
│  1  | Item1 | Description1                                 │
│  2  | Item2 | Description2                                 │
│                                                            │
│  No id=3 created (never added)                             │
│  Data is consistent                                        │
│                                                            │
│  Error logged:                                             │
│  "Database error occurred while creating item"             │
│                                                            │
│  Client gets:                                              │
│  {                                                         │
│    "detail": "Failed to create item"                       │
│  }                                                         │
│  Status: 500 Internal Server Error                         │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## Connection Pool Architecture

```
┌──────────────────────────────────────────────────────────────┐
│              CONNECTION POOL (10 Connections)                │
│  ┌───────────────────────────────────────────────────────┐   │
│  │ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐               │   │
│  │ │READY│ │READY│ │READY│ │READY│ │READY│ ...           │   │
│  │ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘               │   │
│  └───────────────────────────────────────────────────────┘   │
│                          ▲                                   │
└──────────────────────────┼───────────────────────────────────┘
                           │
            ┌──────────────┼─────────────┐
            │              │             │
       ┌────▼────┐    ┌────▼────┐   ┌────▼────┐
       │Request 1│    │Request 2│   │Request 3│
       │         │    │         │   │         │
       │Gets     │    │Gets     │   │Gets     │
       │READY #1 │    │READY #2 │   │READY #3 │
       └────┬────┘    └────┬────┘   └────┬────┘
            │              │             │
            │ Query 1      │ Query 2     │ Query 3
            ▼              ▼             ▼
       ┌────────────────────────────────────────────┐
       │         PostgreSQL Database                │
       │                                            │
       │  SELECT * FROM items;  (Request 1)         │
       │  INSERT INTO ... (Request 2)               │
       │  UPDATE ... (Request 3)                    │
       │                                            │
       └────────────────────────────────────────────┘
            ▲              ▲              ▲
            │              │              │
       ┌────┴────┐    ┌────┴────┐   ┌────┴────┐
       │READY #1 │    │READY #2 │   │READY #3 │
       │(Reused) │    │(Reused) │   │(Reused) │
       └────┬────┘    └────┬────┘   └────┬────┘
            │              │              │
            └──────────────┼──────────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
       ┌────▼────┐    ┌────▼────┐   ┌────▼────┐
       │Response1│    │Response2│   │Response3│
       └─────────┘    └─────────┘   └─────────┘

Connection Pool Benefits:
  - Fast: Connections reused, no creation overhead
  - Reliable: Pool pre-pings connections before use
  - Scalable: Handles 10 concurrent requests easily
  - Smart: Recycles connections after 1 hour to prevent stale

Configuration:
  pool_size = 10            → Keep 10 connections ready
  max_overflow = 20         → Allow up to 20 more if needed
  pool_pre_ping = True      → Test before using
  pool_recycle = 3600       → Recreate after 1 hour
```

These diagrams show the complete architecture and data flows. Study these along with the code to fully understand the system.
