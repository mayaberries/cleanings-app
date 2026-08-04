# pets-app Backend — Platform Notes

> This README documents what we currently know about the platform based on
> work done so far. It's a living snapshot, not a spec — update it as the
> domain model keeps evolving.

## What this actually is

The codebase started life as a gig-marketplace tutorial project ("cleanings
app" — clients post cleaning jobs, cleaners bid to take them). It's actively
being refactored into a **veterinary clinic appointment-scheduling platform**.
Evidence of the transition is all over the codebase: the DB container is
still named `fastapi-pets-db`, service categories are veterinary
(`wellness_exam`, `vaccination`, `microchipping`, `nail_trim`, `bloodwork`,
`imaging`, `lab_testing`, `sick_visit`, `dental_cleaning`, `spay_neuter`,
`surgery`, `wound_care`, `grooming`, `boarding`, `end_of_life`), and several
tables/variables still carry the old `cleaner_id` / "offer" language from the
original marketplace model.

**Not every part of the app has caught up to the new domain yet** — that's
the main thing to keep in mind reading this codebase. When something looks
inconsistent, it's very likely mid-migration rather than intentional.

## Tech stack

- **Framework:** FastAPI
- **DB:** PostgreSQL, accessed via `databases` (async) + `asyncpg` driver
- **Migrations:** Alembic
- **Validation/serialization:** Pydantic v2
- **Auth:** JWT (`phresh:auth` audience — another naming leftover from the
  original tutorial project, "phresh" was its original name)
- **Testing:** pytest + pytest-asyncio (strict mode), httpx `AsyncClient`
  against the ASGI app directly (no live server needed for tests)

## Architecture layering

```
routes/          → FastAPI path operations, thin, delegate to repos
dependencies/     → permission checks, path-param resolution, auth guards
db/repositories/ → all DB access, raw SQL via `databases`, one class per domain
models/          → Pydantic models: *Create / *InDB / *Public / *Update variants
db/migrations/   → Alembic revisions
```

Convention across the codebase: a `*Public` model layers a populated,
richer version on top of `*InDB` (e.g. `AppointmentPublic` adds a full
`user: UserPublic` alongside the raw `user_id`; `ServicePublic` replaces
`owner: str` with a populated user object). Repos have a `populate_*` method
responsible for this hydration.

## Domain entities, as they stand today

### Users
Roles include `client` and `clinic_admin` (and likely more — worth
confirming the full `UserRole` enum). Auth via JWT, profiles are a separate
1:1 entity from the user record.

### Services
Represents something the clinic offers (a wellness exam, a dental cleaning,
etc.), owned by a clinic staff member/admin. Has `duration_minutes`, which
appointments now use to compute their `end_time`.

**Open question, not yet fully resolved:** originally a `Service` was a
single one-off job (like a cleaning job posting) — one appointment, ever.
We've moved appointments off that model (see below), but it's worth
double-checking `services.py` routes/repo don't still carry one-off-job
assumptions anywhere we haven't touched yet.

### Appointments
The core entity we've done the most work on. As of the latest refactor:

- Surrogate `id` (UUID) primary key — **not** `(user_id, service_id)` anymore,
  so a client can book the same service multiple times independently.
- Real scheduling: `start_time` + `end_time` (end computed from
  `service.duration_minutes`, defaulting to 30 minutes if unset).
- Status lifecycle: `requested → confirmed / declined`,
  `confirmed → cancelled / completed`. Canonical vocabulary is
  `requested/confirmed/declined/cancelled/completed` — an earlier
  `pending/accepted/rejected` vocabulary existed in older tests and has been
  retired.
- Confirming an appointment checks for overlapping *confirmed* appointments
  across all of that provider's services (not just the one being confirmed) —
  a provider can't be double-booked regardless of which service type the two
  bookings are for.
- Confirming one appointment does **not** auto-decline other pending requests
  for the same service anymore (that was leftover bidding-marketplace
  behavior from the original cleanings-app model).
- Routes are id-based: `/services/{service_id}/appointments/{appointment_id}`,
  with `/confirm`, `/cancel` sub-actions and `DELETE` for withdrawal.

### Evaluations
A rating/review left by the service owner (clinic) about the client/pet
after a completed appointment.

- Rekeyed to be 1:1 with a specific **appointment** (`appointment_id` is now
  the primary key), not `(service_id, cleaner_id)` — necessary once a client
  can have multiple independent appointments for the same service; the old
  keying made it ambiguous which visit an evaluation was rating.
- `service_id` / `cleaner_id` are still stored as columns (for aggregate
  stats queries — total evaluations, star breakdowns, average ratings per
  cleaner) but are no longer identity.
- Routes nested under the appointment:
  `/services/{service_id}/appointments/{appointment_id}/evaluation`.
- Separately, `/users/{username}/evaluations` (list) and
  `/users/{username}/evaluations/stats` (aggregate) remain keyed by cleaner
  username — those weren't affected by the rekey, since they're inherently
  about "all of a cleaner's evaluations," not a single one.
- Leaving an evaluation is what currently triggers marking the appointment
  `completed` — there's no independent completion trigger yet (flagged as an
  open gap; see roadmap).

### Feed
A combined activity feed across services (created/updated). Untouched by the
appointments/evaluations refactor so far.

### Profiles
1:1 with users, holds display info (name, phone, bio, image). Untouched by
recent work.

## Naming quirks to know about (mostly historical, not yet cleaned up)

- `cleaner_id` / "cleaner" — leftover from the original cleaning-marketplace
  domain, now really means "the client/pet owner in the appointment," not a
  service provider. Confusing on first read.
- "offer" — appointments were originally called "offers" (as in, a cleaner's
  bid to take a job). Some old test names, route dependency names, and error
  messages still use "offer" language even though the model underneath is
  now "appointment."
- `phresh:auth` JWT audience — cosmetic leftover from the tutorial project's
  original name, functionally harmless.

## Test suite structure

Tests were recently restructured from flat per-domain files
(`tests/test_appointments.py`) into subpackages
(`tests/appointments/test_create.py`, `test_accept.py`, `test_cancel.py`,
`test_get.py`, `test_rescind.py`, `test_routing.py`, etc.), same for
evaluations. Fixtures live in `tests/_fixtures/`.

**Known limitation:** the test DB is not reset between tests (migrations are
session-scoped, users aren't recreated if they already exist by email). This
previously caused flaky failures when two tests' appointment fixtures landed
in overlapping time windows for the same provider — mitigated for now with
wide randomized fixture time windows, but the real fix (per-test transaction
rollback) hasn't been built yet. See the roadmap for details.

## Where to look next

See `appointments-evaluations-roadmap.md` for the categorized checklist of
what's done, what's cheap-and-pending, what needs a product decision, and
what's been explicitly punted for later.