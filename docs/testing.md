# Testing

```bash
make test          # both suites
make test-be       # backend only — pytest, needs the dockerized db up
make test-admin    # admin dashboard only — Playwright
```

CI (`.github/workflows/tests.yml`) runs both on push/PR to `master`: the backend
fully dockerized via `make test-be-docker` (build + ephemeral db, no local
Postgres needed), and the admin suite on `lts/*` Node with the Playwright HTML
report uploaded as an artifact for 30 days.

## Backend (`backend/tests/`)

pytest + pytest-asyncio in strict mode, driving httpx `AsyncClient` **against the
ASGI app directly** — no live server needed.

Tests are grouped by domain, matching the shape described in
[architecture.md](architecture.md):

```
tests/appointments/    test_create.py, test_accept.py, test_cancel.py, …
tests/clinics/  tests/evaluations/  tests/pets/  tests/profiles/
tests/public_booking/  tests/services/  tests/users/  tests/feed/
tests/_fixtures/       shared fixtures
tests/_helpers/
```

> **Known limitation — the test DB is not reset between tests.** Migrations are
> session-scoped and users aren't recreated if they already exist by email. This
> causes flaky failures when two tests' appointment fixtures land in overlapping
> time windows for the same provider.
>
> Current mitigation: wide randomized fixture time windows. That is a workaround,
> not a fix — the real answer is per-test transaction rollback, which hasn't been
> built. **If you see an intermittent appointment-conflict failure, suspect this
> before suspecting your change.**

`tests/feed/` is skipped — the Feed feature is dormant, see
[domain.md](domain.md#feed).

## Admin dashboard (`frontend/admin/tests/`)

Playwright, three browser projects (chromium, firefox, webkit). Specs run against
the **built** Node entrypoint, not `astro dev` — see the gotcha in
[development.md](development.md#gotchas-worth-knowing-before-you-lose-time-to-them).

Everything runs in demo mode, so **no API or database needs to be up.**

```
tests/onboarding.spec.ts   the signup wizard, end to end
tests/nav.spec.ts          tab bar + the role gate
tests/fixtures/            input data
tests/helpers/             page actions
tests/wip/                 roadmap specs — see below
```

Data and page-actions are kept in separate files (`fixtures/onboarding.ts` vs
`helpers/onboarding.ts`) so other specs can reuse either half.

### `tests/wip/` — the roadmap as skipped tests

These specs describe admin UI that **doesn't exist yet**. They're written against
`docs/openapi.json` (the backend already supports every endpoint they reference).
Every `describe` is `.skip`'d, so they report as *skipped* rather than failing —
**that skip count is the roadmap, and it should shrink as pages get built.**

| Spec | Backend support | UI status |
|---|---|---|
| `services.spec.ts` | `GET/POST /api/services/`, `PUT/DELETE /api/services/{id}/` | route stub only |
| `appointments.spec.ts` | list/confirm/cancel/withdraw under `/api/services/{id}/appointments/` | route stub only |
| `api-keys.spec.ts` | `GET/POST /api/clinics/{id}/api-keys/`, `DELETE …/{key_id}/` | route stub; onboarding issues the first key |
| `clinic-settings.spec.ts` | `clinics` tag (profile + staff join), `clinic-availability` tag | no route yet (`/settings/*`) |
| `superadmin-clinics.spec.ts` | `GET /api/clinics/` | route stub only |

To graduate one:

1. Move the spec out of `tests/wip/` into `tests/`.
2. Drop the `.skip`.
3. Replace the placeholder selectors with what the real page renders — treat
   these as **acceptance criteria to satisfy, not markup to match exactly**.
4. If it needs data beyond `tests/wip/fixtures.ts`, promote that into
   `tests/fixtures/` following the `fixtures/` + `helpers/` split above.
5. Delete the now-unused export from `tests/wip/fixtures.ts`.

Not covered by `wip/`, deliberately — these serve the public booking widget and
the pet-owner client, not clinic staff: `public-booking`, `pets`, `clinic_pets`,
`clinic_owners`, `feed`, `profiles/{username}`, `users/claim`, `evaluations`.

### Current coverage gap

`buildDemoUser()` only ever returns a `clinic_admin`, so the **superadmin half of
the role gate is untested** — nothing exercises the Clinics tab, or a superadmin
being kept off `/overview`. A `demoSuperadminLogin` action would close this
cheaply and is worth doing before the clinics page becomes real.
