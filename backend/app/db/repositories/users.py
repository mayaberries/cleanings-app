from typing import Optional
from uuid import uuid4

from databases import Database
from fastapi import HTTPException
from pydantic import EmailStr
from starlette.status import HTTP_400_BAD_REQUEST

from app.db.repositories.base import BaseRepository
from app.db.repositories.profiles import OwnerProfilesRepository
from app.models.owner_profile import OwnerProfileCreate, OwnerProfilePublic
from app.models.user import UserCreate, UserPublic, UserInDB, UserRole
from app.services import auth_service

GET_USER_BY_EMAIL_QUERY = """
    SELECT id, username, email, email_verified, role, clinic_id, password, salt, is_active, is_superuser, created_at, updated_at
    FROM users
    WHERE email = :email;
"""

GET_USER_BY_USERNAME_QUERY = """
    SELECT id, username, email, email_verified, role, clinic_id, password, salt, is_active, is_superuser, created_at, updated_at
    FROM users
    WHERE username = :username;
"""

REGISTER_NEW_USER_QUERY = """
    INSERT INTO users (id, username, email, password, salt, role)
    VALUES (:id, :username, :email, :password, :salt, :role)
    RETURNING id, username, email, email_verified, role, clinic_id, password, salt, is_active, is_superuser, created_at, updated_at;
"""

GET_USER_BY_ID_QUERY = """
    SELECT id, username, email, email_verified, role, clinic_id, password, salt, is_active, is_superuser, created_at, updated_at
    FROM users
    WHERE id = :id;
"""


class UsersRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.auth_service = auth_service
        self.profiles_repo = OwnerProfilesRepository(db)

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

    async def register_new_user(self, *, new_user: UserCreate, role: UserRole = UserRole.client) -> UserInDB:
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

        user_params = {
            "id": str(uuid4()),
            "username": new_user.username,
            "email": new_user.email,
            "password": user_password_update.password,
            "salt": user_password_update.salt,
            "role": role.value,
        }

        created_user = await self.db.fetch_one(
            query=REGISTER_NEW_USER_QUERY,
            values=user_params
        )

        await self.profiles_repo.create_profile_for_user(
            profile_create=OwnerProfileCreate(user_id=created_user["id"])
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
            profile=OwnerProfilePublic(**profile.model_dump()) if profile else None,
        )
