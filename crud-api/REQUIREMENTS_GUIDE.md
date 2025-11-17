# Requirements Files - Complete Guide

## Files Overview

### 1. **requirements.txt** (Production)
Contains only the dependencies needed to **run the application in production**.

### 2. **requirements-dev.txt** (Development)
Contains all production dependencies PLUS development/testing tools.

---

## requirements.txt - Detailed Breakdown

### Web Framework
```
FastAPI==0.104.1
```
- Modern async Python web framework
- Used for: Building the API with route decorators (@app.get, @app.post)
- Why: Industry standard, great for APIs, built-in OpenAPI docs

```
uvicorn[standard]==0.24.0
```
- ASGI server (runs FastAPI)
- Used for: Starting the HTTP server (`python main.py` or `uvicorn main:app`)
- Why: Production-grade server, supports async, works with gunicorn

---

### Database
```
SQLAlchemy==2.0.23
```
- SQL Object Relational Mapper (ORM)
- Used for: Define models (Item class), query database, connection pooling
- Why: Industry standard, abstract database operations, works with any SQL DB

```
psycopg2-binary==2.9.9
```
- PostgreSQL database driver
- Used for: Enables SQLAlchemy to connect to PostgreSQL
- Why: Most reliable PostgreSQL driver for Python
- Note: Binary version (psycopg2-binary) is easier to install than psycopg2

---

### Authentication & JWT
```
python-jose[cryptography]==3.3.0
```
- JWT (JSON Web Token) library
- Used for: Decoding and verifying JWT tokens from Auth0
- Why: Standard for OAuth2/JWT workflows
- Note: `[cryptography]` extra includes RSA support for signature verification

```
PyJWT==2.8.1
```
- Alternative JWT library (provides backup functionality)
- Used for: Additional JWT handling capabilities
- Note: python-jose is primary; this is for additional coverage

```
cryptography==41.0.7
```
- Cryptographic library for Python
- Used for: RSA key operations, signature verification
- Why: Secure cryptographic operations for JWT validation

---

### Data Validation
```
pydantic==2.5.0
```
- Runtime data validation library
- Used for: ItemCreate, ItemUpdate, Item schemas (request/response models)
- Why: Validates incoming JSON, generates OpenAPI schema, type-safe
- Example: Ensures name is string, description is string/optional

```
pydantic-settings==2.1.0
```
- Settings management with Pydantic
- Used for: Could be used for environment variable validation
- Why: Type-safe environment variable loading (optional, good practice)

---

### Environment Variables
```
python-dotenv==1.0.0
```
- Load environment variables from .env file
- Used for: Load AUTH0_DOMAIN, AUTH0_API_AUDIENCE, DATABASE_URL
- Why: Development convenience, keeps secrets out of code

---

### HTTP Client
```
requests==2.31.0
```
- HTTP library for making HTTP requests
- Used for: Fetching JWKS from Auth0 (`get_jwks()` function)
- Why: Simple, reliable, industry standard

---

### Utilities
```
typing-extensions==4.8.0
```
- Additional typing features
- Used for: Type hints compatibility across Python versions
- Why: Ensures type hints work on older Python versions

---

## requirements-dev.txt - Detailed Breakdown

Contains everything from requirements.txt PLUS:

### Testing
```
pytest==7.4.3
```
- Testing framework
- Used for: Writing and running unit tests
- Why: Industry standard, great fixtures, plugins

```
pytest-asyncio==0.21.1
```
- Async test support for pytest
- Used for: Testing async FastAPI routes
- Why: Handles async/await in tests

```
httpx==0.25.1
```
- Async HTTP client
- Used for: Making test requests to API endpoints
- Why: Works with async, supports FastAPI TestClient

---

### Code Quality
```
pylint==3.0.3
```
- Code linter
- Used for: Check code for errors and style issues
- Why: Catches bugs, enforces consistency

```
black==23.12.0
```
- Code formatter
- Used for: Automatically format Python code
- Why: Consistent style, no debates, industry standard

```
isort==5.13.2
```
- Import sorter
- Used for: Sort and organize imports at top of files
- Why: Consistent import order, catches unused imports

```
flake8==6.1.0
```
- Linter (PEP8 style checker)
- Used for: Check PEP8 style compliance
- Why: Catches style issues, undefined names

---

### Type Checking
```
mypy==1.7.1
```
- Static type checker
- Used for: Verify type hints are correct
- Why: Catches type errors before runtime

```
types-requests==2.31.0.10
```
- Type hints for requests library
- Used for: mypy understanding of requests library
- Why: Type checking requests calls

