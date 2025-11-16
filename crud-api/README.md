# CRUD API

A production-ready CRUD API built with FastAPI, featuring Auth0 integration, comprehensive error handling, and schema validation with detailed migration support.

## Overview

This is a fully-featured REST API for managing items with the following capabilities:

- Create, read, update, and delete items
- Auth0 JWT authentication with JWKS validation
- Type-safe Pydantic schemas with write-time validation
- Comprehensive error handling with sanitized responses
- Structured logging for debugging and monitoring
- Database session management with transaction rollback
- Support for partial updates via JSON Patch semantics
- Migration tooling for schema evolution

## Features

### API Endpoints

- `GET /health` - Health check endpoint (public)
- `GET /` - Root endpoint (public)
- `POST /items` - Create a new item (protected)
- `GET /items` - Retrieve all items (protected)
- `PUT /items/{item_id}` - Update an item (protected)
- `DELETE /items/{item_id}` - Delete an item (protected)

### Security

- JWT authentication with Auth0 integration
- Token header validation (Authorization: Bearer <token>)
- JWKS (JSON Web Key Set) validation with caching
- Malformed token detection with try/except handling
- HTTP 401 responses for authentication failures
- Sanitized error messages (no sensitive data leakage)
- Full error logging for debugging

### Data Validation

- Required and optional field validation at schema level
- Type checking for all inputs
- Custom validators for data transformation
- Partial update support (omit fields to skip them)
- Write-time validation (validates at request time)
- Database-level constraints for data integrity

### Error Handling

- Proper exception handling in CRUD operations
- Database transaction rollback on errors
- Clear error messages to clients
- Detailed logging for debugging
- Specific HTTP status codes (400, 401, 404, 500)

## Project Structure

```
crud-api/
├── main.py                          # API entry point and route definitions
├── models.py                        # SQLAlchemy ORM models
├── schemas.py                       # Pydantic validation schemas
├── crud.py                          # CRUD operation functions
├── database.py                      # Database configuration
├── migration_backfill_description.py # Database migration script
├── README.md                        # This file
├── MIGRATION_GUIDE.md              # Detailed migration instructions
├── SCHEMA_VALIDATION_IMPROVEMENTS.md # Schema validation details
├── SCHEMA_VALIDATION_COMPLETE.md    # Complete validation guide
├── WRITE_TIME_VALIDATION_SUMMARY.md # Validation strategy summary
├── LEGACY_NULL_HANDLING.md         # Legacy data handling
├── SECURITY_ERROR_HANDLING.md      # Security and error handling details
├── TYPE_SAFETY_IMPROVEMENTS.md     # Type system improvements
└── crud_test.py                    # Test script for API functionality
```

## Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager
- PostgreSQL 12 or higher
- Auth0 account with API credentials

### Setup Instructions

1. Clone the repository and navigate to the project directory:

```bash
cd crud-api
```

2. Create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install fastapi uvicorn sqlalchemy pydantic python-jose requests python-dotenv psycopg2-binary
```

4. Create a `.env` file in the project directory with PostgreSQL and Auth0 credentials:

```
DATABASE_URL=postgresql://username:password@localhost:5432/crud_api_db
AUTH0_DOMAIN=your-auth0-domain.auth0.com
AUTH0_API_AUDIENCE=your-api-identifier
```

Replace the following:
- `username` - Your PostgreSQL user
- `password` - Your PostgreSQL password
- `localhost` - Your PostgreSQL host (or IP address)
- `5432` - Your PostgreSQL port (default is 5432)
- `crud_api_db` - Your PostgreSQL database name

5. Create the PostgreSQL database:

```bash
createdb -U username crud_api_db
```

6. Start the application:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## Usage

### Interactive API Documentation

FastAPI provides automatic interactive API documentation via Swagger UI:

```
http://localhost:8000/docs
```

Alternatively, ReDoc documentation is available at:

```
http://localhost:8000/redoc
```

### Example Requests

#### Health Check (No Authentication)

```bash
curl http://localhost:8000/health
```

#### Create an Item

```bash
curl -X POST http://localhost:8000/items \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Item",
    "description": "Item description"
  }'
```

#### Get All Items

```bash
curl -X GET http://localhost:8000/items \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Update an Item

```bash
curl -X PUT http://localhost:8000/items/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Item"
  }'
```

#### Delete an Item

```bash
curl -X DELETE http://localhost:8000/items/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Data Models

### Item

An item has the following fields:

- `id` (integer) - Unique identifier (auto-generated)
- `name` (string) - Item name (required)
- `description` (string) - Item description (coerced to empty string if None)

### Schema Validation

The API uses Pydantic models for validation:

- `ItemCreate` - Used for POST requests
- `ItemUpdate` - Used for PUT requests (all fields optional)
- `Item` - Used for responses

## Authentication

The API uses Auth0 for JWT authentication. All protected endpoints require a valid JWT token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6In...
```

