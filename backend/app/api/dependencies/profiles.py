from fastapi import Depends, HTTPException, Query, status

from app.core.config import SECRET_KEY
from app.models.profiles.owner_profile import OwnerProfileInDB
from app.db.repositories.profiles import OwnerProfilesRepository
from app.api.dependencies.database import get_repository
from app.services import auth_service


async def get_profile_from_claim_token(
    token: str = Query(..., description="The claim token issued for this owner profile."),
    profiles_repo: OwnerProfilesRepository = Depends(get_repository(OwnerProfilesRepository)),
) -> OwnerProfileInDB:
    profile_id = auth_service.get_profile_id_from_claim_token(token=token, secret_key=str(SECRET_KEY))

    profile = await profiles_repo.get_profile_by_id(id=profile_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No profile found for this claim token.",
        )

    if profile.user_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This profile has already been claimed.",
        )

    return profile