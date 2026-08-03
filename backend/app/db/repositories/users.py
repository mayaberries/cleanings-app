from typing import Optional
from uuid import uuid4
from pydantic import EmailStr
from fastapi import HTTPException, status
from sqlalchemy.sql.elements import False_
from sqlalchemy.sql.expression import false
from starlette.status import HTTP_400_BAD_REQUEST
from databases import Database

from app.db.repositories.base import BaseRepository
from app.models.user import UserCreate, UserPublic, UserUpdate, UserInDB
from app.services import auth_service
from app.db.repositories.profiles import ProfilesRepository
from app.models.profile import ProfileCreate, ProfilePublic

GET_USER_BY_EMAIL_QUERY = """
    SELECT id, username, email, email_verified, password, salt, is_active, is_superuser, created_at, updated_at
    FROM users
    WHERE email = :email;
"""
GET_USER_BY_USERNAME_QUERY = """
    SELECT id, username, email, email_verified, password, salt, is_active, is_superuser, created_at, updated_at
    FROM users
    WHERE username = :username;
"""
REGISTER_NEW_USER_QUERY = """
    INSERT INTO users (id, username, email, password, salt)
    VALUES (:id, :username, :email, :password, :salt)
    RETURNING id, username, email, email_verified, password, salt, is_active, is_superuser, created_at, updated_at;
"""

GET_USER_BY_ID_QUERY = """
    SELECT id, username, email, email_verified, password, salt, is_active, is_superuser, created_at, updated_at
    FROM users
    WHERE id = :id;
"""


class UsersRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.auth_service = auth_service
        self.profiles_repo = ProfilesRepository(db)

    async def get_user_by_email(self, *, email: EmailStr, populate: bool = True) -> UserInDB:
        user_record = await self.db.fetch_one(query=GET_USER_BY_EMAIL_QUERY, values={"email": email})

        if user_record:
            user = UserInDB(**user_record)

            if populate:
                return await self.populate_user(user=user)

            return user

    async def get_user_by_id(self, *, user_id: str, populate: bool = True) -> UserPublic:
        user_record = await self.db.fetch_one(
            query=GET_USER_BY_ID_QUERY,
            values={"id": user_id}
        )

        if user_record:
            user = UserInDB(**user_record)

            if populate:
                return await self.populate_user(user=user)

            return user

    async def get_user_by_username(self, *, username: str, populate: bool = True) -> UserInDB:
        user_record = await self.db.fetch_one(query=GET_USER_BY_USERNAME_QUERY, values={"username": username})

        if user_record:
            user = UserInDB(**user_record)

            if populate:
                return await self.populate_user(user=user)

            return user

    async def register_new_user(self, *, new_user: UserCreate) -> UserInDB:
        if await self.get_user_by_email(email=new_user.email) is not None:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="That email is already taken. Please try another one."
            )

        if await self.get_user_by_username(username=new_user.username) is not None:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="That username is already taken. Please try another one."
            )

        user_password_update = self.auth_service.create_salt_and_hashed_password(
            plaintext_password=new_user.password
        )

        # Build query parameters directly without relying on pydantic.copy()
        user_params = {
            "id": str(uuid4()),
            "username": new_user.username,
            "email": new_user.email,
            "password": user_password_update.password,
            "salt": user_password_update.salt,
        }

        created_user = await self.db.fetch_one(
            query=REGISTER_NEW_USER_QUERY,
            values=user_params
        )

        await self.profiles_repo.create_profile_for_user(
            profile_create=ProfileCreate(user_id=created_user["id"])
        )

        return await self.populate_user(user=UserInDB(**created_user))

    async def authenticate_user(self, *, email: EmailStr, password: str) -> Optional[UserInDB]:
        user = await self.get_user_by_email(email=email, populate=False)

        if not user:
            return None

        if not self.auth_service.verify_password(password=password, salt=user.salt, hashed_pwd=user.password):
            return None

        return user

    async def populate_user(self, *, user: UserInDB) -> UserInDB:
        profile = await self.profiles_repo.get_profile_by_user_id(user_id=user.id)

        return UserPublic(
            **user.model_dump(),
            profile=ProfilePublic(**profile.model_dump()) if profile else None,
        )