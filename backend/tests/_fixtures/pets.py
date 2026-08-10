import pytest_asyncio
from databases import Database

from app.db.repositories.pets import PetProfilesRepository
from app.models.owner_profile import OwnerProfileInDB
from app.models.pet_profile import PetProfileCreate, PetProfileInDB
from app.db.repositories.profiles import OwnerProfilesRepository
from app.models.user import UserInDB


async def create_pet_for_user(
        db: Database, user: UserInDB, name: str = "Test Pet", species: str = "dog"
) -> PetProfileInDB:
    """Not a fixture itself -- a helper for fixtures/tests that need a pet
    under an arbitrary user's own owner profile (e.g. looping over
    test_client_list). Every client user already has an owner_profile via
    register_new_user, so this never has to create one."""
    profiles_repo = OwnerProfilesRepository(db)
    pets_repo = PetProfilesRepository(db)
    owner_profile = await profiles_repo.get_profile_by_user_id(user_id=user.id)
    return await pets_repo.create_pet(
        new_pet=PetProfileCreate(name=name, species=species),
        owner_profile_id=owner_profile.id,
    )


@pytest_asyncio.fixture
async def user_client_one_pet(db: Database, user_client_one: UserInDB) -> PetProfileInDB:
    return await create_pet_for_user(db, user_client_one, name="Rex")


@pytest_asyncio.fixture
async def user_client_two_pet(db: Database, user_client_two: UserInDB) -> PetProfileInDB:
    return await create_pet_for_user(db, user_client_two, name="Milo")


@pytest_asyncio.fixture
async def user_client_three_pet(db: Database, user_client_three: UserInDB) -> PetProfileInDB:
    return await create_pet_for_user(db, user_client_three, name="Nala")


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
