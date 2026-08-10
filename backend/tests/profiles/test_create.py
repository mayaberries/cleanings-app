import pytest
from databases import Database
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.db.repositories.profiles import OwnerProfilesRepository
from app.models.profiles.owner_profile import OwnerProfileInDB
from app.models.auth.user import UserPublic

pytestmark = pytest.mark.asyncio


class TestProfileCreate:
    async def test_profile_created_for_new_users(self, app: FastAPI, client: AsyncClient, db: Database) -> None:
        profiles_repo = OwnerProfilesRepository(db)

        new_user = {"email": "dwayne@johnson.io",
                    "username": "therock", "password": "dwaynetherockjohnson"}
        response = await client.post(app.url_path_for("users:register-new-user"), json=new_user)
        assert response.status_code == status.HTTP_201_CREATED

        created_user = UserPublic(**response.json())
        user_profile = await profiles_repo.get_profile_by_user_id(user_id=created_user.id)
        assert user_profile is not None
        assert isinstance(user_profile, OwnerProfileInDB)
