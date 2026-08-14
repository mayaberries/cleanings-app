# pets-app Backend — Platform Notes

A FastAPI backend for veterinary clinics to manage services and
appointments, with a public, key-authenticated booking surface designed to
be embedded as a widget on any clinic's own website — no login required for
the end user.

Service categories are veterinary (`wellness_exam`, `vaccination`,
`microchipping`, `nail_trim`, `bloodwork`, `imaging`, `lab_testing`,
`sick_visit`, `dental_cleaning`, `spay_neuter`, `surgery`, `wound_care`,
`grooming`, `boarding`, `end_of_life`).

**Not every part of the app is at the same level of polish yet** — when
something looks inconsistent between layers, it's very likely a part that
hasn't been touched in the current refactor pass, rather than intentional.

## Tech stack

- **Framework:** FastAPI
- **DB:** PostgreSQL, accessed via `databases` (async) + `asyncpg` driver
- **Migrations:** Alembic
- **Validation/serialization:** Pydantic v2
- **Auth:** JWT
- **Rate limiting:** `limits`, in-memory by default, Redis-backed once
  `REDIS_URL` is set (needed once the app runs with more than one worker)
- **Testing:** pytest + pytest-asyncio (strict mode), httpx `AsyncClient`
  against the ASGI app directly (no live server needed for tests)
- **Admin CLI:** Typer + httpx (`backend/cli/`) — a thin HTTP client of
  this same API, used for cross-tenant platform operations (see below)

## Architecture layering

```
routes/          → FastAPI path operations, thin, delegate to repos
dependencies/     → permission checks, path-param resolution, auth guards
db/repositories/ → all DB access, raw SQL via `databases`, one class per domain
models/          → Pydantic models: *Create / *InDB / *Public / *Update variants
db/migrations/   → Alembic revisions
cli/             → Typer admin CLI, talks to the API over HTTP only
```

Convention across the codebase: a `*Public` model layers a populated,
richer version on top of `*InDB` (e.g. `AppointmentPublic` adds a full
`user: UserPublic` and `pet: PetProfilePublic` alongside the raw `user_id`
and `pet_id`). Repos have a `populate_*` method responsible for this
hydration.

`models/` is organized by **domain scope** rather than one file per table —
`app/models/auth/`, `profiles/`, `clinics/`, `services/`, `appointments/`.
The rest of the layers above (`routes/`, `db/repositories/`,
`dependencies/`, `tests/`) haven't caught up yet and are still flat. See the
roadmap below.

**Known drift risk:** some permission checks are duplicated between the
`dependencies/` layer (stops a request before it reaches a route) and the
`db/repositories/` layer (defense-in-depth, doesn't trust the dependency
was wired correctly). When a permission rule changes, both copies need
updating — grep for the check's condition across `dependencies/` and
`db/repositories/` rather than assuming one file is authoritative.

## Three authentication surfaces

| Surface                                                                                                                                | Auth                                                  | Who uses it                                                        |
|----------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------|--------------------------------------------------------------------|
| Staff/admin API (`/clinics`, `/services`, `/pets`, `/clinic_pets`, `/clinics/{id}/availability` PUT, appointment confirm/cancel, etc.) | JWT bearer token                                      | Logged-in clinic staff/admins                                      |
| Public booking API (`/public/...`)                                                                                                     | `X-Clinic-Key` header (`pk_live_...` / `pk_test_...`) | Anonymous visitors, via a widget embedded on the clinic's own site |
| Platform-operator surface (`GET /clinics/`, and superuser bypass on the two above)                                                      | JWT bearer token, `is_superuser = true`                | The single platform superuser, mainly via the admin CLI            |

The public key is a publishable-style credential (Stripe-`pk_`-style) — safe
to ship in client-side JS. It's scoped to one clinic, rate-limited
independently per key and per IP, and revocable without touching any other
key the clinic holds.

## Domain entities, as they stand today

### Users

