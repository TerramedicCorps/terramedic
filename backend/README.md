# Terramedic Backend

Django backend for the Terramedic platform.

## Setup

```bash
cd backend
python3.14 -m venv .venv
source .venv/bin/activate
poetry install
python manage.py migrate
python manage.py runserver
```

## Requirements

- Python 3.14+
- SpatiaLite (for local development)
- PostgreSQL + PostGIS (for production)
