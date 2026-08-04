# Notifications: A Possible Future Direction (Feed → Event Log)

> **Status:** speculative, not scoped, not scheduled. This is a design note
> to save the reasoning for later, not something to build now. Written when
> we decided to skip (not delete) the old marketplace Feed feature pending a
> decision — see `appointments-evaluations-roadmap.md`.

## The idea in one sentence

The old Feed's *shape* — an append-only log of timestamped, typed events —
is a reasonable foundation for email/WhatsApp notifications, even though its
*content* (service create/update events, for public browsing) doesn't fit
the platform anymore.

## Why the old Feed doesn't transfer directly

Old Feed answered: "what services were recently posted or changed, that I
might want to browse?" That's a marketplace-discovery question. Nothing in
the scheduling-first, low-disruption direction has a browsing journey — a
pet owner books a known service at a known clinic, they don't scroll a feed
of new listings. So the *audience* (public, browsing) and the *subject*
(services) are both wrong for where the product is going.

## What would actually be useful instead

An internal, append-only log of **appointment lifecycle events**, used to
drive outbound notifications rather than a browsable page:

| Event | Likely notification |
|---|---|
| Appointment requested | Email/WhatsApp to clinic staff |
| Appointment confirmed | Email/WhatsApp to client |
| Appointment declined | Email/WhatsApp to client |
| Appointment cancelled (by client) | Email/WhatsApp to clinic |
| Appointment cancelled (by clinic, if ever added) | Email/WhatsApp to client |
| Appointment completed | Maybe nothing, or a "how was your visit" prompt |
| Evaluation left | Maybe nothing, or an internal digest for clinic staff |
| Appointment reminder (T-24h, T-1h) | Email/WhatsApp to client — **not** a status transition, would need a scheduled job, not just an event hook |

The first six rows are naturally covered by hooking into the *existing*
appointment status transitions (`requested → confirmed`, `→ declined`,
`→ cancelled`, `→ completed`) — no new event-sourcing infrastructure needed,
just a dispatch step wherever those transitions already happen in
`AppointmentsRepository`. The reminder row is different in kind: it isn't
triggered by a state change at all, it's triggered by the *passage of time*
relative to `start_time`, which means it needs a scheduled job/worker, not
just an event hook. Worth keeping that distinction in mind so "notifications"
doesn't get scoped as one uniform mechanism when it's really two.

## Rough shape, if/when this gets built

Not a spec — just enough to remember the shape of the idea:

- A `notification_events` table (or similar): `id`, `appointment_id`,
  `event_type` (`requested` / `confirmed` / `declined` / `cancelled` /
  `completed`), `created_at`. Append-only, one row per transition.
- A dispatcher (could be as simple as a function called at the same call
  sites where `AppointmentsRepository` already changes status — no new
  triggers needed) that reads the event type and fires the right
  email/WhatsApp send.
- Channel abstraction (email vs. WhatsApp) kept separate from the event log
  itself, so adding a channel later doesn't touch the event model.
- Reminders (time-based, not event-based) would need their own scheduled job
  querying `appointments` for `start_time` within a lookahead window and
  `status = confirmed` — separate from the event-log mechanism above.

## What NOT to do

Don't resurrect the old Feed code (routes, pagination, service-scoped
queries) as a starting point — it's built around the wrong entity (services)
and the wrong audience (public/browsable) and would need to be rewritten
past recognition anyway. Start fresh from the appointment status
transitions when this becomes a real priority.