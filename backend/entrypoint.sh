#!/bin/sh
set -e

python manage.py migrate --noinput

# Load seed data only if no organizations exist
python manage.py shell -c "
from terramedic.organizations.models import Organization
if Organization.objects.count() == 0:
    from django.core.management import call_command
    call_command('loaddata', 'seed_data')
    print('Seed data loaded.')
else:
    print('Data already exists, skipping seed.')
"

exec gunicorn terramedic.core.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --access-logfile -
