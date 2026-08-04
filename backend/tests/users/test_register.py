import pytest
from databases.core import Database
from fastapi import FastAPI
from httpx import AsyncClient
from starlette.status import (
    HTTP_201_CREATED,
)

from app.db.repositories.users import UsersRepository
from app.models.user import UserPublic
from app.services import auth_service

pytestmark = pytest.mark.asyncio


class TestUsersRegistration:
    async def test_users_can_register_successfully(
            self,
            app: FastAPI,
            client: AsyncClient,
            db: Database
    ) -> None:
        user_repo = UsersRepository(db)
        new_user = {"email": "shakira@shakira.io",
                    "username": "shakirashakira", "password": "chantaje"}
        # make sure user doesn't exist yet
        user_in_db = await user_repo.get_user_by_email(email=new_user["email"])
        assert user_in_db is None
        # send post request to create user and ensure it is successful
        response = await client.post(app.url_path_for("users:register-new-user"), json=new_user)
        assert response.status_code == HTTP_201_CREATED
        # ensure that the user now exists in the db
        user_in_db = await user_repo.get_user_by_email(email=new_user["email"], populate=False)
        assert user_in_db is not None
        assert user_in_db.email == new_user["email"]
        assert user_in_db.username == new_user["username"]

        created_user = UserPublic(
            **response.json()).model_dump(exclude={"access_token", "profile"})
        assert created_user == user_in_db.model_dump(exclude={"password", "salt"})

    @pytest.mark.parametrize(
        "attr, value, status_code",
        (
                ("email", "shakira@shakira.io", 400),
                ("username", "shakirashakira", 400),
                ("email", "invalid_email@one@two.io", 422),
                ("password", "short", 422),
                ("username", "shakira@#$%^<>", 422),
                ("username", "ab", 422),
        )
    )
    async def test_user_registration_fails_when_credentials_are_taken(
            self,
            app: FastAPI,
            client: AsyncClient,
            db: Database,
            attr: str,
            value: str,
            status_code: int,
    ) -> None:
        new_user = {"email": "nottaken@email.io",
                    "username": "not_taken_username", "password": "freepassword"}
        new_user[attr] = value
        res = await client.post(app.url_path_for("users:register-new-user"), json=new_user)
        assert res.status_code == status_code

    async def test_users_saved_password_is_hashed_and_has_salt(
            self,
            app: FastAPI,
            client: AsyncClient,
            db: Database
    ) -> None:
        user_repo = UsersRepository(db)

        new_user = {"email": "beyonce@knowles.io",
                    "username": "queenbey", "password": "destinyschild"}

        response = await client.post(app.url_path_for("users:register-new-user"), json=new_user)

        assert response.status_code == HTTP_201_CREATED

        user_in_db = await user_repo.get_user_by_email(email=new_user["email"], populate=False)

        assert user_in_db is not None
        assert user_in_db.salt is not None and user_in_db.salt != "123"
        assert user_in_db.password != new_user["password"]
        assert auth_service.verify_password(
            password=new_user["password"],
            salt=user_in_db.salt,
            hashed_pwd=user_in_db.password
        )
