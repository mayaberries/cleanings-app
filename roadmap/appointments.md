# Appointments + Evaluations — MVP Roadmap

## ✅ Done

### Appointments
- [x] Appointments carry real scheduling (`start_time` / `end_time`), derived from `service.duration_minutes`
- [x] Surrogate `id` primary key — a client can book the same service multiple times independently
- [x] Full lifecycle: `requested → confirmed / declined`, `confirmed → cancelled / completed`
- [x] Confirming an appointment checks for overlapping *confirmed* appointments across the provider's other services
- [x] Confirming one appointment no longer auto-declines other pending requests for the same service
- [x] Routes moved to `id`-based identity (`/services/{service_id}/appointments/{appointment_id}`)
- [x] Cancel / withdraw / confirm permission checks rewritten around appointment ownership, not `(service_id, username)`
- [x] `populate_appointment` bug fixed (was dropping required `user_id`)
- [x] `service.owner` type ambiguity (`UserPublic` vs. raw id string) fixed at the one call site that broke on it

### Evaluations
- [x] Evaluations rekeyed by `appointment_id` (1:1 with a specific completed visit) instead of `(service_id, cleaner_id)`
- [x] Routes nested under the appointment (`/services/{service_id}/appointments/{appointment_id}/evaluation`)
- [x] `cleaner_id` / `service_id` kept as columns for aggregate-stats queries, no longer used as identity
- [x] `mark_as_completed` call signature fixed to match the new appointment-based repo
- [x] Old `offers_repo` / "offer" naming cleaned up to `appointments_repo`

### Testing
- [x] Full suite green across appointments, evaluations, and everything else
- [x] Fixtures updated for scheduled appointments and appointment-keyed evaluations
- [x] Diagnosed and patched test-flakiness from fixture time-window collisions (random wide windows instead of a fixed `+1 day` offset)

---

## 🟡 To Do — cheap, mechanical, worth doing before calling this MVP-complete

- [ ] **Real test isolation.** Current fix is statistical (wide random time windows), not structural. Wrap each test in a DB transaction that rolls back at teardown so tests can't see each other's leftover data at all.
- [ ] **Conflict check on appointment *creation***, not just confirmation. Right now a client can request unlimited overlapping appointments with the same provider — only confirmation is guarded. Decide: block overlapping requests outright, or let requests pile up and rely on the owner to naturally reject/ignore overlaps at confirm time?
- [ ] **Reject `start_time` in the past.** `AppointmentCreate` currently has no validation against `now()`.

---

## 🔴 To Do — product decisions needed before building

- [ ] **Cancellation policy.** No lead-time minimum, no distinction between cancelling with 2 minutes' notice vs. 2 weeks'. Need a decision on what's acceptable before writing the check.
- [ ] **Completion trigger.** `mark_as_completed` currently only fires when someone leaves an evaluation — a confirmed appointment with no evaluation sits in `confirmed` forever, even after `end_time` passes. Options:
  - scheduled job that sweeps past-due confirmed appointments
  - lazy transition on read (mark completed if `end_time` has passed, whenever it's fetched)
  - explicit "mark complete" endpoint, decoupled from evaluation
- [ ] **No-show / unevaluated completions.** No path currently exists to close out an appointment that happened but was never rated — depends on the completion-trigger decision above.

---

## ⚪ Explicitly punted (fine to leave as known gaps, not MVP blockers)

- [ ] **Provider availability / working hours.** Overlap-checking only prevents double-booking against *other confirmed appointments* — there's no concept of business hours or blocked-off time. "Available" currently just means "not already booked."
- [ ] **Evaluations migration backfill note.** The `appointment_id` NOT NULL/PK swap assumes no pre-existing rows. Fine for a fresh dev DB; would need a real backfill strategy before running against populated data.