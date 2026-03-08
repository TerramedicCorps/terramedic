#!/bin/sh
set -e

python manage.py migrate --noinput

# Load seed data only if explicitly enabled and no organizations exist
if [ "${LOAD_SEED_DATA:-false}" = "true" ]; then
  python manage.py seed_if_empty
fi

exec gunicorn terramedic.core.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --access-logfile -
