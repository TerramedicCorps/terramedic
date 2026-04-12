# Terramedic Backend

Django backend for the Terramedic platform.

> **Note on architecture:** The SvelteKit frontend
> (`../terramedic/`) and this Django backend are deployed
> separately. Netlify deploy previews only serve the frontend
> — Django routes like `/admin/` and `/api/` are **not**
> reachable from a Netlify preview URL. To review admin or
> API work on a PR, run this backend locally (or against the
> deployed Zappa stage, if available).

## Requirements

- Python 3.14+
- SpatiaLite (for local development)
- PostgreSQL + PostGIS (for production)

## Setup

```bash
cd backend
python3.14 -m venv .venv
source .venv/bin/activate
poetry install --with curation  # omit --with curation if you
                                 # don't need the AI eval CLI
python manage.py migrate
python manage.py runserver
```

The dev server listens on <http://localhost:8000>.

## Viewing the admin

1. Create a superuser (one-time):

   ```bash
   python manage.py createsuperuser
   ```

2. Open <http://localhost:8000/admin/> and sign in.

The evaluation queue dashboard is under **Nominations** →
**Evaluations** in the admin sidebar.

## Running in Docker (matches CI)

If you want an environment identical to what `test.yml` uses:

```bash
docker build -t terramedic-backend .
docker run --rm -p 8000:8000 \
  -e DEBUG=true \
  -e SECRET_KEY=dev-key \
  -e ALLOWED_HOSTS=localhost,127.0.0.1 \
  terramedic-backend
```

Then `docker exec -it <container> python manage.py createsuperuser`
to be able to sign into the admin.

## Deployed backend (Zappa)

If the backend is deployed to AWS Lambda via Zappa, the admin
lives at the API Gateway URL for that stage. To find it:

```bash
poetry run zappa status dev
```

No custom domain is currently configured, so the URL will be a
raw `*.execute-api.*.amazonaws.com` address.
