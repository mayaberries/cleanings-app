# Admin CLI (`backend/cli/`)

A Typer CLI that is a **pure HTTP client of the same API** — no direct DB access,
so it works unmodified against local, staging, or production.

It exists for the two things the JWT staff API alone doesn't cover:

1. Cross-tenant platform operations (listing/creating clinics as a superuser)
2. Driving the [static-site generator](static-sites.md) from real clinic data
   instead of hand-typed flags

```bash
pip install -r requirements-cli.txt
```

Kept separate from `requirements.txt` **on purpose** — the API server itself
never imports from `cli/`.

All commands run from `backend/`, so `cli` resolves as a package:
`python -m cli.main <command>`.

## One-time setup: the platform superuser

```bash
python -m cli.main bootstrap
# prompts for API base URL (default http://localhost:8000/api), email,
# username, password
# → creates the one platform superuser and logs the CLI in as them
```

Genuinely one-time: `ix_users_single_superuser` (a partial unique index)
guarantees at most one row can have `is_superuser = true`, and the bootstrap
endpoint 403s cleanly on every call after the first.

There is no supported way to add a *second* superuser or transfer the role.
`backend/scripts/promote_superuser.py` exists, but it **talks to the DB directly**
and isn't gated the same way — treat it as a manual, trusted-operator-only tool
you'd run with the same access level as a hand-written migration, not a flow.

## Everyday session

```bash
python -m cli.main login     # any existing user; superuser-only commands
                             # 403 if this account isn't the superuser
python -m cli.main whoami
python -m cli.main logout
```

Session (API base URL + JWT) is stored in
`~/.config/pets-admin-cli/credentials.json`.

## Clinics

```bash
python -m cli.main clinics list
python -m cli.main clinics create "Acme Vet" --phone "555-0100"
python -m cli.main clinics create-key <clinic_id> --label "Website widget"
python -m cli.main clinics keys <clinic_id>
```

> `clinics create` links the new clinic to **whoever is logged in**, the same as
> the normal clinic_admin signup flow. It works once per user, because a user can
> only belong to one clinic (`clinic_id` must be null going in). This means even
> the superuser can't provision several clinics on other people's behalf yet —
> see [roadmap.md](roadmap.md).

## Static sites

```bash
python -m cli.main sites generate <clinic_id> --public-api-url https://api.yourdomain.com/api
python -m cli.main sites generate-all --public-api-url https://api.yourdomain.com/api
```

`generate-all` walks every clinic via `GET /clinics/`. You need it after **any**
change to `frontend/template/`, since config is baked in at build time and
nothing rebuilds itself. Details in [static-sites.md](static-sites.md).
