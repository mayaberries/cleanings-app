# Admin dashboard (`frontend/admin/`)

The Astro SSR dashboard clinic staff and the platform superuser sign into. It is
an HTTP client of the backend like everything else — it never touches the
database.

```
Astro 7, output: "server", @astrojs/node (standalone)   — runs as a Node process
Vue 3 islands + nanostores                              — the interactive bits
Tailwind v4 via @tailwindcss/vite                       — @theme in global.css
Playwright                                              — tests
```

## Request lifecycle

```
src/middleware.ts        session cookie → context.locals.user, then two guards:
                           1. not signed in + not a public path  → /login
                           2. signed in but wrong role for this tab → their landing tab
        ↓
src/pages/*.astro        reads Astro.locals.user, passes it down as a prop
        ↓
src/layout/AdminLayout.astro   chrome + <AdminNav client:load>
```

Session storage is Astro's built-in session driver, configured by the Node
adapter (filesystem-backed in dev). `src/lib/session.ts`'s `requireSession()`
exists to turn "no session driver configured" into a clear error instead of a
confusing `undefined`.

Writes to the session happen only in **Astro Actions** (`src/actions/index.ts`):
`login`, `logout`, `demoLogin`. `login` exchanges email/password for a JWT at
`POST /users/login/token`, then immediately fetches `/users/me/` to build the
`SessionUser`.

> The backend's login endpoint takes an OAuth2 form with a **`username`** field,
> not `email` — the action posts the email address under the `username` key. This
> looks like a bug at the call site and isn't.

## Routing and the role gate

`src/lib/nav.ts` is the single tab registry. Each tab's `role` does double duty:
it decides **who sees the tab in the nav** *and* **who may land on its URL**.
Keeping both readings in one table is the whole point — a tab hidden from the nav
but reachable by typing its URL is exactly the bug this prevents.

| Tab | Path | Visible to |
|---|---|---|
| Clinics | `/clinics` | superadmin |
| Overview | `/overview` | clinic_admin |
| Appointments | `/appointments` | clinic_admin |
| Services | `/services` | clinic_admin |
| API Keys | `/api-keys` | clinic_admin |
| Website | `/website` | clinic_admin |
| Account | `/account` | both |

`/` is not a tab — it redirects to whichever tab the role starts on
(`landingPathFor()`), so `login.astro` and the middleware can both send people to
a plain `/` without knowing the role. `/login` and `/onboarding` are the public
paths. Anything `tabForPath()` doesn't recognize falls through to Astro's 404
rather than being redirected.

Most of these pages are still `TabStub` placeholders. Their acceptance criteria
are already written as skipped specs — see [testing.md](testing.md).

> ⚠️ **The role gate is a UI guard, not the security boundary.** Nothing stops a
> signed-in clinic admin from calling `GET /api/clinics/` directly. Every
> endpoint still has to enforce `is_superuser`/role server-side.

## nanostores: never `.set()` from server code

**This is the single most important rule in this app, and it is not obvious.**

Nanostores atoms are module-level singletons. Under `output: "server"` the module
is instantiated **once per Node process and shared by every concurrent request**.
A `.set($currentUser)` in `.astro` frontmatter or in middleware would let one
visitor's session data render into another visitor's page — a real auth leak, not
a theoretical one.

So `src/stores/auth.ts` confines every write to `hydrateCurrentUser()`, which is
only ever called from a Vue `onMounted` — a lifecycle hook that does not run
during SSR. The server's copy of those stores stays permanently `null`, which is
exactly what we want.

The pattern for any new island that needs the user:

```
SSR      → gets the user through props (Astro.locals.user → <Component user={…}>)
Client   → onMounted fills the store; later islands read the store, no prop-drilling
Render   → storeUser.value ?? props.user     // identical before and after hydration
```

That `??` fallback is what keeps the server markup and the hydrated markup
identical — no mismatch, no flash of empty nav. `AdminNav.vue` is the reference
implementation; copy its shape.

## Demo mode

The sign-in page has a **"Demo · Clinic admin"** button (the `demoLogin` action)
that seeds a fake session from `src/lib/demoData.ts` — no backend needed. It's
how the Playwright suite runs without an API or database.

> `buildDemoUser()` always returns a **`clinic_admin`**. There is no demo
> superadmin, which is why the superadmin half of the role gate (the Clinics tab;
> a superadmin being kept off `/overview`) is currently untested. Adding a
> `demoSuperadminLogin` action would close that cheaply.

## The onboarding wizard

`/onboarding` is a public, multi-step signup flow (account → clinic → services →
review → launch). It's deliberately **vanilla JS, not Vue** — it predates the
islands work. Logic lives in `src/lib/onboarding/*`, with mutable wizard state in
a plain object in `state.js`. Don't confuse that with the nanostores auth state;
they solve different problems and shouldn't be merged.

It has its own demo mode (`demoBackend.js`) that swaps every backend call for a
mocked response, separate from the session-level demo login above.

> **Known backend gap the wizard runs into:** `POST /users/` always registers a
> `client`-role account, but creating a clinic requires `clinic_admin`. There is
> no self-service HTTP path to register as a clinic admin yet, so a real (non-demo)
> onboarding run fails at the clinic step unless the account is promoted out of
> band. The wizard surfaces this in its error copy (`launch.js`).

## Styling and design tokens

Colors and fonts for the admin app live in `src/styles/global.css` under
Tailwind v4's `@theme` block. Both `.astro` and `.vue` files are scanned by
Tailwind's automatic content detection.

> **Drift worth knowing about:** `frontend/shared/design-tokens.mjs` calls itself
> the "single source of truth" for tokens across every Astro project, but that's
> no longer true. `frontend/template` doesn't import it at all; `frontend/admin`
> imports only `googleFontsHref` from it and defines its real colors in
> `global.css`; and `docs/proto/theme-config.js` keeps a third hand-copied set.
> The same hex values are currently maintained in three places. Its `colors` and
> `fontFamily` exports are effectively dead code.

## Layout of the source tree

```
src/actions/index.ts     Astro Actions — the only place the session is written
src/components/          Vue islands (.vue) and Astro components (.astro)
src/layout/              AdminLayout.astro — the signed-in chrome
src/lib/auth.ts          SessionUser type
src/lib/nav.ts           tab registry + role gate helpers (imported by server AND client)
src/lib/session.ts       requireSession() guard
src/lib/demoData.ts      demo session + seeded stat data
src/lib/onboarding/      the vanilla-JS wizard
src/middleware.ts        auth + role guards
src/pages/               routes
src/stores/auth.ts       nanostores — read the warning above before touching
tests/                   Playwright specs
```
