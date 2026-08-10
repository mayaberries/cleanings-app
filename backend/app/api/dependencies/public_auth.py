from fastapi import Header, HTTPException, status, Depends

from app.models.clinic import ClinicInDB
from app.db.repositories.clinic_api_keys import ClinicAPIKeysRepository
from app.api.dependencies.database import get_repository

# TODO  Both envs work equally. Need to create separates envs
VALID_KEY_PREFIXES = ("pk_live_", "pk_test_")


async def get_clinic_from_public_key(
        x_clinic_key: str = Header(
            ...,
            alias="X-Clinic-Key",
            description="Clinic-scoped publishable key, e.g. pk_live_xxx. "
                        "Safe to embed in client-side code on the clinic's own site.",
        ),
        keys_repo: ClinicAPIKeysRepository = Depends(get_repository(ClinicAPIKeysRepository)),
) -> ClinicInDB:
    if not x_clinic_key.startswith(VALID_KEY_PREFIXES):
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
