from typing import List
from fastapi import APIRouter, Body, Depends, HTTPException, Path
from starlette.status import HTTP_201_CREATED, HTTP_404_NOT_FOUND

from app.models.pet import PetCreate, PetInDB, PetPublic, PetUpdate
from app.models.user import UserInDB
from app.db.repositories.pets import PetsRepository

from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.pets import (
    get_pet_by_id_from_path,
    check_pet_access_permissions,
    check_pet_modification_permissions,
)


router = APIRouter()


@router.post("/", response_model=PetPublic, name="pets:create-pet", status_code=HTTP_201_CREATED)
async def create_new_pet(
    new_pet: PetCreate = Body(..., embed=False),
    current_user: UserInDB = Depends(get_current_active_user),
    pets_repo: PetsRepository = Depends(get_repository(PetsRepository)),
) -> PetPublic:
    return await pets_repo.create_pet(new_pet=new_pet, requesting_user=current_user)


@router.get("/", response_model=List[PetPublic], name="pets:list-all-user-pets")
async def get_all_pets(
    current_user: UserInDB = Depends(get_current_active_user),
    pets_repo: PetsRepository = Depends(get_repository(PetsRepository)),
) -> List[PetPublic]:
    return await pets_repo.list_all_user_pets(requesting_user=current_user)


@router.get(
    "/{pet_id}/",
    response_model=PetPublic,
    name="pets:get-pet-by-id",
    dependencies=[Depends(check_pet_access_permissions)],
)
async def get_pet_by_id(
    pet: PetInDB = Depends(get_pet_by_id_from_path),
) -> PetPublic:
    return pet


@router.put(
    "/{pet_id}/",
    response_model=PetPublic,
    name="pets:update-pet-by-id",
    dependencies=[Depends(check_pet_modification_permissions)],
)
async def update_pet_by_id(
    pet: PetInDB = Depends(get_pet_by_id_from_path),
    pet_update: PetUpdate = Body(..., embed=False),
    pets_repo: PetsRepository = Depends(get_repository(PetsRepository)),
) -> PetPublic:
    updated_pet = await pets_repo.update_pet(pet=pet, pet_update=pet_update)

    if not updated_pet:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="No pet found with that id.",
        )
    return updated_pet


@router.delete(
    "/{pet_id}/",
    response_model=str,
    name="pets:delete-pet-by-id",
    dependencies=[Depends(check_pet_modification_permissions)],
)
async def delete_pet_by_id(
    pet_id: str = Path(..., title="The ID of the pet to delete."),
    current_user: UserInDB = Depends(get_current_active_user),
    pets_repo: PetsRepository = Depends(get_repository(PetsRepository)),
) -> str:
    return await pets_repo.delete_pet_by_id(id=pet_id, requesting_user=current_user)