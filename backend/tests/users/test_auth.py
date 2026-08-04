import jwt
import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from starlette.status import (
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
)

from app.core.config import SECRET_KEY, JWT_ALGORITHM, JWT_AUDIENCE
from app.models.user import UserInDB, UserPublic
from app.services import auth_service

pytestmark = pytest.mark.asyncio

class TestUserLogin:
    async def test_user_can_login_successfully_and_receives_valid_token(
            self, app: FastAPI, client: AsyncClient, user_client_one: UserInDB
    ) -> None:
        client.headers["content-type"] = "application/x-www-form-urlencoded"

        login_data = {
            "username": user_client_one.email,
            "password": "clientOnePass",
        }

        response = await client.post(app.url_path_for("users:login-email-and-password"),
                                     data=login_data)

        assert response.status_code == HTTP_200_OK

        token = response.json().get("access_token")
        creds = jwt.decode(token, str(SECRET_KEY),
                           audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM])

        assert "username" in creds
        assert creds["username"] == user_client_one.username

        assert "sub" in creds
        assert creds["sub"] == user_client_one.email

        assert "token_type" in response.json()
        assert response.json().get("token_type") == "bearer"

    @pytest.mark.parametrize(
        "credential, wrong_value, status_code",
        (
                ("email", "wrong@email.com", 401),
                ("email", None, 422),
                ("email", "notemail", 401),
                ("password", "wrongpassword", 401),
                ("password", None, 422),
        ),
    )
    async def test_user_with_wrong_creds_doesnt_receive_token(
            self, app: FastAPI, client: AsyncClient, user_client_one: UserInDB, credential: str, wrong_value: str,
            status_code: int,
    ) -> None:
        client.headers["content-type"] = "application/x-www-form-urlencoded"
        user_data = user_client_one.model_dump()
        user_data["password"] = "password123"
        user_data[credential] = wrong_value
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }

        response = await client.post(app.url_path_for("users:login-email-and-password"), data=login_data)

        assert response.status_code == status_code
        assert "access_token" not in response.json()


class TestUserMe:
    async def test_authenticated_user_can_retrieve_own_data(
            self, app: FastAPI, create_authorized_client, user_client_one: UserInDB,
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_one)

        response = await authorized_client.get(app.url_path_for("users:get-current-user"))

        assert response.status_code == HTTP_200_OK

        user = UserPublic(**response.json())

        assert user.email == user_client_one.email
        assert user.username == user_client_one.username
        assert user.id == user_client_one.id

    async def test_user_cannot_access_own_data_if_not_authenticated(
            self, app: FastAPI, client: AsyncClient, user_client_one: UserInDB
    ) -> None:
        response = await client.get(app.url_path_for("users:get-current-user"))

        assert response.status_code == HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize("jwt_prefix", (("",), ("value",), ("Token",), ("JWT",), ("Swearer",),))
    async def test_user_cannot_access_own_data_with_incorrect_jwt_prefix(
            self, app: FastAPI, client: AsyncClient, user_client_one: UserInDB, jwt_prefix: str,
    ) -> None:
        token = auth_service.create_access_token_for_user(
            user=user_client_one, secret_key=str(SECRET_KEY))

        response = await client.get(
            app.url_path_for("users:get-current-user"),
            headers={
                "Authorization": f"{jwt_prefix} {token}"
            }
        )

        assert response.status_code == HTTP_401_UNAUTHORIZED
