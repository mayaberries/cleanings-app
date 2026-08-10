import pytest
from fastapi import FastAPI, status
from pydantic import HttpUrl

from app.models.profiles.owner_profile import OwnerProfilePublic
from app.models.auth.user import UserInDB

pytestmark = pytest.mark.asyncio


class TestProfileManagement:
    @pytest.mark.parametrize(
        "attr,value",
        (
                ("full_name", "Lebron James"),
                ("phone_number", "555-333-1000"),
                ("bio", "This is a test bio"),
                ("image", "http://testimages.com/testimage"),
        )
    )
    async def test_user_can_update_own_profile(
            self, app: FastAPI, create_authorized_client, user_client_one: UserInDB, attr: str, value: str
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_one)

        assert getattr(user_client_one.profile, attr) != value

        response = await authorized_client.put(
            app.url_path_for("profiles:update-own-profile"),
            json={attr: value},
        )

        assert response.status_code == status.HTTP_200_OK

        profile = OwnerProfilePublic(**response.json())

        actual = getattr(profile, attr)
        if isinstance(actual, HttpUrl):
            actual = str(actual)

        assert actual == value

    @pytest.mark.parametrize(
        "attr, value, status_code",
        (
                ("full_name", [], 422),
                ("bio", {}, 422),
                ("image", "./image-string.png", 422),
                ("image", 5, 422),
        ),
    )
    async def test_user_receives_error_for_invalid_update_params(
            self,
            app: FastAPI,
            create_authorized_client,
            user_client_one: UserInDB,
            attr: str,
            value: str,
            status_code: int,
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_one)

        response = await authorized_client.put(
            app.url_path_for("profiles:update-own-profile"),
            json={attr: value}
        )

        assert response.status_code == status_code
