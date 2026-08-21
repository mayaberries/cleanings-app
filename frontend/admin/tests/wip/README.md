# wip/ — roadmap tests

These specs describe admin UI that doesn't exist yet. They're written against
`docs/openapi.json` (the backend already supports every endpoint referenced
here) and against what `src/pages/index.astro` already says is coming next:
services, appointments, and API-key tabs for clinic admins; a clinics list +
site-launch panel for superadmins.

Every `test.describe` in here is `.skip`'d, so they show up as **skipped**
(not failing) in normal `make test-admin` / `npm test` runs — that skip count
is the roadmap: it should shrink as pages get built.

## Workflow

When you build one of these pages:

1. Move its spec out of `tests/wip/` into `tests/`.
2. Drop the `.skip` from its `test.describe`.
3. Replace the placeholder selectors (role/label guesses) with whatever the
   real page actually renders — treat these as acceptance criteria to satisfy,
   not markup to match exactly.
4. If it needs input data beyond what's in `tests/wip/fixtures.ts`, promote
   that data into `tests/fixtures/` following the pattern in
   `tests/fixtures/onboarding.ts` (data) / `tests/helpers/onboarding.ts`
   (page actions).
5. Delete the now-unused export(s) from `tests/wip/fixtures.ts`.

## Coverage map

| Spec                       | Backend (docs/openapi.json)                                                             | UI status                                  |
|-----------------------------|-------------------------------------------------------------------------------------------|---------------------------------------------|
| `services.spec.ts`          | `services` tag — `GET/POST /api/services/`, `PUT/DELETE /api/services/{id}/`             | no page yet                                 |
| `appointments.spec.ts`      | `appointments` tag — list/confirm/cancel/withdraw under `/api/services/{id}/appointments/`| no page yet                                 |
| `api-keys.spec.ts`          | `clinic-api-keys` tag — `GET/POST /api/clinics/{id}/api-keys/`, `DELETE .../{key_id}/`    | onboarding issues the first key; no manage page |
| `clinic-settings.spec.ts`   | `clinics` tag (profile + staff join), `clinic-availability` tag (hours)                  | no page yet                                 |
| `superadmin-clinics.spec.ts`| `clinics` tag — `GET /api/clinics/`                                                       | no page yet ("clinics list ... come next")  |

Not covered here (out of scope for the admin dashboard — these serve the
public booking widget / pet-owner client, not clinic staff):
`public-booking`, `pets`, `clinic_pets`, `clinic_owners`, `feed`,
`profiles/{username}`, `users/claim`, `evaluations`.
