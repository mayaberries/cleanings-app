from fastapi import APIRouter, Path, Body
from fastapi.exceptions import HTTPException
from fastapi.param_functions import Depends
from starlette import status

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.clinic_owner_profiles import get_current_clinic_staff
from app.api.dependencies.database import get_repository
from app.db.repositories.clinic_owner_profiles import ClinicOwnerProfilesRepository
from app.db.repositories.profiles import OwnerProfilesRepository
from app.models.profiles.owner_profile import OwnerProfileUpdate, OwnerProfilePublic
from app.models.auth.token import ProfileClaimTokenResponse
from app.models.auth.user import UserInDB
from app.services import auth_service

router = APIRouter()


@router.get("/{username}", response_model=OwnerProfilePublic, name="profiles:get-profile-by-username")
async def get_profile_by_username(
        *,
        username: str = Path(..., min_length=3, pattern="^[a-zA-Z0-9_-]+$"),
        current_user: UserInDB = Depends(get_current_active_user),
        profiles_repo: OwnerProfilesRepository = Depends(
            get_repository(OwnerProfilesRepository)),
) -> OwnerProfilePublic:
    profile = await profiles_repo.get_profile_by_username(username=username)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No profile found with  username '{username}'."
        )

    return profile


@router.put("/me/", response_model=OwnerProfilePublic, name="profiles:update-own-profile")
async def update_own_profile(
        profile_update: OwnerProfileUpdate = Body(..., embed=False),
        current_user: UserInDB = Depends(get_current_active_user),
        profiles_repo: OwnerProfilesRepository = Depends(
            get_repository(OwnerProfilesRepository))
) -> OwnerProfilePublic:
    updated_profile = await profiles_repo.update_profile(profile_update=profile_update, requesting_user=current_user)
    return updated_profile


@router.post(
    "/{profile_id}/claim-token/",
    response_model=ProfileClaimTokenResponse,
    name="profiles:create-claim-token",
)
async def create_profile_claim_token(
        profile_id: str = Path(...),
        current_user: UserInDB = Depends(get_current_clinic_staff),
        profiles_repo: OwnerProfilesRepository = Depends(get_repository(OwnerProfilesRepository)),
        pivots_repo: ClinicOwnerProfilesRepository = Depends(get_repository(ClinicOwnerProfilesRepository)),
) -> ProfileClaimTokenResponse:
    profile = await profiles_repo.get_profile_by_id(id=profile_id)

    not_found = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No profile found with that id at your clinic.",
    )

    if not profile:
        raise not_found

    pivot = await pivots_repo.get_pivot_for_clinic_and_owner(
        clinic_id=current_user.clinic_id, owner_profile_id=profile_id
    )
    if not pivot:
        raise not_found

    if profile.user_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This profile is already linked to an account.",
        )

    token = auth_service.create_profile_claim_token(profile_id=profile.id)

    return ProfileClaimTokenResponse(token=token)
