# Static clinic site generation — mechanism overview

Two halves, one command chain:

```
backend/cli   (Typer, Python)  →  talks to the FastAPI backend over HTTP
                                    (auth, list clinics, read active public key)
                                ↓
frontend/scripts/generate-site.mjs  (Node)  →  drives `astro build`
                                ↓
frontend/sites/<slug>/         plain static HTML/CSS/JS, deploy anywhere
```

## What you need to add to the backend first

1. Apply the migration: `f1a2b3c4d5e6_add_clinic_slug.py` (adds `clinics.slug`).
2. Drop in the updated `app/models/clinics/clinic.py`, `app/db/repositories/clinics.py`,
   `app/api/dependencies/roles.py`, `app/api/dependencies/clinics.py`,
   `app/api/dependencies/clinic_api_keys.py`, `app/api/routes/clinics.py`.
   - Adds `GET /clinics/` (list all clinics — new, platform-operator only).
   - Adds `require_superuser` dependency, using the `is_superuser` column
     that already existed on `users` but was never checked anywhere.
   - `check_clinic_modification_permissions` / `check_clinic_admin_permissions`
     now let a superuser manage *any* clinic, not just their own — needed
     so the CLI can read any clinic's active public key.
3. Promote yourself: `python scripts/promote_superuser.py you@yourclinic.com`
   — deliberately not an HTTP endpoint, run this with the same access
   level you'd use to run a migration by hand.

**I reconstructed `create_clinic_for_admin` / `join_clinic_as_staff` in the
repository file from what I'd already seen of them — diff it against your
actual file before applying, in case I mis-transcribed some detail I
didn't have full visibility into.**

## Installing the two toolchains

```bash
# CLI (Python)
cd backend
pip install -r requirements-cli.txt

# Astro template (Node)
cd ../frontend/template
npm install
```

## End-to-end flow

```bash
# one-time
python backend/scripts/promote_superuser.py you@yourclinic.com

python -m cli.main login   # prompts for API base URL, email, password
# (run from backend/, so `cli` resolves as a package)

python -m cli.main clinics list
#  Slug        Name        ID
#  acme-vet    Acme Vet    3f2b...

python -m cli.main sites generate 3f2b... --public-api-url https://api.yourdomain.com/api
# ✓ built frontend/sites/acme-vet/

# after any template change, rebuild everyone (config is baked in, so
# nothing rebuilds itself automatically):
python -m cli.main sites generate-all --public-api-url https://api.yourdomain.com/api
```

Output is a plain static folder per clinic — ship it to S3 / Cloudflare
Pages / Netlify / nginx, or serve it straight from FastAPI's `StaticFiles`
for the simplest possible MVP.

## Deliberately not addressed yet

- The actual booking UI (calendar/slot picker/guest form) — `index.astro`
  is a placeholder that only proves config injection works.
- What triggers `sites generate` in practice — right now it's a person
  running the CLI by hand after creating a clinic + issuing its key.
  Wiring an automatic trigger (e.g. a webhook on key creation) is a
  reasonable next step once this manual flow feels solid.
- Hosting/deploy automation for `frontend/sites/*` output.
- `pk_live_`/`pk_test_` environment isolation (pre-existing gap, documented
  in the main README's roadmap — matters more once test keys get handed
  to a real second clinic).