---

### Development Server
```
watchfiles==0.20.0
```
- File watcher
- Used for: Auto-reload server when code changes
- Why: During development, reload on file change (used by uvicorn --reload)

---

### Documentation
```
sphinx==7.2.6
sphinx-rtd-theme==2.0.0
```
- Documentation generation
- Used for: Generate HTML docs from docstrings
- Why: Professional documentation, industry standard

---

## Installation Instructions

### For Production
```bash
pip install -r requirements.txt
```

### For Development/Testing
```bash
pip install -r requirements-dev.txt
```

### For Specific Environment
```bash
# Virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt  # or requirements-dev.txt
```

---

## Dependency Tree

```
FastAPI Project
│
├── Web Framework
│   ├── FastAPI
│   └── uvicorn
│
├── Database
│   ├── SQLAlchemy
│   └── psycopg2-binary
│
├── Authentication
│   ├── python-jose
│   ├── PyJWT
│   └── cryptography
│
├── Validation
│   ├── pydantic
│   └── pydantic-settings
│
├── Configuration
│   └── python-dotenv
│
├── HTTP Client
│   └── requests
│
└── Development (in requirements-dev.txt)
    ├── Testing: pytest, pytest-asyncio, httpx
    ├── Code Quality: pylint, black, isort, flake8
    ├── Type Checking: mypy, types-requests
    ├── Development: watchfiles
    └── Documentation: sphinx, sphinx-rtd-theme
```

---

## Version Pinning Strategy

All packages are **pinned to specific versions** (e.g., `FastAPI==0.104.1`) to ensure:

1. **Reproducibility**: Same versions everywhere (local, CI/CD, production)
2. **Stability**: No unexpected breaking changes
3. **Security**: Controlled dependency updates

### When to Update
```bash
# Check for outdated packages
pip list --outdated

# Update to latest (use with caution)
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade FastAPI
```

---

## Python Version Requirements

Based on the packages used, minimum Python version is:
- **Python 3.8+** (FastAPI/Pydantic support)
- **Recommended: Python 3.9+** (better performance)
- **Current standard: Python 3.11+**

---

## Installing Requirements in Ansible

For your Ansible deployment, you would typically do:

```yaml
- name: Install Python dependencies
  pip:
    requirements: /path/to/requirements.txt
    virtualenv: /opt/crud-api/venv
```

Or in your Terraform/Ansible setup:

```bash
pip install -r crud-api/requirements.txt
```

---

## Key Differences: requirements.txt vs requirements-dev.txt

| Category | requirements.txt | requirements-dev.txt |
|----------|------------------|----------------------|
| **Purpose** | Production only | Development + Testing |
| **FastAPI** | ✅ | ✅ |
| **pytest** | ❌ | ✅ |
| **pylint** | ❌ | ✅ |
| **black** | ❌ | ✅ |
| **mypy** | ❌ | ✅ |
| **Size** | ~10 packages | ~25 packages |
| **Install Time** | Fast | Slower |
| **Disk Space** | Less | More |
| **Use Case** | Docker, AWS, Production | Local development, testing |

---

## Troubleshooting Common Issues

### Issue: "ModuleNotFoundError: No module named 'fastapi'"
```bash
# Solution: Install requirements
pip install -r requirements.txt
```

### Issue: PostgreSQL connection fails
```bash
# Make sure psycopg2 is installed
pip install psycopg2-binary

# And DATABASE_URL is set
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
```

### Issue: Auth0 JWT verification fails
```bash
# Make sure required packages are installed
pip install python-jose cryptography

# And environment variables are set
export AUTH0_DOMAIN="your-domain.auth0.com"
export AUTH0_API_AUDIENCE="your-api-id"
```

### Issue: Can't import mypy/pytest
```bash
# Make sure you installed dev requirements
pip install -r requirements-dev.txt
```

---

## Upgrading Packages Safely

```bash
# Check current versions
pip list

# Check for security vulnerabilities
pip install safety
safety check

# Generate updated requirements.txt
pip install pip-tools
pip-compile --upgrade requirements.in  # if you use requirements.in

# Update specific package
pip install --upgrade FastAPI
pip freeze > requirements.txt
```

---

## Next Steps

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **For development, also install**:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Run the application**:
   ```bash
   python main.py
   # or
   uvicorn main:app --reload
   ```

4. **Run tests**:
   ```bash
   pytest crud_test.py
   ```

5. **Check code quality**:
   ```bash
   pylint crud-api/*.py
   black crud-api/
   mypy crud-api/
   ```