Authentication failures return HTTP 401 with a descriptive error message.

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK` - Successful request
- `201 Created` - Item successfully created
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid authentication
- `404 Not Found` - Item not found
- `500 Internal Server Error` - Server error (with sanitized error message)

Error responses include a detail field:

```json
{
  "detail": "Item not found"
}
```

Sensitive information (database errors, stack traces) is logged internally but never returned to clients.

## Database Migrations

The project includes a migration system for handling schema changes:

### Phase 1: Backfill NULL Values

Run before deploying code changes:

```bash
python migration_backfill_description.py
```

This converts all existing NULL descriptions to empty strings.

### Phase 2: Add Database Constraint

Run after code is stable:

```bash
python migration_backfill_description.py --phase2
```

This adds a NOT NULL constraint to the description column for defense-in-depth.

See MIGRATION_GUIDE.md for detailed migration instructions.

## Type Safety

The project uses Python type hints throughout:

- Full type hints on all functions
- Pydantic models for runtime validation
- ConfigDict for model configuration
- Optional types for nullable fields
- Return type hints for all functions

This enables IDE autocomplete, type checking with mypy, and better error messages.

## Logging

The application uses Python's logging module for structured logging:

- Application logs are sent to stdout
- Errors include full stack traces for debugging
- Sanitized error messages go to clients
- Contextual information (item IDs) included in logs
- Log format includes timestamp, logger name, level, and message

Configure logging in main.py:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Testing

A test script is provided for basic API functionality:

```bash
python crud_test.py
```

This script demonstrates:

- Creating items
- Retrieving items
- Updating items
- Deleting items

Before running tests, ensure you have a valid Auth0 token available.

## Documentation Files

The project includes comprehensive documentation:

- `MIGRATION_GUIDE.md` - Step-by-step migration instructions
- `SCHEMA_VALIDATION_IMPROVEMENTS.md` - Schema validation details and examples
- `SCHEMA_VALIDATION_COMPLETE.md` - Complete implementation guide
- `WRITE_TIME_VALIDATION_SUMMARY.md` - Before/after validation comparison
- `LEGACY_NULL_HANDLING.md` - Legacy data migration strategy
- `SECURITY_ERROR_HANDLING.md` - Security and error handling details
- `TYPE_SAFETY_IMPROVEMENTS.md` - Type system improvements and benefits

## Development Notes

### Database

The application uses SQLAlchemy ORM with PostgreSQL. Connection pooling is configured in database.py:

- Pool size: 10 connections kept in the pool
- Max overflow: 20 additional connections when needed
- Pool pre-ping: Tests connections before using them to detect stale connections
- Pool recycle: Recycles connections after 1 hour to handle database timeouts
- Connection string format: `postgresql://user:password@host:port/database`

The database URL is read from the DATABASE_URL environment variable.

### Session Management

Database sessions are properly managed with:

- Dependency injection via FastAPI's Depends mechanism
- Automatic cleanup via context managers
- Transaction rollback on errors
- Session consistency checks in CRUD operations

### CRUD Operations

All CRUD operations are in crud.py:

- `get_items()` - Retrieve all items
- `create_item()` - Create a new item
- `update_item()` - Update an existing item
- `delete_item()` - Delete an item

Each function includes error handling with proper logging and rollback.

### Schema Design

Schemas are defined in schemas.py using Pydantic:

- `ItemBase` - Base model with common fields
- `ItemCreate` - For POST request validation
- `ItemUpdate` - For PUT request validation (partial updates)
- `Item` - For response serialization

Validators ensure data integrity at request time, not database time.

## Performance Considerations

- Database indexes on frequently queried fields (id, name)
- JWKS response caching (1 hour TTL)
- Efficient SQL queries using SQLAlchemy
- Minimal overhead from validation

## Deployment

For production deployment:

1. Ensure PostgreSQL database is running and accessible
2. Set DATABASE_URL to the PostgreSQL connection string
3. Set AUTH0_DOMAIN and AUTH0_API_AUDIENCE from Auth0 dashboard
4. Run migrations (Phase 1 and Phase 2)
5. Use a production ASGI server (gunicorn, uvicorn with workers)
6. Configure logging to centralized logging service
7. Set up monitoring and alerting
8. Use HTTPS for all endpoints

Example production startup:

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

PostgreSQL-specific recommendations:

- Use a dedicated database user with restricted permissions
- Enable SSL connections: Use `postgresql+psycopg2://` with SSL mode
- Configure backup and recovery procedures
- Monitor connection pool usage and adjust pool_size/max_overflow as needed
- Set up database replication for high availability

## Troubleshooting

### Authentication Errors

If you get `401 Unauthorized`:

- Verify Auth0 credentials in .env file
- Check token is valid and not expired
- Verify token is in Authorization header as "Bearer <token>"

### Database Errors

If you get database connection errors:

- Verify DATABASE_URL is a valid PostgreSQL connection string
- Ensure PostgreSQL server is running: `pg_isready -h localhost -p 5432`
- Check database exists: `psql -U username -l`
- Verify database user has appropriate permissions
- Check connection string format: `postgresql://user:password@host:port/database`
- Test connection: `psql postgresql://user:password@host:port/database`

### Connection Pool Errors

If you get connection pool exhaustion:

- Increase pool_size or max_overflow in database.py
- Check for connection leaks in application code
- Monitor active connections: `SELECT count(*) FROM pg_stat_activity;`

### PostgreSQL-Specific Issues

If psycopg2 installation fails:

- Install system dependencies: `apt-get install postgresql-client libpq-dev`
- Or use psycopg2-binary: `pip install psycopg2-binary`

If you get "FATAL: too many connections":

- Check max_connections setting: `SHOW max_connections;`
- Reduce connection pool size or add more PostgreSQL replicas

### Schema Validation Errors

If you get `400 Bad Request` with validation errors:

- Check request JSON matches expected schema
- Ensure required fields are provided
- Verify field types match schema (string, not number)

## License

This project is part of the python-DevOps repository.

## Contributing

For bug fixes or improvements:

1. Create a feature branch
2. Make your changes
3. Update documentation if needed
4. Submit a pull request

## Support

For issues or questions, refer to the documentation files in the project or the FastAPI documentation at https://fastapi.tiangolo.com/