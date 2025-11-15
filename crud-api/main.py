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

app = FastAPI(title="CRUD API", version="1.0")

# ---------------------------
# Auth0 Config
# ---------------------------
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE")
AUTH0_ALGORITHMS = ["RS256"]

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

    token = parts[1]

    # Fetch JWKS
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    jwks = requests.get(jwks_url).json()

    unverified_header = jwt.get_unverified_header(token)

    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }

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

