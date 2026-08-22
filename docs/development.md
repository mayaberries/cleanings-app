# Development

Everything here is driven by the root `Makefile`. Run `make help` for the full
list of targets — this page covers what the target names don't tell you.

## First-time setup

```bash
make prepare-env      # copies docker-compose.yml.dist → docker-compose.yml
                      # and backend/.env.template → backend/.env (both cp -n,
                      # so it never clobbers an existing file)
# fill in SECRET_KEY and POSTGRES_* in backend/.env

make db-up            # Postgres 13 in Docker, container fastapi-pets-db
make install-deps     # backend/requirements.in into the active venv
make upgrade-db       # alembic upgrade head
make run              # uvicorn, reload — interactive docs at /docs

cd frontend/admin && npm install && make admin-dev
```

`docker-compose.yml` and `backend/.env` are both gitignored, which is why the
`.dist`/`.template` pair exists.

## The two dev servers

| | Command | Port |
|---|---|---|
| Backend API | `make run` | 8000 (`/api` prefix) |
| Admin dashboard | `make admin-dev` | 4321 |

The admin app reads `BACKEND_API_URL` (see `frontend/admin/.env.example`,
default `http://localhost:8000/api`). The dashboard's demo login needs no
backend at all — see [admin-dashboard.md](admin-dashboard.md).

## Dependency management (backend)

`requirements.in` is the hand-edited list; `requirements.txt` is the frozen
lockfile. After adding a dependency, edit `.in` then:

```bash
make update-deps      # installs .in, then refreezes .txt
```

`make freeze-deps` refreezes without installing. Both filter out `pip-chill`.
`backend/requirements-cli.txt` is separate on purpose — the API server never
imports from `cli/`.

## Gotchas worth knowing before you lose time to them

**`astro dev` self-daemonizes.** In this Astro version it forks a background
server and the launching command exits immediately. So a plain `astro dev` won't
block, `astro dev` in a background shell won't behave the way you expect, and a
second invocation prints *"Dev server already running"* rather than starting a
new one. Manage it explicitly:

```bash
astro dev --background      # start
astro dev status
astro dev logs              # only works if started with --background
astro dev stop
```

This is also why the Playwright config runs the *built* Node entrypoint
(`npm run build && npm start`) instead of `astro dev` — Playwright's `webServer`
can't supervise or clean up a process that forks away from it.

**You can't drive Astro Actions with curl.** Actions enforce a CSRF origin check,
so a bare `curl -X POST /_actions/login` gets a 403, and adding an `Origin`
header still won't produce a usable session cookie. Use Playwright (or a real
browser) to exercise anything that logs in. This costs more time than it should
if you don't know it up front.

**Astro's `output: "server"` shares module state across requests.** Any
module-level mutable value — a nanostores atom, a cache, a plain `let` — is
shared by every concurrent visitor in that Node process. For auth state this is
a data-leak bug, not a style issue. The rules are in
[admin-dashboard.md](admin-dashboard.md#nanostores-never-set-from-server-code).

**Permission checks are intentionally duplicated** between `app/api/dependencies/`
and `app/db/repositories/`. Changing a rule in one place is not enough; see
[architecture.md](architecture.md#known-drift-risk-duplicated-permission-checks).

## Editor / tooling notes

- `make pep` runs `autopep8` across the backend in place.
- `.claude/settings.json` denies edits to `.idea/**` and `*.iml` so JetBrains
  project files don't get churned by tooling.
- `docs/proto/` is a static, no-build prototype of the dashboard. It has no
  relationship to the running app beyond being the design target — open its HTML
  files directly in a browser. See [proto/README.md](proto/README.md).
