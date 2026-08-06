from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_404_NOT_FOUND

from app.models.pet_profile import (
    ClinicPetProfileCreate,
    PetProfileInDB,
    PetProfilePublic,
    PetProfileUpdate,
)
from app.models.user import UserInDB
from app.db.repositories.pets import PetProfilesRepository

from app.api.dependencies.database import get_repository
from app.api.dependencies.clinic_owner_profiles import get_current_clinic_staff
from app.api.dependencies.clinic_pets import (
    check_pet_owner_registered_with_clinic,
    get_clinic_pet_by_id_from_path,
    validate_owner_filter_registered_with_clinic,
)

router = APIRouter()


@router.post(
    "/",
    response_model=PetProfilePublic,
    name="clinic_pets:create-pet",
    status_code=HTTP_201_CREATED,
    dependencies=[Depends(check_pet_owner_registered_with_clinic)],
)
async def create_pet_for_owner(
        new_pet: ClinicPetProfileCreate = Body(..., embed=False),
        pets_repo: PetProfilesRepository = Depends(get_repository(PetProfilesRepository)),
) -> PetProfilePublic:
    return await pets_repo.create_pet(new_pet=new_pet, owner_profile_id=new_pet.owner_profile_id)


@router.get("/", response_model=List[PetProfilePublic], name="clinic_pets:list-pets")
async def list_clinic_pets(
        owner_profile_id: Optional[str] = Depends(validate_owner_filter_registered_with_clinic),
        current_user: UserInDB = Depends(get_current_clinic_staff),
        pets_repo: PetProfilesRepository = Depends(get_repository(PetProfilesRepository)),
) -> List[PetProfilePublic]:
    return await pets_repo.list_pet_profiles_for_clinic(
        clinic_id=current_user.clinic_id, owner_profile_id=owner_profile_id
    )


@router.get("/{pet_id}/", response_model=PetProfilePublic, name="clinic_pets:get-pet-by-id")
async def get_clinic_pet_by_id(
        pet: PetProfileInDB = Depends(get_clinic_pet_by_id_from_path),
) -> PetProfilePublic:
    return pet


@router.put("/{pet_id}/", response_model=PetProfilePublic, name="clinic_pets:update-pet-by-id")
async def update_clinic_pet_by_id(
        pet_update: PetProfileUpdate = Body(..., embed=False),
        pet: PetProfileInDB = Depends(get_clinic_pet_by_id_from_path),
        pets_repo: PetProfilesRepository = Depends(get_repository(PetProfilesRepository)),
) -> PetProfilePublic:
    updated_pet = await pets_repo.update_pet(pet=pet, pet_update=pet_update)

    if not updated_pet:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="No pet found with that id.")

    return updated_pet


@router.delete("/{pet_id}/", response_model=str, name="clinic_pets:delete-pet-by-id")
async def delete_clinic_pet_by_id(
        pet: PetProfileInDB = Depends(get_clinic_pet_by_id_from_path),
        pets_repo: PetProfilesRepository = Depends(get_repository(PetProfilesRepository)),
) -> str:
    return await pets_repo.delete_pet_by_id(id=pet.id, owner_profile_id=pet.owner_profile_id)
