from fastapi import APIRouter, Body, Depends
from starlette.status import HTTP_201_CREATED

from app.models.clinic_owner_profile import (
    ClinicOwnerProfileInDB,
    ClinicOwnerProfilePublic,
    ClinicOwnerProfileRegistration,
    ClinicOwnerProfileUpdate,
)
from app.models.user import UserInDB
from app.db.repositories.clinic_owner_profiles import ClinicOwnerProfilesRepository

from app.api.dependencies.database import get_repository
from app.api.dependencies.clinic_owner_profiles import (
    get_current_clinic_staff,
    get_clinic_owner_pivot_by_id_from_path,
)

router = APIRouter()


@router.post("/", response_model=ClinicOwnerProfilePublic, name="clinic_owners:register-owner", status_code=HTTP_201_CREATED)
async def register_owner_with_clinic(
        registration: ClinicOwnerProfileRegistration = Body(..., embed=False),
        current_user: UserInDB = Depends(get_current_clinic_staff),
        pivots_repo: ClinicOwnerProfilesRepository = Depends(get_repository(ClinicOwnerProfilesRepository)),
) -> ClinicOwnerProfilePublic:
    pivot = await pivots_repo.register_owner_profile_with_clinic(
        clinic_id=current_user.clinic_id, registration=registration
    )
    return await pivots_repo.populate_pivot(pivot=pivot)


@router.get("/{owner_profile_id}/", response_model=ClinicOwnerProfilePublic, name="clinic_owners:get-owner-by-id")
async def get_clinic_owner_by_id(
        pivot: ClinicOwnerProfileInDB = Depends(get_clinic_owner_pivot_by_id_from_path),
        pivots_repo: ClinicOwnerProfilesRepository = Depends(get_repository(ClinicOwnerProfilesRepository)),
) -> ClinicOwnerProfilePublic:
    return await pivots_repo.populate_pivot(pivot=pivot)


@router.put("/{owner_profile_id}/", response_model=ClinicOwnerProfilePublic, name="clinic_owners:update-owner")
async def update_clinic_owner(
        pivot_update: ClinicOwnerProfileUpdate = Body(..., embed=False),
        pivot: ClinicOwnerProfileInDB = Depends(get_clinic_owner_pivot_by_id_from_path),
        pivots_repo: ClinicOwnerProfilesRepository = Depends(get_repository(ClinicOwnerProfilesRepository)),
) -> ClinicOwnerProfilePublic:
    updated_pivot = await pivots_repo.update_pivot(pivot=pivot, pivot_update=pivot_update)
    return await pivots_repo.populate_pivot(pivot=updated_pivot)