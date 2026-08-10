from typing import Union, Type, Optional

import jwt
import pytest
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from httpx import AsyncClient
from pydantic import ValidationError
from starlette.datastructures import Secret

from app.core.config import SECRET_KEY, JWT_ALGORITHM, JWT_AUDIENCE, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.auth.user import UserInDB
from app.services import auth_service

pytestmark = pytest.mark.asyncio


class TestAuthTokens:
    async def test_can_create_access_token_succesfully(
            self, app: FastAPI, client: AsyncClient, user_client_one: UserInDB
    ) -> None:
        access_token = auth_service.create_access_token_for_user(
            user=user_client_one,
            secret_key=str(SECRET_KEY),
            audience=JWT_AUDIENCE,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES,
        )

        creds = jwt.decode(access_token, str(SECRET_KEY),
                           audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM])

        assert creds.get("username") is not None
        assert creds.get("username") == user_client_one.username
        assert creds["aud"] == JWT_AUDIENCE

    async def test_token_missing_user_is_invalid(self, app: FastAPI, client: AsyncClient) -> None:
        access_token = auth_service.create_access_token_for_user(
            user=None,
            secret_key=str(SECRET_KEY),
            audience=JWT_AUDIENCE,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES,
        )

        with pytest.raises(jwt.PyJWTError):
            jwt.decode(access_token, str(SECRET_KEY),
                       audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM])

    @pytest.mark.parametrize(
        "secret_key, jwt_audience, exception",
        (
                ("wrong-secret", JWT_AUDIENCE, jwt.InvalidSignatureError),
                (None, JWT_AUDIENCE, jwt.InvalidSignatureError),
                (SECRET_KEY, "othersite:auth", jwt.InvalidAudienceError),
                (SECRET_KEY, None, ValidationError),
        )
    )
    async def test_invalid_token_content_raises_error(
            self,
            app: FastAPI,
            client: AsyncClient,
            user_client_one: UserInDB,
            secret_key: Union[str, Secret],
            jwt_audience: str,
            exception: Type[BaseException],

    ) -> None:
        with pytest.raises(exception):
            access_token = auth_service.create_access_token_for_user(
                user=user_client_one,
                secret_key=str(secret_key),
                audience=jwt_audience,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES,
            )

            jwt.decode(access_token, str(SECRET_KEY),
                       audience=JWT_AUDIENCE, algorithms=[JWT_ALGORITHM])

    async def test_can_retrieve_username_from_token(
            self, app: FastAPI, client: AsyncClient, user_client_one: UserInDB
    ) -> None:
        token = auth_service.create_access_token_for_user(
            user=user_client_one, secret_key=str(SECRET_KEY))

        username = auth_service.get_username_from_token(
            token=token, secret_key=str(SECRET_KEY))

        assert username == user_client_one.username

    @pytest.mark.parametrize(
        "secret, wrong_token",
        (
                (SECRET_KEY, "asdf"),  # use wrong token
                (SECRET_KEY, ""),  # use wrong token
                (SECRET_KEY, None),  # use wrong token
                ("ABC123", "use correct token"),  # use wrong secret
        ),
    )
    async def test_error_when_token_or_secret_is_wrong(
            self,
            app: FastAPI,
            client: AsyncClient,
            user_client_one: UserInDB,
            secret: Union[Secret, str],
            wrong_token: Optional[str]
    ) -> None:
        token = auth_service.create_access_token_for_user(
            user=user_client_one, secret_key=str(SECRET_KEY))

        if wrong_token == "use correct token":
            wrong_token = token

        with pytest.raises(HTTPException):
            username = auth_service.get_username_from_token(
                token=wrong_token, secret_key=str(secret))
