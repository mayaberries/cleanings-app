from typing import List

from fastapi import APIRouter, Body, Depends
from starlette.status import HTTP_201_CREATED

from app.models.clinics.clinic import ClinicInDB
from app.models.clinics.clinic_api_key import ClinicAPIKeyCreate, ClinicAPIKeyPublic, ClinicAPIKeyInDB
from app.models.auth.user import UserInDB
from app.db.repositories.clinic_api_keys import ClinicAPIKeysRepository

from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.clinics import get_clinic_by_id_from_path
from app.api.dependencies.clinic_api_keys import (
    check_clinic_admin_permissions,
    get_clinic_api_key_by_id_from_path,
)

router = APIRouter(dependencies=[Depends(check_clinic_admin_permissions)])


@router.post(
    "/",
    response_model=ClinicAPIKeyPublic,
    name="clinic-api-keys:create-key",
    status_code=HTTP_201_CREATED,
)
async def create_clinic_api_key(
        clinic: ClinicInDB = Depends(get_clinic_by_id_from_path),
        key_create: ClinicAPIKeyCreate = Body(..., embed=False),
        current_user: UserInDB = Depends(get_current_active_user),
        keys_repo: ClinicAPIKeysRepository = Depends(get_repository(ClinicAPIKeysRepository)),
) -> ClinicAPIKeyPublic:
    return await keys_repo.create_key_for_clinic(
        clinic_id=clinic.id, key_create=key_create, requesting_user=current_user
    )


@router.get("/", response_model=List[ClinicAPIKeyPublic], name="clinic-api-keys:list-keys")
async def list_clinic_api_keys(
        clinic: ClinicInDB = Depends(get_clinic_by_id_from_path),
        keys_repo: ClinicAPIKeysRepository = Depends(get_repository(ClinicAPIKeysRepository)),
) -> List[ClinicAPIKeyPublic]:
    return await keys_repo.list_keys_for_clinic(clinic_id=clinic.id)


@router.delete("/{key_id}/", response_model=ClinicAPIKeyPublic, name="clinic-api-keys:revoke-key")
async def revoke_clinic_api_key(
        clinic: ClinicInDB = Depends(get_clinic_by_id_from_path),
        key: ClinicAPIKeyInDB = Depends(get_clinic_api_key_by_id_from_path),
        current_user: UserInDB = Depends(get_current_active_user),
        keys_repo: ClinicAPIKeysRepository = Depends(get_repository(ClinicAPIKeysRepository)),
) -> ClinicAPIKeyPublic:
    return await keys_repo.revoke_key(key_id=key.id, clinic_id=clinic.id, requesting_user=current_user)
