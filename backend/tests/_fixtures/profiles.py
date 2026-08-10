import pytest_asyncio
from databases import Database

from app.db.repositories.profiles import OwnerProfilesRepository
from app.models.profiles.owner_profile import OwnerProfileCreate, OwnerProfileInDB

from app.db.repositories.clinic_owner_profiles import ClinicOwnerProfilesRepository
from app.models.clinics.clinic_owner_profile import ClinicOwnerProfileRegistration
from app.models.auth.user import UserInDB


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


@pytest_asyncio.fixture
async def owner_registered_with_clinic_a(db: Database, user_clinic_a_admin: UserInDB) -> OwnerProfileInDB:
    profiles_repo = OwnerProfilesRepository(db)
    pivots_repo = ClinicOwnerProfilesRepository(db)

    owner_profile = await profiles_repo.create_owner_profile(
        profile_create=OwnerProfileCreate(full_name="Clinic A Owner", phone_number="+1-555-0200")
    )

    await pivots_repo.register_owner_profile_with_clinic(
        clinic_id=user_clinic_a_admin.clinic_id,
        registration=ClinicOwnerProfileRegistration(owner_profile_id=owner_profile.id),
    )

    return owner_profile


@pytest_asyncio.fixture
async def owner_registered_with_clinic_b(db: Database, user_clinic_b_admin: UserInDB) -> OwnerProfileInDB:
    profiles_repo = OwnerProfilesRepository(db)
    pivots_repo = ClinicOwnerProfilesRepository(db)

    owner_profile = await profiles_repo.create_owner_profile(
        profile_create=OwnerProfileCreate(full_name="Clinic B Owner", phone_number="+1-555-0300")
    )

    await pivots_repo.register_owner_profile_with_clinic(
        clinic_id=user_clinic_b_admin.clinic_id,
        registration=ClinicOwnerProfileRegistration(owner_profile_id=owner_profile.id),
    )

    return owner_profile
