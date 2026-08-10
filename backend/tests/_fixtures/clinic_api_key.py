import pytest_asyncio
from databases import Database

from app.db.repositories.clinic_api_keys import ClinicAPIKeysRepository
from app.models.clinics.clinic_api_key import ClinicAPIKeyCreate, ClinicAPIKeyInDB
from app.models.auth.user import UserInDB


@pytest_asyncio.fixture
async def clinic_a_public_key(db: Database, user_clinic_a_admin: UserInDB) -> ClinicAPIKeyInDB:
    keys_repo = ClinicAPIKeysRepository(db)
    return await keys_repo.create_key_for_clinic(
        clinic_id=user_clinic_a_admin.clinic_id,
        key_create=ClinicAPIKeyCreate(label="test widget - clinic a"),
        requesting_user=user_clinic_a_admin,
    )


@pytest_asyncio.fixture
async def clinic_b_public_key(db: Database, user_clinic_b_admin: UserInDB) -> ClinicAPIKeyInDB:
    keys_repo = ClinicAPIKeysRepository(db)
    return await keys_repo.create_key_for_clinic(
        clinic_id=user_clinic_b_admin.clinic_id,
        key_create=ClinicAPIKeyCreate(label="test widget - clinic b"),
        requesting_user=user_clinic_b_admin,
    )