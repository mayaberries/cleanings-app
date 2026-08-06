from typing import Optional

from fastapi import Body, Depends, HTTPException, Path, Query, status

from app.models.user import UserInDB
from app.models.pet_profile import ClinicPetProfileCreate, PetProfileInDB

from app.db.repositories.pets import PetProfilesRepository
from app.db.repositories.clinic_owner_profiles import ClinicOwnerProfilesRepository

from app.api.dependencies.database import get_repository
from app.api.dependencies.clinic_owner_profiles import get_current_clinic_staff


async def check_pet_owner_registered_with_clinic(
        new_pet: ClinicPetProfileCreate = Body(..., embed=False),
        current_user: UserInDB = Depends(get_current_clinic_staff),
        pivots_repo: ClinicOwnerProfilesRepository = Depends(get_repository(ClinicOwnerProfilesRepository)),
) -> None:
    """A clinic can only create pets for owners it actually has a
    relationship with — same 404-not-403 opacity as the rest of the
    clinic-scoped layer, so staff can't fish for owner_profile_ids that
    belong to another clinic entirely."""
    pivot = await pivots_repo.get_pivot_for_clinic_and_owner(
        clinic_id=current_user.clinic_id, owner_profile_id=new_pet.owner_profile_id
    )

    if not pivot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No owner found with that id at your clinic.",
        )


async def get_clinic_pet_by_id_from_path(
        pet_id: str = Path(...),
        current_user: UserInDB = Depends(get_current_clinic_staff),
        pets_repo: PetProfilesRepository = Depends(get_repository(PetProfilesRepository)),
) -> PetProfileInDB:
    pet = await pets_repo.get_pet_by_id_for_clinic(id=pet_id, clinic_id=current_user.clinic_id)

    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pet found with that id at your clinic.",
        )

    return pet


async def validate_owner_filter_registered_with_clinic(
        owner_profile_id: Optional[str] = Query(None),
        current_user: UserInDB = Depends(get_current_clinic_staff),
        pivots_repo: ClinicOwnerProfilesRepository = Depends(get_repository(ClinicOwnerProfilesRepository)),
) -> Optional[str]:
    """When listing is filtered to a specific owner, that owner must be
    registered with this clinic — otherwise the filter would leak whether
    an owner exists at another clinic entirely."""
    if owner_profile_id is None:
        return None

    pivot = await pivots_repo.get_pivot_for_clinic_and_owner(
        clinic_id=current_user.clinic_id, owner_profile_id=owner_profile_id
    )

    if not pivot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No owner found with that id at your clinic.",
        )

    return owner_profile_id
