# CRUD API

This project is a simple CRUD (Create, Read, Update, Delete) application built with FastAPI and SQLite. It is intended for learning and practicing API development, database interaction, and general Python application structure.

## Overview

The application provides basic CRUD operations using FastAPI as the web framework and SQLAlchemy for database interaction. The data is stored in a local SQLite database, which is created automatically when the application runs for the first time.

## Project Structure

```
crud-api/
│── main.py # API entry point
│── models.py # SQLAlchemy models
│── schemas.py # Pydantic request/response schemas
│── database.py # Database engine and session utilities
│── crud_test.py # Test script for basic API functionality
│── crud.db # SQLite database (auto-created)
│── venv/ # Virtual environment (ignored by Git)
│── README.md

```

## Setup Instructions

### 1. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate

pip install fastapi uvicorn sqlalchemy pydantic

uvicorn main:app --reload

http://localhost:8000

http://localhost:8000/docs

python3 crud_test.py
```

Notes

The SQLite database file crud.db is created automatically.

The venv/ folder and cache directories are excluded from version control.

This project is part of a larger repository containing multiple Python-based learning projects.