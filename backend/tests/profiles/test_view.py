import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient
from starlette.status import HTTP_200_OK

from app.models.profiles.owner_profile import OwnerProfilePublic
from app.models.auth.user import UserInDB

pytestmark = pytest.mark.asyncio

class TestProfileView:
    async def test_authenticated_user_can_view_other_users_profile(
            self, app: FastAPI, create_authorized_client, user_client_one: UserInDB, user_client_two: UserInDB
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_one)

        response = await authorized_client.get(
            app.url_path_for("profiles:get-profile-by-username",
                             username=user_client_two.username)
        )
        assert response.status_code == HTTP_200_OK
        profile = OwnerProfilePublic(**response.json())
        assert profile.username == user_client_two.username

    async def test_unregistered_users_cannot_access_other_users_profile(
            self, app: FastAPI, client: AsyncClient, user_client_two: UserInDB
    ) -> None:
        response = await client.get(
            app.url_path_for("profiles:get-profile-by-username",
                             username=user_client_two.username)
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_no_profile_is_returned_when_username_matches_no_user(
            self, app: FastAPI, create_authorized_client, user_client_one: UserInDB
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_one)

        response = await authorized_client.get(
            app.url_path_for("profiles:get-profile-by-username",
                             username="username_doesnt_match")
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
