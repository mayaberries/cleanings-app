import pytest_asyncio
from databases import Database

from app.db.repositories.pets import PetProfilesRepository
from app.models.owner_profile import OwnerProfileInDB
from app.models.pet_profile import PetProfileCreate, PetProfileInDB


@pytest_asyncio.fixture
async def clinic_a_pet(db: Database, owner_registered_with_clinic_a: OwnerProfileInDB) -> PetProfileInDB:
    pets_repo = PetProfilesRepository(db)
    return await pets_repo.create_pet(
        new_pet=PetProfileCreate(name="Fido", species="dog"),
        owner_profile_id=owner_registered_with_clinic_a.id,
    )


@pytest_asyncio.fixture
async def clinic_b_pet(db: Database, owner_registered_with_clinic_b: OwnerProfileInDB) -> PetProfileInDB:
    pets_repo = PetProfilesRepository(db)
    return await pets_repo.create_pet(
        new_pet=PetProfileCreate(name="Rex", species="dog"),
        owner_profile_id=owner_registered_with_clinic_b.id,
    )
