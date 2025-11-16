from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Validate that DATABASE_URL is a PostgreSQL connection string
if not SQLALCHEMY_DATABASE_URL.startswith("postgresql://") and not SQLALCHEMY_DATABASE_URL.startswith("postgresql+psycopg2://"):
    raise ValueError("DATABASE_URL must be a PostgreSQL connection string (postgresql://... or postgresql+psycopg2://...)")

# PostgreSQL connection pooling configuration
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,           # Number of connections to keep in the pool
    max_overflow=20,        # Maximum overflow connections
    pool_pre_ping=True,     # Test connections before using them
    pool_recycle=3600,      # Recycle connections after 1 hour
    echo=False              # Set to True for SQL query logging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
