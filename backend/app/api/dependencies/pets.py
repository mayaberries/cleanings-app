from fastapi import HTTPException, Depends, Path, status

from app.models.auth.user import UserInDB
from app.models.profiles.pet_profile import PetProfileInDB

from app.db.repositories.pets import PetProfilesRepository

from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_current_active_user


def get_owner_profile_id_for_user(*, user: UserInDB) -> str:
    """The requesting user's own owner profile is what pets are actually
    scoped to — pets never reference the user id directly anymore."""
    profile = getattr(user, "profile", None)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No owner profile found for the current user.",
        )
    return profile.id


async def get_pet_by_id_from_path(
    pet_id: str = Path(...),
    pets_repo: PetProfilesRepository = Depends(get_repository(PetProfilesRepository)),
) -> PetProfileInDB:
    pet = await pets_repo.get_pet_by_id(id=pet_id)

    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pet found with that id."
        )
    return pet


def user_owns_pet(*, user: UserInDB, pet: PetProfileInDB) -> bool:
    return pet.owner_profile_id == get_owner_profile_id_for_user(user=user)


async def check_pet_access_permissions(
    current_user: UserInDB = Depends(get_current_active_user),
    pet: PetProfileInDB = Depends(get_pet_by_id_from_path),
) -> None:
    if not user_owns_pet(user=current_user, pet=pet):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action forbidden. Users are only able to access pets belonging to their own owner profile."
        )


async def check_pet_modification_permissions(
    current_user: UserInDB = Depends(get_current_active_user),
    pet: PetProfileInDB = Depends(get_pet_by_id_from_path),
) -> None:
    if not user_owns_pet(user=current_user, pet=pet):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action forbidden. Users are only able to modify pets belonging to their own owner profile."
        )