Roles include `client`, `clinic_admin`, and `clinic_aux` staff, plus an
`is_guest` flag for accounts auto-provisioned by the public booking flow
(no login path ever accepts credentials for these — they exist purely to
anchor a guest's contact info and appointment history). Auth via JWT,
profiles are a separate 1:1 entity from the user record.

`is_superuser` is a separate, orthogonal flag — a platform-operator role,
not a `role` enum value. It bypasses the "only this clinic's own admin"
scoping on clinic modification and API-key management, and is required for
`GET /clinics/` (list all clinics). Enforced as **at most one** superuser
at the DB level (`ix_users_single_superuser`, a partial unique index on
`is_superuser = true`) — see Admin CLI below for how it's created. There's
no self-service HTTP path to grant it to a second account; that's
deliberate for now (see roadmap).

### Clinics

The tenant/organization boundary — almost everything else (services, staff,
pets-via-owners, appointments, availability, API keys) is scoped to a
clinic. A clinic has a weekly recurring hours schedule (`clinic_availability`
— JSONB blob per weekday + timezone, readable unauthenticated so a widget
can pull it directly).

Each clinic also has a `slug` — a stable, URL/folder-safe identifier
distinct from its UUID `id`, used by the static-site generator
(`frontend/scripts/generate-site.mjs`) as the output folder name and future
subdomain/path segment. Defaults to a slugified `name` at creation, settable
explicitly, immutable after creation (changing it would orphan an
already-built static site).

### Clinic API keys

Publishable-style keys (`pk_live_...` / `pk_test_...`) a clinic admin (or
the platform superuser, on any clinic) issues to authenticate the public
booking surface. A clinic can hold several at once so a leaked or rotated
key can be revoked with zero embed downtime.
**Known gap:** `live` vs `test` is currently cosmetic only — both write to
the same real data, no isolation yet (see roadmap).

### Owner profiles & pets

Pet owners aren't necessarily registered users — `clinic_owner_profiles` is
a pivot linking an owner profile to a clinic (with `status: active/blocked`),
and this is what the public booking flow uses to attach a guest to a clinic
without ever requiring them to sign up. Pets belong to an owner profile, not
directly to a user, and can be created either by clinic staff
(`/clinic_pets`) or on the fly during a public booking (either link an
existing pet by id, or create a new one inline).

### Services

Represents something the clinic offers (a wellness exam, a dental cleaning,
etc.), owned by a clinic staff member/admin. Has `duration_minutes`, which
appointments use to compute their `end_time`.

### Appointments

The core scheduling entity.

- Surrogate `id` (UUID) primary key — a client can book the same service
  multiple times independently.
- Real scheduling: `start_time` + `end_time` (end computed from
  `service.duration_minutes`, defaulting to 30 minutes if unset).
- Every appointment carries a `pet_id` — not just a user — so it's possible
  to know which animal a booking is for.
- Status lifecycle: `requested → confirmed / declined`,
  `confirmed → cancelled / completed`.
- Confirming an appointment checks for overlapping *confirmed* appointments
  across all of that provider's services — a provider can't be double-booked
  regardless of which service type the two bookings are for. Public
  bookings land as `requested`, so two guests *can* both successfully
  request the same slot; only confirming one resolves it — worth treating
  as an explicit product decision (manual review at low volume) rather than
  a bug.
- Confirming one appointment does **not** auto-decline other pending
  requests for the same service.
- Routes are id-based: `/services/{service_id}/appointments/{appointment_id}`,
  with `/confirm`, `/cancel` sub-actions and `DELETE` for withdrawal.

### Evaluations

A rating/review left by the service owner (clinic) about the client/pet
after a completed appointment.

- 1:1 with a specific **appointment** (`appointment_id` is the primary key).
- `service_id` / `cleaner_id` are still stored as columns for aggregate
  stats queries (total evaluations, star breakdowns, average ratings) but
  are no longer identity.
- Routes nested under the appointment:
  `/services/{service_id}/appointments/{appointment_id}/evaluation`.
- Separately, `/users/{username}/evaluations` (list) and
  `/users/{username}/evaluations/stats` (aggregate) remain keyed by
  username.
- Leaving an evaluation is what currently triggers marking the appointment
  `completed` — there's no independent completion trigger yet (flagged as
  an open gap).

### Feed

A combined activity feed across services (created/updated). Its future is
undecided as scheduling and notifications take priority — currently skipped
in tests.

### Profiles

1:1 with users, holds display info (name, phone, bio, image).

## Test suite structure

Tests live in subpackages by domain (`tests/appointments/test_create.py`,
`test_accept.py`, `test_cancel.py`, etc.), same for evaluations, pets, and
public booking. Fixtures live in `tests/_fixtures/`.

