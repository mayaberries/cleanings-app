from fastapi import HTTPException, Depends, Path, status

from app.models.user import UserInDB
from app.models.pet import PetInDB

from app.db.repositories.pets import PetsRepository

from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_current_active_user


async def get_pet_by_id_from_path(
    pet_id: str = Path(...),
    current_user: UserInDB = Depends(get_current_active_user),
    pets_repo: PetsRepository = Depends(get_repository(PetsRepository)),
) -> PetInDB:
    pet = await pets_repo.get_pet_by_id(id=pet_id, requesting_user=current_user)

    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pet found with that id."
        )
    return pet


def user_owns_pet(*, user: UserInDB, pet: PetInDB) -> bool:
    return pet.owner == user.id


async def check_pet_access_permissions(
    current_user: UserInDB = Depends(get_current_active_user),
    pet: PetInDB = Depends(get_pet_by_id_from_path),
) -> None:
    if not user_owns_pet(user=current_user, pet=pet):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action forbidden. Users are only able to access pets they own."
        )


async def check_pet_modification_permissions(
    current_user: UserInDB = Depends(get_current_active_user),
    pet: PetInDB = Depends(get_pet_by_id_from_path),
) -> None:
    if not user_owns_pet(user=current_user, pet=pet):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action forbidden. Users are only able to modify pets they own."
        )