# Roadmap

Merged from the old root README roadmap and `roadmap/appointments.md`. Grouped by
what the gap actually blocks, not by layer.

## ✅ Ready for solo usage (own clinic, own embedded widget)

- Clinic + staff account creation, JWT auth
- Public API key issuance/revocation, scoped rate limiting
- `GET /public/services` — list bookable services with a public key
- `GET /public/pets?email=` — guest pet lookup, no duplicate pets on repeat visits
- `POST /public/appointments` — books pet + owner + service + time in one call;
  auto-creates the guest owner, auto-registers them with the clinic, auto-creates
  or links the pet
- Conflict detection against confirmed appointments (`409` on overlap)
- Full staff-side lifecycle: list / get / confirm / cancel / withdraw
- Weekly clinic hours (`clinic_availability`), `GET` unauthenticated so a widget
  can read hours directly
- Platform superuser bootstrap (single, DB-enforced) + `GET /clinics/`
- Admin CLI — bootstrap, clinic + key creation, static-site generation
- Static-site generation — Astro template + build-time config injection per clinic
- Admin dashboard — session auth, onboarding wizard, tab routing + role gate

### Appointments & evaluations, specifically

- Real scheduling (`start_time`/`end_time` from `service.duration_minutes`)
- Surrogate `id` PK — the same service can be booked repeatedly
- Full lifecycle, with overlap checking across all of a provider's services
- Confirming one appointment no longer auto-declines other pending requests
- Permission checks rewritten around appointment ownership, not
  `(service_id, username)`
- Conflict check on **creation**, not just confirmation
- `start_time` in the past is rejected
- Evaluations rekeyed by `appointment_id`, routes nested under the appointment
- `cleaner_id`/`service_id` kept as columns for aggregate stats, no longer identity
- Old `offers_repo` / "offer" naming cleaned up to `appointments_repo`

## 🔴 Product decisions needed before building

These are blocked on a decision, not on effort.

- **Cancellation policy.** No lead-time minimum, and no distinction between
  cancelling with 2 minutes' notice and 2 weeks'. The rule needs deciding before
  the check can be written.
- **Completion trigger.** `mark_as_completed` only fires when someone leaves an
  evaluation, so a confirmed appointment nobody rates stays `confirmed` forever,
  even long past `end_time`. Options: a scheduled sweep of past-due confirmed
  appointments; a lazy transition on read; or an explicit "mark complete"
  endpoint decoupled from evaluation.
- **No-show / unevaluated completions.** No path exists to close out an
  appointment that happened but was never rated. Depends on the decision above.
- **Public bookings start as `requested`, not `confirmed`.** Two guests can
  request the same slot; only the check on *confirm* blocks a real double-booking.
  Fine as manual review at low volume, but it should be an explicit product
  decision before scaling traffic.

## 🔧 Refinement (not blocking solo use; needed before wider/third-party use)

- **No computed availability/slot endpoint.** Clinic hours are readable, but
  nothing combines hours + existing bookings into an open-slots list reachable
  via the public key. Widgets must offer times within business hours and handle
  `409` reactively instead of graying out taken slots.
- **`pk_live_` / `pk_test_` behave identically.** Test-key traffic writes real
  data with no isolation. Needs environment-tagged data or environment-restricted
  deploys before a test key goes to anyone else.
- **No guest self-service.** Once booked, a guest can't view, cancel, or
  reschedule without contacting the clinic.
- **No clinic metadata on the public surface** (name, timezone) reachable via the
  key itself — currently assumes the integrator already knows the `clinic_id` and
  timezone.
- **No idempotency protection** on `POST /public/appointments` — a double-submit
  or retry can create duplicate guest bookings.
- **Test DB isolation.** No per-test transaction rollback; randomized fixture time
  windows are a workaround. See [testing.md](testing.md).
- **Single-superuser only.** `ix_users_single_superuser` enforces exactly one. A
  real multi-operator flow (invite/promote over HTTP, with an audit trail) hasn't
  been designed.
- **Superuser can only create one clinic.** `create_clinic_for_admin` still
  requires `clinic_id is None` and attaches the new clinic to the requesting user.
  Fine for bootstrap, but blocks provisioning clinics on other people's behalf
  without a dedicated "create + assign owner" path.
- **Permission-check duplication** between `dependencies/` and `repositories/` —
  confirmed drift once already. Worth an audit pass rather than fixing instances
  as they're hit. See [architecture.md](architecture.md#known-drift-risk-duplicated-permission-checks).
- **What triggers `sites generate` in practice.** Currently a person running the
  CLI by hand. An automatic trigger (e.g. on key creation) is a reasonable next
  step once the manual flow feels solid.
- **Provider working hours vs. overlap checking.** Overlap checks only prevent
  double-booking against *other confirmed appointments*. "Available" currently
  means "not already booked" — there's no concept of business hours or blocked-off
  time in the check itself.
- **Evaluations migration backfill.** The `appointment_id` NOT NULL/PK swap
  assumes no pre-existing rows. Fine on a fresh dev DB; needs a real backfill
  strategy before running against populated data.

## 🖥 Admin dashboard

- Most tabs are route stubs. Acceptance criteria already exist as skipped specs
  in `frontend/admin/tests/wip/` — see [testing.md](testing.md) for how to
  graduate one.
- No demo superadmin, so the superadmin half of the role gate is untested.
- Design tokens are maintained in three places; `frontend/shared/design-tokens.mjs`
  no longer lives up to its "single source of truth" comment. See
  [admin-dashboard.md](admin-dashboard.md#styling-and-design-tokens).
- `/settings/clinic`, `/settings/staff`, `/settings/hours` are referenced by wip
  specs but have no route or nav entry yet.

## 🧹 Refactor: reorganize by domain scope

`models/`, `routes/`, and `tests/` are **already** grouped by domain. Still flat:

- `app/db/repositories/`
- `app/api/dependencies/`

Same principle as the models split: group by the domain a piece of logic serves,
regardless of whether that scope maps to one table, several, or a slice of one —
not a mechanical file-per-model mapping.

## 💭 Speculative

- [notes/notifications-feed.md](notes/notifications-feed.md) — reusing the
  dormant Feed's append-only-log *shape* for appointment notifications. A design
  note, not scoped or scheduled.
