# Static clinic sites (`frontend/template/` → `frontend/sites/`)

Each clinic gets a plain static HTML/CSS/JS folder, built from one shared Astro
template with that clinic's config **baked in at build time**. Deploy it
anywhere — S3, Cloudflare Pages, Netlify, nginx, or straight from FastAPI's
`StaticFiles`.

## The command chain

```
backend/cli   (Typer, Python)  →  talks to the FastAPI backend over HTTP
                                  (auth, list clinics, read active public key)
                        ↓
frontend/scripts/generate-site.mjs   (Node)  →  drives `astro build`
                        ↓
frontend/sites/<slug>/         plain static output, one folder per clinic
```

The CLI's job is to resolve real values — the clinic's `slug` and its most recent
active `pk_live_` key — from the backend, so nobody hand-types them into a build
command. See [admin-cli.md](admin-cli.md).

## Prerequisites

```bash
cd backend && pip install -r requirements-cli.txt   # CLI (Python)
cd frontend/template && npm install                 # Astro template (Node)
```

The backend support this depends on — `clinics.slug`, `GET /clinics/`, the
`require_superuser` dependency, and superuser bypass on clinic/API-key
permissions — is **already in the codebase**. Nothing needs to be applied by
hand; just run migrations (`make upgrade-db`) like normal.

## End-to-end flow

```bash
# one-time: create the platform superuser
python -m cli.main bootstrap

# everyday
python -m cli.main login
python -m cli.main clinics list
#  Slug        Name        ID
#  acme-vet    Acme Vet    3f2b...

python -m cli.main sites generate 3f2b... --public-api-url https://api.yourdomain.com/api
# ✓ built frontend/sites/acme-vet/
```

All CLI commands run from `backend/`, so `cli` resolves as a package.

## Config is baked in — nothing rebuilds itself

Because each site's clinic id, public key, and API URL are injected at build
time, **a change to `frontend/template/` does not reach any already-built site.**
After any template change, rebuild everyone:

```bash
python -m cli.main sites generate-all --public-api-url https://api.yourdomain.com/api
```

## Generated output is gitignored

`frontend/.gitignore` covers `sites/` and `clinics.json`. That matters: build
output contains **live publishable keys** (`frontend/sites/registry.json` records
each site's `slug`, `clinicId`, `key`, `apiUrl`, and `lastBuiltAt`). The keys are
publishable-style and safe in client-side JS, but there's no reason to commit
them. `frontend/clinics.example.json` is the tracked template.

## Deliberately not addressed yet

- **The actual booking UI.** The template has components for hero, services,
  hours, and a `BookingWidget`, but `index.astro` is still substantially a
  placeholder proving config injection works.
- **What triggers `sites generate` in practice.** Today it's a person running the
  CLI by hand after creating a clinic and issuing its key. An automatic trigger
  (e.g. a webhook on key creation) is a reasonable next step once the manual flow
  feels solid.
- **Hosting/deploy automation** for `frontend/sites/*`.
- **`pk_live_` / `pk_test_` isolation** — a pre-existing platform-wide gap, not
  specific to static sites. See [roadmap.md](roadmap.md).
