import pytest_asyncio
from databases import Database

from app.db.repositories.profiles import OwnerProfilesRepository
from app.models.owner_profile import OwnerProfileCreate, OwnerProfileInDB


@pytest_asyncio.fixture
async def guest_owner_profile(db: Database) -> OwnerProfileInDB:
    """An account-less owner profile, as if created by a clinic (or the
    future embeddable widget) on behalf of a walk-in owner who hasn't
    registered yet."""
    profiles_repo = OwnerProfilesRepository(db)
    return await profiles_repo.create_owner_profile(
        profile_create=OwnerProfileCreate(
            full_name="Guest Owner",
            phone_number="+1-555-0100",
        )
    )
