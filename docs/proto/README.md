# Pets Admin — dashboard prototype

**This is a prototype, not shipped code.** A static, no-backend mockup of the
admin dashboard, split into one real page per tab. It replaces the single-file
version at `docs/dashboard.html` (still there, untouched, if you want to
compare) with the same demo broken into its granular views.

No build step, no framework, no `fetch()`. Open `login.html` directly in a
browser (double-click works, no local server required) and click through it.

## Layout

```
login.html          — entry point. "Superadmin view" / "Clinic admin view"
                       buttons (or fill in any email/password) seed fake data
                       and drop you into the right first tab.

clinics.html         — superadmin: list of clinics + per-clinic "launch site" panel
overview.html        — clinic admin: stat cards
appointments.html    — clinic admin: per-service appointment list, confirm/cancel
services.html        — clinic admin: service cards
api-keys.html        — clinic admin: create/revoke API keys
website.html         — clinic admin: their own clinic's "launch site" panel
account.html         — both roles: edit display name / email / password

shared.js            — state (sessionStorage), the login+role/tab access guard
                        ("boot"), header/nav rendering, and the site-launch
                        panel shared by clinics.html and website.html
theme-config.js       — Tailwind CDN config (colors/fonts), loaded by every page
styles.css            — badge classes + base styles, loaded by every page
```

Each `*.html` is a full, independently-openable document — good for linking
someone straight to "here's the Services tab" without them having to click
through the login screen first (as long as they seed data for the relevant
role by visiting `login.html` at some point in the same tab session).

## How it holds together with no backend

Every page loads `shared.js`, then its own `<name>.js`. On load, each view
script calls `boot("<its tab id>")`, which:

1. reads `state` out of `sessionStorage` — redirects to `login.html` if no
   one's "signed in" yet;
2. redirects to the current role's landing tab if this page doesn't belong to
   it (e.g. a clinic admin hitting `clinics.html` gets bounced to
   `overview.html`);
3. fills in the shared header/role badge/nav that's already sitting in the
   page's static markup.

`sessionStorage` (not `localStorage`) is the one deviation from
`docs/dashboard.html`'s "nothing is saved, ever" original design — it's a
consequence of splitting into real pages: a real navigation now happens
between "tabs," so state needs to survive that hop. It still clears the
moment the tab closes, so the spirit (nothing durable, resets trivially) is
unchanged — sign out (or open a new tab) for a clean slate.

## Known trade-off

Each `*.html` repeats the same ~25-line `<head>` + header/nav markup instead
of a shared layout include, because this is plain static HTML with no server
and no build step. If that duplication becomes annoying, the fix is a tiny
static-site generator (Eleventy, Vite in SSG mode, even a five-line Node
script) — not a runtime `fetch()` of partials, which breaks when a page is
opened directly via `file://`.

## Promoting a view into the real app

**The shell is already ported.** `boot()`'s role/tab access guard now lives in
`frontend/admin/src/middleware.ts` + `src/lib/nav.ts`, and `renderShell()`'s tab
bar is `src/components/AdminNav.vue`. Every tab below has a real route in the
admin app; most are still content placeholders. See
[../admin-dashboard.md](../admin-dashboard.md).

What's left to port is each tab's **body**. When one is ready to become real
(backed by the actual API — see `docs/openapi.json` and
`frontend/admin/tests/wip/`, plus [../testing.md](../testing.md) for the
graduation workflow): treat this page's markup and interactions as the target to
hit, not something to copy wholesale. The real page fetches from the backend
instead of reading `state`, and lives under Astro's routing/session/layout
conventions instead of this prototype's `boot()`.
