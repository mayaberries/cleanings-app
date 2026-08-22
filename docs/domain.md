# Domain model

What the entities are and how they relate, as they stand today. For the
layering that holds them, see [architecture.md](architecture.md); for the gaps
called out below, see [roadmap.md](roadmap.md).

## Clinics — the tenant boundary

Almost everything else is scoped to a clinic: services, staff, pets-via-owners,
appointments, availability, API keys.

A clinic has a weekly recurring hours schedule (`clinic_availability` — a JSONB
blob per weekday plus a timezone). **`GET` on it is unauthenticated on purpose**,
so an embedded widget can pull hours directly.

Each clinic also has a **`slug`**: a stable, URL/folder-safe identifier distinct
from its UUID `id`. It's the output folder name for the static-site generator and
the future subdomain/path segment. Defaults to a slugified `name`, can be set
explicitly at creation, and is **immutable afterwards** — changing it would
orphan an already-built static site.

## Users

Roles: `client`, `clinic_admin`, `clinic_aux` (staff). Plus:

- **`is_guest`** — accounts auto-provisioned by the public booking flow. No login
  path ever accepts credentials for these; they exist purely to anchor a guest's
  contact info and appointment history.
- **`is_superuser`** — a separate, orthogonal platform-operator flag, *not* a
  `role` value. Bypasses per-clinic scoping on clinic modification and API-key
  management, and is required for `GET /clinics/`. The DB enforces **at most one**
  (`ix_users_single_superuser`). See [admin-cli.md](admin-cli.md) for how it's
  created; there is deliberately no self-service HTTP path to grant it to a
  second account.

Auth is JWT. Profiles are a separate 1:1 entity from the user record.

## Clinic API keys

Publishable-style keys (`pk_live_…` / `pk_test_…`) that a clinic admin — or the
superuser, on any clinic — issues to authenticate the public booking surface. A
clinic can hold several at once, so a leaked or rotated key can be revoked with
zero embed downtime.

> **Known gap:** `live` vs `test` is currently **cosmetic only**. Both write to
> the same real data with no isolation. Don't hand a test key to a third party
> expecting a sandbox.

## Owner profiles & pets

Pet owners aren't necessarily registered users. `clinic_owner_profiles` is a
pivot linking an owner profile to a clinic (with `status: active/blocked`), and
it's what lets the public booking flow attach a guest to a clinic without ever
requiring signup.

Pets belong to an **owner profile**, not directly to a user. They can be created
by clinic staff (`/clinic_pets`) or on the fly during a public booking — either
linking an existing pet by id, or creating a new one inline.

## Services

Something the clinic offers, owned by a clinic staff member/admin. Carries
`duration_minutes`, which appointments use to compute `end_time`.

Categories are veterinary: `wellness_exam`, `vaccination`, `microchipping`,
`nail_trim`, `bloodwork`, `imaging`, `lab_testing`, `sick_visit`,
`dental_cleaning`, `spay_neuter`, `surgery`, `wound_care`, `grooming`,
`boarding`, `end_of_life`.

## Appointments — the core scheduling entity

- Surrogate UUID `id` primary key, so a client can book the same service multiple
  times independently.
- Real scheduling: `start_time` + `end_time`, where end is computed from
  `service.duration_minutes` (defaulting to 30 minutes if unset).
- Every appointment carries a **`pet_id`**, not just a user — so it's always
  known which animal a booking is for.
- Status lifecycle: `requested → confirmed / declined`, then
  `confirmed → cancelled / completed`.
- Routes are id-based: `/services/{service_id}/appointments/{appointment_id}`,
  with `/confirm` and `/cancel` sub-actions and `DELETE` for withdrawal.

### Two scheduling behaviours that look like bugs but aren't

**Double-booking is only blocked at confirm time.** Confirming checks for
overlapping *confirmed* appointments across all of that provider's services — a
provider can't be double-booked regardless of service type. But public bookings
land as `requested`, so two guests *can* both successfully request the same slot;
only confirming one resolves it. Treat this as an explicit product decision
(manual review at low volume), not a defect — though it should be revisited
before scaling traffic.

**Confirming one appointment does not auto-decline the others** for the same
service. Also deliberate.

## Evaluations

A rating/review left by the service owner (the clinic) about the client/pet after
a completed appointment.

- **1:1 with an appointment** — `appointment_id` is the primary key.
- `service_id` / `cleaner_id` are still columns, used for aggregate stats (total
  evaluations, star breakdowns, averages), but are **no longer identity**.
- Routes nest under the appointment:
  `/services/{service_id}/appointments/{appointment_id}/evaluation`.
- Separately, `/users/{username}/evaluations` and
  `/users/{username}/evaluations/stats` remain keyed by username.

> **Known gap:** leaving an evaluation is what currently marks an appointment
> `completed`. There is no independent completion trigger, so a confirmed
> appointment nobody rates stays `confirmed` forever, even long past `end_time`.

## Profiles

1:1 with users. Display info: name, phone, bio, image.

## Feed

A combined activity feed across services (created/updated). **Currently skipped
in tests and effectively dormant** — it's a leftover from the app's earlier
marketplace shape and doesn't fit the scheduling-first direction. Its future is
undecided; see [notes/notifications-feed.md](notes/notifications-feed.md) for why
it was skipped rather than deleted, and what its append-only-log *shape* might be
worth reusing for.
