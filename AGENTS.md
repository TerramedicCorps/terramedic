# Agents — AI Operating Manual

This file is for AI agents working on the Terramedic
project. For general contributor guidance (code style,
testing, commits, PR process), see
[CONTRIBUTING.md](CONTRIBUTING.md). For strategic context,
see [docs/STRATEGY.md](docs/STRATEGY.md).

## Cold Start

An agent dropped into this repo with no prior knowledge
should be able to get the project running from this
section alone.

### Prerequisites

- Node.js 20+ and Yarn
- Python 3.14+ and [Poetry](https://python-poetry.org/)
- Git

All paths below are relative to the repository root.

### Frontend

```bash
git clone https://github.com/TerramedicCorps/terramedic.git
cd terramedic/terramedic
yarn install
yarn dev
```

The frontend runs at `http://localhost:5173`.

### Backend

```bash
cd ../backend  # or cd terramedic/backend from repo root
poetry env use python3.14  # if Python 3.14 isn't default
poetry install
mkdir -p db
DEBUG=true poetry run python manage.py migrate
DEBUG=true poetry run python manage.py runserver
```

The backend runs at `http://localhost:8000`. `DEBUG=true`
is required for local development — it tells Django to
use a dev secret key and enables debug mode.

### Verify Everything Works

```bash
# Frontend (from terramedic/)
yarn lint && yarn test:unit --run && yarn build

# Backend (from backend/)
poetry run ruff check .
poetry run mypy terramedic
poetry run pytest
```

If all of these pass, you're ready to work.

## Full Validation Pass

Before submitting a PR, run:

```bash
# Frontend (from terramedic/)
yarn format
yarn lint
yarn test:unit --run
yarn test:e2e
yarn build

# Backend (from backend/)
poetry run ruff check .
poetry run mypy terramedic
poetry run pytest
```

All green = ready for review.

## Agent Roles

- **Dev Agent:** Implements features, fixes bugs, writes
  tests, submits PRs.
- **PM Agent:** Manages the backlog, triages issues,
  maintains the roadmap.
- **Curator Agent:** Evaluates candidate environmental
  organizations for inclusion in the database.

## Behavioral Guardrails

- No merges without founder review.
- No new dependencies without approval.
- No external communications (social media, email,
  Slack) without sign-off.
- No changes to security-related files, CI/CD config,
  or repo settings without explicit instruction.

## Security

Never commit API keys, `.env` files, or credentials. All
secrets go through environment variables. The `.gitignore`
covers `.env*`, `*.key`, `*.pem`, and `*.p12`. Gitleaks
runs in CI on every push and PR.

GitHub issues are public. Do not put internal strategy
details, organization evaluation scores, partnership
discussions, or personal information in issue or PR
descriptions. Keep PR descriptions technical.

## Human-AI Framing

When writing any user-facing content, PR descriptions, or
issue text, avoid these patterns:

1. **Don't frame humans as subordinate to AI.**
   Write "AI assists with research" not "AI handles
   the work while humans check the output."
2. **Don't frame human effort as replaceable.**
   Write "AI helps scale curation" not "AI replaces
   the need for human curators."
3. **Don't use doom framing about non-adoption.**
   Write "AI can help us do more" not "without AI we
   can't keep up."
4. **Don't frame human work as a bottleneck.**
   Write "human review ensures quality" not "human
   review slows down the pipeline."
5. **Don't frame human roles as leftovers.**
   Write "humans provide judgment and accountability"
   not "humans handle what AI can't do yet."
6. **Don't overstate AI's current role.**
   Write "AI assists with curation" not "AI curates
   our database."

The test: if a volunteer or nonprofit leader read this,
would they feel valued or sidelined?
