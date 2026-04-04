# Product Roadmap

This roadmap is aligned with
[docs/STRATEGY.md](STRATEGY.md). Each phase has clear
deliverables that can be decomposed into GitHub issues.

## Phase 1: Database and Curation Pipeline

**Goal:** Populate the database at scale with curated
environmental organizations.

**Deliverables:**

- Curation schema (JSON Schema defining the evaluation
  output format)
- Semi-automated curation pipeline (Python CLI tool)
- Curator system prompt and 5-step evaluation checklist
- First batch of organizations evaluated through the
  pipeline and approved by a human reviewer
- Database populated with 100+ curated orgs
- Seed data replaced by pipeline-sourced data
- Curation review UI in Django admin — a dedicated
  interface for reviewing, approving, and rejecting
  pipeline evaluations

**Depends on:** Nothing — this is the foundation.

## Phase 2: Public API

**Goal:** Expose the curated database through a public
REST API that external consumers can query.

**Deliverables:**

- Public API endpoints for querying orgs by SDG,
  geography, participation type, evidence score, and
  other metadata
- Schema extended to capture what each org needs — not
  just who they are, but what kinds of work (human or AI)
  would help them
- API documentation (OpenAPI / Swagger)
- Rate limiting and usage monitoring
- API versioning strategy

**Depends on:** Phase 1 (needs data in the database).

## Phase 3: MCP Server

**Goal:** Make the database queryable by AI agents through
the Model Context Protocol.

**Deliverables:**

- MCP server wrapping the public API
- Org discovery queries ("find orgs working on ocean
  conservation in Southeast Asia")
- Needs discovery queries ("find orgs that need compute
  for biodiversity monitoring")
- Documentation for agent developers
- Tested with at least one MCP-compatible AI agent

**Depends on:** Phase 2 (needs the API).

## Phase 4: Website Refresh and Agent Onboarding

**Goal:** Improve the human experience and add an
agent-facing entry point.

**Deliverables:**

- Improved search and filtering for human users
- Developer- and agent-facing section: API docs, MCP
  setup guides, examples of how agents can contribute
- Mobile experience improvements
- Content updated to reflect the expanded database

**Depends on:** Phases 1–3 (needs data, API, and MCP
in place).

## Current Status

- Phase 1: Partially started. Database schema, Django
  models, and curation evaluation schema exist. Curation
  pipeline CLI tool, review UI, and initial curated
  dataset not yet built.
- Phase 2: Partially started. Basic API endpoints exist
  (list, detail, nearby). Public documentation and
  extended schema not yet built.
- Phase 3: Not started.
- Phase 4: Not started. Current site is a working
  prototype.
