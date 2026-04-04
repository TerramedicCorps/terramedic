# Architecture

## Overview

Terramedic is a full-stack platform with a SvelteKit
frontend and a Django REST API backend. The frontend is
statically hosted on Netlify. The backend runs on AWS
Lambda via Zappa, backed by PostgreSQL with PostGIS.

```text
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Netlify    │     │  AWS Lambda  │     │  PostgreSQL  │
│  (SvelteKit) │────▶│   (Django)   │────▶│  (PostGIS)   │
│              │     │              │     │              │
│  Static HTML │     │  REST API    │     │  RDS shared  │
│  + JS bundle │     │  Django Ninja│     │  account     │
└──────────────┘     └──────────────┘     └──────────────┘
       ▲                    ▲
       │                    │
   Humans via           AI agents via
   web browser          API / MCP (future)
```

Most pages are prerendered at build time. The frontend
calls the backend API during the build to fetch org data,
then serves static HTML. At runtime, the API is also
available for direct queries.

## Frontend

**Framework:** SvelteKit 2 with Svelte 5, TypeScript,
Tailwind CSS v4, Flowbite Svelte components.

**Key paths:**

| Path | Purpose |
|---|---|
| `terramedic/src/routes/` | Pages: home, about, volunteer, donate, resources, careers, other-actions, warming-stripes, contact-us, privacy |
| `terramedic/src/lib/components/` | Reusable components (~24 files) |
| `terramedic/src/lib/server/api.ts` | API client — fetches org data from the backend |
| `terramedic/src/lib/utils/` | Client utilities (analytics, etc.) |
| `terramedic/src/app.css` | Global styles, Tailwind v4 theme tokens |

**Data flow:** Each page that shows org data has a
`+page.server.ts` load function that calls
`fetchOrganizations()` from `$lib/server/api.ts`. This
hits the backend API at build time (prerendering) or at
request time. Data is passed to the page component as a
`data` prop.

**Prerendering:** Most pages export
`export const prerender = true`. Org data is fetched once
at build time and baked into the static HTML.

## Backend

**Framework:** Django 6 with Django Ninja (REST API),
django-parler (i18n), PostGIS (geospatial).

**Key paths:**

| Path | Purpose |
|---|---|
| `backend/terramedic/core/` | Settings, URL routing, API instance, secrets |
| `backend/terramedic/organizations/` | Models, API endpoints, admin, fixtures |
| `backend/terramedic/organizations/models.py` | Organization and Tag models |
| `backend/terramedic/organizations/api.py` | REST endpoints |
| `backend/terramedic/organizations/fixtures/seed_data.json` | Seed data (~100 orgs, 31 tags) |

**Models:**

- **Organization** (TranslatableModel): name, website_url,
  image_url, category, sort_order, is_active, location
  (PointField). Translated fields: description,
  action_text.
- **Tag**: name (unique). Many-to-many with Organization.
- **Category** choices: donate, volunteer, resource,
  action, career.

**API endpoints** (all public, no auth):

| Endpoint | Description |
|---|---|
| `GET /api/organizations/` | List orgs, optional `?category=` filter |
| `GET /api/organizations/{id}/` | Single org |
| `GET /api/organizations/nearby/` | GIS search by lat/lng/radius |
| `GET /api/health` | Health check |

**Data entry:** Currently via seed fixtures
(`manage.py seed_if_empty`) and Django admin. The curation
pipeline (Initiative 1) will automate evaluation; approved
orgs will be added through the admin or a future write API.

## Infrastructure

**Hosting:**

- Frontend: Netlify (static, prerendered)
- Backend: AWS Lambda via Zappa (containerized)
- Database: RDS PostgreSQL + PostGIS (shared AWS account)
- Static assets: S3 + CloudFront
- DNS: Route53

**Terraform** (`terraform/`):

Provisions the AWS infrastructure across shared and prod
accounts. Key modules: networking (VPC, subnets),
database (RDS), lambda-ecr, zappa (S3 + IAM), secrets
(Secrets Manager), storage (S3 + CloudFront), github-oidc,
monitoring (CloudWatch, budgets).

**Docker:**

The backend Dockerfile builds a Lambda-compatible image
with Python 3.14, SpatiaLite, and GDAL. The entrypoint
runs migrations, seeds data if empty, then starts
gunicorn. `docker-compose.yml` provides a local dev
environment.

## CI/CD

All workflows in `.github/workflows/`:

| Workflow | Triggers | Purpose |
|---|---|---|
| `lint.yml` | Push, PRs | Prettier, ESLint, YAML lint, markdown lint, Ruff, mypy |
| `test.yml` | Push, PRs | pytest (backend), Vitest + Playwright (frontend) |
| `security.yml` | Push, PRs, weekly | CodeQL analysis |
| `secret-scan.yml` | Push, PRs | Gitleaks secret detection |
| `deploy.yml` | Push to main/dev | Build Docker image, push to ECR, deploy via Zappa |
| `dev_cost_control.yml` | Schedule | AWS dev environment cost monitoring |

Deployment uses GitHub OIDC for AWS authentication — no
long-lived credentials. Push to `main` deploys to prod;
push to `dev` deploys to the dev environment.

## Load-Bearing Files

These files are critical to system operation. Understand
them fully before modifying.

**Frontend:**

- `terramedic/svelte.config.js` — Netlify adapter; wrong
  adapter breaks deployment
- `terramedic/src/routes/+layout.svelte` — Root layout;
  affects every page
- `terramedic/src/lib/server/api.ts` — API client; all
  org data flows through this

**Backend:**

- `backend/terramedic/core/settings.py` — Database,
  middleware, installed apps
- `backend/terramedic/core/api.py` — Ninja API instance
  and router registration
- `backend/terramedic/organizations/models.py` — Schema
  changes require migrations
- `backend/Dockerfile` — Lambda runtime image
- `backend/entrypoint.sh` — Startup: migrations + seed

**Infrastructure:**

- `terraform/environments/prod/main.tf` — Production AWS
  resources
- `.github/workflows/deploy.yml` — Deployment pipeline
