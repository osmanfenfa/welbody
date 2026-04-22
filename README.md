<div align="center">
  
# Welbody

Provides REST APIs for patients, prescriptions, labs, inventory, pharmacy, triage, nursing, users, and admin utilities.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)](https://sqlalchemy.org)
[![Alembic](https://img.shields.io/badge/Alembic-6BA81E?style=flat-square&logo=alembic&logoColor=white)](https://alembic.sqlalchemy.org)
[![Uvicorn](https://img.shields.io/badge/Uvicorn-2094f3?style=flat-square&logo=uvicorn&logoColor=white)](https://uvicorn.org)

## Features

Modular FastAPI routes organized by domain (patients, pharmacy, lab, etc.)

SQLAlchemy models with Alembic migrations

Service layer and data schemas for clean separation

JWT-based auth, audit logging, and utilities

## Quickstart

Create and activate a virtual environment

Install dependencies

```bash
pip install -r requirements.txt
```

Apply database migrations

```bash
alembic upgrade head
```

Run the development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Structure

`app/` — FastAPI app, routers (`app/api`), services, models, schemas
`migrations/` — Alembic migration scripts
`requirements.txt` — Python dependencies

<div align="center">
