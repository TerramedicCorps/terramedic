#!/bin/sh
set -e

mkdir -p /app/db

python manage.py migrate --noinput

exec gunicorn terramedic.core.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --access-logfile -
