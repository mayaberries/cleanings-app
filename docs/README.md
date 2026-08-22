# Documentation

Everything about how this project works lives here. The root
[`README.md`](../README.md) is deliberately just "clone it and get it running";
anything beyond that is below.

## Start here

| Doc | What it answers |
|---|---|
| [architecture.md](architecture.md) | How the pieces fit — the three deployables, the three auth surfaces, backend layering and its conventions |
| [domain.md](domain.md) | What the entities are: clinics, users, keys, pets, services, appointments, evaluations |
| [development.md](development.md) | Setup, `make` targets, dev servers, and the gotchas that cost time |
| [testing.md](testing.md) | Both suites, how to run them, and what the skipped specs mean |
| [roadmap.md](roadmap.md) | What's done, what's blocked on a decision, what's a known gap |

## Per-component

| Doc | Covers |
|---|---|
| [admin-dashboard.md](admin-dashboard.md) | `frontend/admin/` — Astro SSR, session auth, role gate, nanostores rules, demo mode, onboarding wizard |
| [static-sites.md](static-sites.md) | `frontend/template/` → `frontend/sites/` — the per-clinic static site generator |
| [admin-cli.md](admin-cli.md) | `backend/cli/` — the Typer CLI for cross-tenant operations and site builds |

## Reference & notes

- [`openapi.json`](openapi.json) — the backend's API schema. The source of truth
  for endpoint shapes; the `tests/wip/` specs are written against it.
- [`proto/`](proto/README.md) — a static, no-build prototype of the admin
  dashboard, one page per tab. The design target for tabs that aren't built yet.
  `dashboard.html` is its older single-file ancestor, kept for comparison.
- [`notes/notifications-feed.md`](notes/notifications-feed.md) — speculative
  design note on reusing the dormant Feed's shape for notifications.

## If you only read three things

1. **[The nanostores/SSR rule](admin-dashboard.md#nanostores-never-set-from-server-code)** —
   module state is shared across concurrent requests; getting this wrong leaks
   one user's session into another's page.
2. **[Duplicated permission checks](architecture.md#known-drift-risk-duplicated-permission-checks)** —
   permission rules live in two layers on purpose, and have drifted before.
3. **[The test DB isn't reset between tests](testing.md#backend-backendtests)** —
   intermittent appointment-conflict failures are usually this, not your change.
