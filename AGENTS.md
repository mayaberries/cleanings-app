# Agent notes

Full documentation lives in **[`docs/`](docs/README.md)** — start at its index
and follow the table. Don't re-derive things it already answers.

## Where to look first

| Working on | Read |
|---|---|
| `backend/` layering, permissions, conventions | [docs/architecture.md](docs/architecture.md) |
| What an entity means or why a field exists | [docs/domain.md](docs/domain.md) |
| `frontend/admin/` | [docs/admin-dashboard.md](docs/admin-dashboard.md) |
| `frontend/template/`, `frontend/sites/` | [docs/static-sites.md](docs/static-sites.md) |
| `backend/cli/` | [docs/admin-cli.md](docs/admin-cli.md) |
| Running or writing tests | [docs/testing.md](docs/testing.md) |
| "Is this a bug or a known gap?" | [docs/roadmap.md](docs/roadmap.md) — **check before fixing** |
| Endpoint shapes | `docs/openapi.json` |

## Traps that cost real time

**Never `.set()` a nanostore from server code.** Astro runs `output: "server"`;
module state is shared by every concurrent request, so writing auth state at SSR
leaks one visitor's session into another's page. Writes belong in `onMounted`
only. → [details](docs/admin-dashboard.md#nanostores-never-set-from-server-code)

**Astro Actions can't be driven with curl.** The CSRF origin check 403s, and
faking the header still won't yield a session cookie. Use Playwright to exercise
any flow that logs in.

**`astro dev` self-daemonizes.** It forks and the launching command exits, so it
won't block and a second call just says "already running". Use
`astro dev --background` / `status` / `logs` / `stop`.

**Permission rules live in two layers on purpose** — `app/api/dependencies/` and
`app/db/repositories/`. Grep both when changing one; they have drifted before.

**The backend test DB isn't reset between tests.** Intermittent
appointment-conflict failures are usually this, not your change.

**The backend login endpoint takes `username`, not `email`,** in its OAuth2 form —
the admin app posts the email address under the `username` key on purpose.

## House style

- Match the surrounding code's comment density and idiom. This codebase comments
  the *why* — non-obvious constraints, deliberate trade-offs — not the *what*.
- Not every layer is equally polished. An inconsistency is more likely an
  untouched corner than a decision; check the roadmap before "fixing" it.
- When you learn something non-obvious that isn't written down, add it to
  `docs/` rather than leaving it in a commit message.
