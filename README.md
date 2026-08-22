# pets-app

A FastAPI backend and Astro frontends for veterinary clinics to manage services
and appointments — with a public, key-authenticated booking surface designed to
be embedded as a widget on a clinic's own website, no login required for the pet
owner.

- `backend/` — FastAPI + PostgreSQL API, plus a Typer admin CLI
- `frontend/admin/` — Astro SSR dashboard for clinic staff
- `frontend/template/` — Astro template built into a static site per clinic

## Requirements

Python 3.11+, Node 22.12+, Docker (for Postgres).

## Get it running

```bash
git clone <repo-url> && cd cleanings-app

make prepare-env          # writes docker-compose.yml and backend/.env from templates
$EDITOR backend/.env      # fill in SECRET_KEY and POSTGRES_*

make db-up                # Postgres in Docker
make install-deps         # backend deps into the active venv
make upgrade-db           # alembic upgrade head
make run                  # API on :8000 — interactive docs at /docs
```

The admin dashboard, in a second terminal:

```bash
cd frontend/admin && npm install
make admin-dev            # dashboard on :4321
```

Sign in with **"Demo · Clinic admin"** to click through the dashboard without a
backend or any seeded data.

## Tests

```bash
make test                 # both suites
make test-be              # backend (pytest) — needs `make db-up`
make test-admin           # admin dashboard (Playwright) — needs nothing running
```

`make help` lists every target.

## Documentation

**→ [`docs/`](docs/README.md)** — architecture, domain model, per-component
guides, testing, and the roadmap.

Quick links: [architecture](docs/architecture.md) ·
[domain model](docs/domain.md) · [development](docs/development.md) ·
[testing](docs/testing.md) · [roadmap](docs/roadmap.md)
