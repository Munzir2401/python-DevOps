import os
from fastapi import FastAPI, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from jose import jwt
import requests

import models, schemas, crud
from database import SessionLocal, engine

from dotenv import load_dotenv
load_dotenv()

# ---------------------------
# Create DB Tables
# ---------------------------
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CRUD API", 
    version="1.1",
    description="""
    ## CRUD API with Auth0 Integration
    
    ### Version History
    - **v1.1**: (Current) Made description field optional in ItemBase/ItemCreate (description: str | None = None).
      ItemUpdate now supports true partial updates with all optional fields.
    - **v1.0**: Initial release with required description field.
    
    ### Migration Notes
    - Existing NULL description values are coerced to empty string on read for backward compatibility.
    - Clients should update to send optional description fields in create/update requests.
    """
)

# ---------------------------
# Auth0 Config
# ---------------------------
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE")
AUTH0_ALGORITHMS = ["RS256"]

if not AUTH0_DOMAIN or not AUTH0_API_AUDIENCE:
    raise RuntimeError("AUTH0_DOMAIN and AUTH0_API_AUDIENCE must be set")

# ---------------------------
# Database Dependency
# ---------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------
# JWT Verification
# ---------------------------
def verify_jwt(request: Request):
    """Verify Auth0-issued JWT"""

    auth = request.headers.get("Authorization")
    if not auth:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    parts = auth.split()
    if parts[0].lower() != "bearer" or len(parts) != 2:
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
from functools import lru_cache
from datetime import datetime, timedelta

# Cache JWKS for 1 hour
_jwks_cache = {"data": None, "expires_at": None}

def get_jwks():
    """Fetch and cache JWKS from Auth0"""
    now = datetime.utcnow()
    if _jwks_cache["data"] and _jwks_cache["expires_at"] and now < _jwks_cache["expires_at"]:
        return _jwks_cache["data"]
    
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    try:
        response = requests.get(jwks_url, timeout=10)
        response.raise_for_status()
        jwks = response.json()
        _jwks_cache["data"] = jwks
        _jwks_cache["expires_at"] = now + timedelta(hours=1)
        return jwks
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Unable to fetch JWKS: {str(e)}")

def verify_jwt(request: Request):
    """Verify Auth0-issued JWT"""
    
    auth = request.headers.get("Authorization")
    if not auth:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    parts = auth.split()
    if parts[0].lower() != "bearer" or len(parts) != 2:
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    
    token = parts[1]
    
    jwks = get_jwks()
    
    # Wrap jwt.get_unverified_header in try/except to catch malformed tokens
    try:
        unverified_header = jwt.get_unverified_header(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Malformed token: unable to read header")
    
    # Validate jwks is a dict with "keys" list
    if not isinstance(jwks, dict):
        raise HTTPException(status_code=401, detail="Invalid JWKS format: expected dict")
    
    if "keys" not in jwks:
        raise HTTPException(status_code=401, detail="Invalid JWKS format: missing 'keys' field")
    
    if not isinstance(jwks["keys"], list):
        raise HTTPException(status_code=401, detail="Invalid JWKS format: 'keys' must be a list")
    
    # Required fields for RSA key
    required_fields = {"kid", "kty", "use", "n", "e"}
    
    rsa_key = {}
    for key in jwks["keys"]:
        # Validate key is a dict
        if not isinstance(key, dict):
            raise HTTPException(status_code=401, detail="Invalid JWKS format: key entry must be a dict")
        
        # Validate all required fields exist and are strings
        for field in required_fields:
            if field not in key:
                raise HTTPException(status_code=401, detail=f"Invalid JWKS format: missing required field '{field}' in key")
            if not isinstance(key[field], str):
                raise HTTPException(status_code=401, detail=f"Invalid JWKS format: field '{field}' must be a string")
        
        # Check if this key matches the token header
        if key["kid"] == unverified_header.get("kid"):
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
            break

    if not rsa_key:
        raise HTTPException(status_code=401, detail="Invalid token header")

    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=AUTH0_ALGORITHMS,
            audience=AUTH0_API_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")

    return payload


# ---------------------------
# Public Routes
# ---------------------------
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running"}

@app.get("/")
def root():
    return {"message": "CRUD API is running"}


# ---------------------------
# Protected Routes (CRUD)
# ---------------------------
@app.post("/items")
def create_item(item: schemas.ItemCreate,
                db: Session = Depends(get_db),
                payload=Depends(verify_jwt)):
    return crud.create_item(db, item)

@app.get("/items")
def read_items(db: Session = Depends(get_db),
               payload=Depends(verify_jwt)):
    return crud.get_items(db)

@app.put("/items/{item_id}")
def update_item(item_id: int, item: schemas.ItemUpdate,
                db: Session = Depends(get_db),
                payload=Depends(verify_jwt)):
    return crud.update_item(db, item_id, item)

@app.delete("/items/{item_id}")
def delete_item(item_id: int,
                db: Session = Depends(get_db),
                payload=Depends(verify_jwt)):
    return crud.delete_item(db, item_id)