**Known limitation:** the test DB is not reset between tests (migrations are
session-scoped, users aren't recreated if they already exist by email). This
can cause flaky failures when two tests' appointment fixtures land in
overlapping time windows for the same provider — mitigated for now with
wide randomized fixture time windows, but the real fix (per-test transaction
rollback) hasn't been built yet.

---

## Getting it running

```bash
cp .env.template .env   # fill in SECRET_KEY, POSTGRES_*
pip install -r requirements.txt
alembic upgrade head
make run                 # or: uvicorn app.api.server:app --reload
```

Interactive docs land at `/docs` once the server is up. See the root
`Makefile` for the full set of `db-*`, `tests`, and dependency-management
targets.

## Usage: minimal booking flow

**1. As clinic staff — create a clinic, then a public key:**

```bash
curl -X POST /api/clinics/ -H "Authorization: Bearer <jwt>" \
  -d '{"name": "Acme Vet", "email": "hi@acmevet.com"}'

curl -X POST /api/clinics/{clinic_id}/api-keys/ -H "Authorization: Bearer <jwt>" \
  -d '{"label": "Website widget", "environment": "live"}'
# -> returns pk_live_...
```

**2. From the embedded widget — list services with the public key:**

```bash
curl /api/public/services -H "X-Clinic-Key: pk_live_..."
```

**3. Book an appointment** (creates the pet + registers the owner with the
clinic automatically):

```bash
curl -X POST /api/public/appointments -H "X-Clinic-Key: pk_live_..." \
  -d '{
    "email": "owner@example.com",
    "full_name": "Jane Owner",
    "phone_number": "+52...",
    "service_id": "...",
    "pet": {"new_pet": {"name": "Rex", "species": "dog"}},
    "start_time": "2026-09-01T15:00:00Z"
  }'
```

A `409` means the slot conflicts with an existing *confirmed* appointment —
the widget should prompt for another time. New bookings land as
`requested`; staff confirm or decline via the JWT-authed
`/services/{id}/appointments/{id}/confirm` / `/cancel` routes.

**4. Returning visitors** can be shown their existing pets instead of
re-entering them: `GET /api/public/pets?email=owner@example.com` (same key).

---

## Admin CLI (`backend/cli/`)

A Typer CLI that's a pure HTTP client of this same API — no direct DB
access, so it works unmodified against local, staging, or production
deployments. It exists for two things the JWT staff API alone doesn't
cover: cross-tenant platform operations (listing/creating clinics as a
superuser) and driving the static-site generator
(`frontend/scripts/generate-site.mjs`) from real clinic data instead of
hand-typed flags.

```bash
pip install -r requirements-cli.txt   # separate from requirements.txt on
                                       # purpose — the API server itself
                                       # never imports from cli/
```

All commands are run from `backend/` so `cli` resolves as a package:
`python -m cli.main <command>`.

### One-time setup: the platform superuser

```bash
python -m cli.main bootstrap
# prompts for API base URL (defaults to http://localhost:8000/api),
# email, username, password
# → creates the one platform superuser and logs the CLI in as them
```

Enforced as a true one-time action — `ix_users_single_superuser` (a
partial unique index) guarantees at most one row can have
`is_superuser = true`, and the bootstrap endpoint 403s cleanly on every
call after the first. There's currently no self-service way to add a
*second* superuser or transfer the role; `scripts/promote_superuser.py`
exists for that but talks to the DB directly and isn't gated the same way
— treat it as a manual, trusted-operator-only tool, not a supported flow.

### Everyday session

```bash
python -m cli.main login     # any existing user; superuser-only commands
                              # will 403 if this account isn't one
python -m cli.main whoami
python -m cli.main logout
```

Session (API base URL + JWT) is stored in `~/.config/pets-admin-cli/credentials.json`.

### Clinics

```bash
python -m cli.main clinics list
python -m cli.main clinics create "Acme Vet" --phone "555-0100"
# links the new clinic to whoever's logged in, same as the normal
# clinic_admin signup flow — works once per user, since a user can only
# belong to one clinic (clinic_id must be null going in)

python -m cli.main clinics create-key <clinic_id> --label "Website widget"
python -m cli.main clinics keys <clinic_id>
```

### Static sites

```bash
python -m cli.main sites generate <clinic_id> --public-api-url https://api.yourdomain.com/api
# resolves the clinic's slug + most recent active live key from the
# backend, then drives `astro build` → frontend/sites/<slug>/

python -m cli.main sites generate-all --public-api-url https://api.yourdomain.com/api
# walks every clinic (GET /clinics/); needed after any change to
# frontend/template/, since config is baked in at build time and nothing
# rebuilds itself automatically
```

Output is a plain static folder per clinic — deploy anywhere, or serve
straight from FastAPI's `StaticFiles` for the simplest possible setup.
See `frontend/README_STATIC_SITES.md` for the generator mechanism itself.

---

## Roadmap

### ✅ Ready for solo usage (own clinic, own embedded widget)

- Clinic + staff account creation, JWT auth
- Public API key issuance/revocation, scoped rate limiting
- `GET /public/services` — list bookable services with a public key
- `GET /public/pets?email=` — guest pet lookup, no duplicate pets on repeat visits
- `POST /public/appointments` — books an appointment **with pet + owner + service + time** in one call; auto-creates the
  guest owner, auto-registers them with the clinic, auto-creates or links the pet
- Conflict detection against confirmed appointments (`409` on overlap)
- Full staff-side lifecycle: list / get / confirm / cancel / withdraw appointments
- Weekly clinic hours (`clinic_availability`) — `GET` is unauthenticated, so a widget can read hours directly using the
  clinic's own known `clinic_id`
- Platform superuser bootstrap (single, DB-enforced) + `GET /clinics/` — a way to see/manage clinics across tenants
- Admin CLI (`backend/cli/`) — bootstrap, clinic + key creation, static-site generation, all as one HTTP client
- Static-site generation mechanism (`frontend/`) — Astro template + build-time config injection per clinic

### 🔧 Left for refinement (not blocking solo use, needed before wider/third-party use)

- **No computed availability/slot endpoint.** Clinic hours are readable, but nothing combines hours + existing bookings
  into an actual open-slots list reachable via the public key. Widgets must offer times within business hours and handle
  `409` reactively rather than graying out taken slots proactively.
- **`pk_live_` / `pk_test_` behave identically.** Test-key traffic writes real data with no isolation — needs either
  environment-tagged data or environment-restricted deploys before handing a test key to anyone else.
- **No guest self-service.** Once booked, a guest has no way to view, cancel, or reschedule their own appointment
  without contacting the clinic directly.
- **No clinic metadata on the public surface** (name, timezone) reachable via the key itself — currently assumes the
  integrator already knows the clinic's `clinic_id` and timezone.
- **No idempotency protection** on `POST /public/appointments` — a double-submit/retry can create duplicate guest
  bookings.
- **Public bookings start as `requested`, not `confirmed`.** Two guests can request the same slot; only the check on
  *confirm* actually blocks a double-booking. Fine as a manual-review flow at low volume, but should be an explicit
  product decision before scaling traffic.
- **Evaluation completion trigger.** Marking an appointment `completed` currently only happens as a side effect of
  leaving an evaluation — no independent "mark completed" action exists yet.
- **Test DB isolation.** No per-test transaction rollback yet; current mitigation is randomized fixture time windows,
  which is a workaround, not a fix.
- **Single-superuser only.** `ix_users_single_superuser` enforces exactly one for now; a real multi-operator flow
  (invite/promote a second superuser over HTTP, with its own audit trail) hasn't been designed.
- **Superuser can only create one clinic.** `create_clinic_for_admin` still requires `clinic_id is None` going in and
  attaches the new clinic to the requesting user either way — fine for solo/bootstrap use, but blocks a superuser from
  provisioning several clinics on other people's behalf without a dedicated "create + assign owner" path.
- **Permission-check duplication between `dependencies/` and `db/repositories/`.** Confirmed drift once already
  (`create_key_for_clinic` / `revoke_key` in `ClinicAPIKeysRepository` had their own stale copy of the admin check
  after the dependency layer was updated) — worth an audit pass rather than fixing instances as they're hit.
- **What triggers `sites generate` in practice.** Currently a person running the CLI by hand after creating a clinic +
  issuing its key. An automatic trigger (e.g. on key creation) is a reasonable next step once the manual flow feels solid.

### 🧹 Refactor: reorganize by scope (routes, repositories, dependencies, tests)

`models/` is already split by domain (`auth/`, `profiles/`, `clinics/`,
`services/`, `appointments/`) instead of one file per table. The rest of the
app is still flat and has grown past the point where that's comfortable.
Next pass: apply the same domain-scoped grouping to:

- `app/api/routes/` — group by scope (e.g. `clinics/`, `appointments/`, `public_booking/`), not necessarily 1:1 with a
  single table, mirroring how `public_booking.py` already spans services + pets + appointments + owners in one file
- `app/db/repositories/`
- `app/api/dependencies/`
- `tests/`

Same principle as the models split: group by the domain/scope a piece of
logic serves, regardless of whether that scope maps to one table, several,
or a slice of one — not by mechanical 1:1 file-per-model mapping.
