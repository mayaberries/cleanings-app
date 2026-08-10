from typing import Optional

from fastapi import Header, HTTPException, status, Depends

from app.models.clinics.clinic import ClinicInDB
from app.db.repositories.clinic_api_keys import ClinicAPIKeysRepository
from app.api.dependencies.database import get_repository

# TODO(env-scoping): pk_live_ and pk_test_ currently behave identically
# end to end. The prefix below is checked for format validity only and
# then thrown away -- nothing downstream knows or cares which environment
# resolved the request. A "test" key can create real, dashboard-visible
# appointments against a real clinic right now. Before shipping, pick one:
#
#   1. Data isolation (do this if staging and prod share one database).
#      A booking made with a pk_test_ key must never appear next to real
#      bookings in a clinic's dashboard. Requires:
#        - get_active_clinic_by_public_key() (db/repositories/
#          clinic_api_keys.py) must start returning the key's
#          `environment` alongside the clinic -- it currently discards it.
#          Either widen the return type to a small (clinic, environment)
#          pair, or stash it on request.state in this dependency so
#          downstream handlers don't need a new param threaded through
#          every route signature.
#        - A new nullable `environment` column on `appointments` (new
#          migration), set from that value in create_public_appointment
#          (routes/public_booking.py).
#        - Every admin-facing appointment list/dashboard query gets an
#          implicit `WHERE environment = 'live'` (or an explicit toggle to
#          view test bookings) -- audit app/db/repositories/appointments.py
#          for every read path, not just the obvious ones.
#        - Decide whether get_or_create_guest_user (db/repositories/
#          users.py) should also tag test-environment guest accounts, so
#          they're excluded from any future clinic-facing client lists.
#
#   2. Deploy-level restriction (do this if staging and prod are fully
#      separate deployments/databases already). Add an APP_ENVIRONMENT
#      config value ('production' | 'staging') and reject the "wrong"
#      prefix right here, next to the existing format check -- e.g.
#      pk_live_ keys 401 in a staging deployment and vice versa. Much
#      smaller change than #1, but does nothing if prod and staging ever
#      end up sharing a DB.
#
# Neither is implemented yet -- pick based on the actual deploy topology,
# not in isolation from it.
VALID_KEY_PREFIXES = ("pk_live_", "pk_test_")


async def get_clinic_from_public_key(
    x_clinic_key: Optional[str] = Header(
        None,
        alias="X-Clinic-Key",
        description="Clinic-scoped publishable key, e.g. pk_live_xxx. "
                     "Safe to embed in client-side code on the clinic's own site.",
    ),
    keys_repo: ClinicAPIKeysRepository = Depends(get_repository(ClinicAPIKeysRepository)),
) -> ClinicInDB:
    """
    All failure paths return the same generic 401 + detail message, so a
    missing key, a malformed key, and a revoked/unknown key are
    indistinguishable to the caller — no need to help someone enumerate
    valid key shapes.
    """
    if not x_clinic_key or not x_clinic_key.startswith(VALID_KEY_PREFIXES):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing clinic API key.",
        )

    clinic = await keys_repo.get_active_clinic_by_public_key(public_key=x_clinic_key)

    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing clinic API key.",
        )

    return clinic