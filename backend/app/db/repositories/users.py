import secrets
from typing import Optional
from uuid import uuid4

from databases import Database
from fastapi import HTTPException
from pydantic import EmailStr
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from app.db.repositories.base import BaseRepository
from app.db.repositories.profiles import OwnerProfilesRepository
from app.models.owner_profile import OwnerProfileCreate, OwnerProfilePublic, OwnerProfileUpdate
from app.models.user import UserCreate, UserPublic, UserInDB, UserRole
from app.services import auth_service

USER_COLUMNS = (
    "id, username, email, email_verified, role, clinic_id, password, salt, "
    "is_active, is_superuser, is_guest, created_at, updated_at"
)

GET_USER_BY_EMAIL_QUERY = f"""
    SELECT {USER_COLUMNS}
    FROM users
    WHERE email = :email;
"""

GET_USER_BY_USERNAME_QUERY = f"""
    SELECT {USER_COLUMNS}
    FROM users
    WHERE username = :username;
"""

REGISTER_NEW_USER_QUERY = f"""
    INSERT INTO users (id, username, email, password, salt, role)
    VALUES (:id, :username, :email, :password, :salt, :role)
    RETURNING {USER_COLUMNS};
"""

GET_USER_BY_ID_QUERY = f"""
    SELECT {USER_COLUMNS}
    FROM users
    WHERE id = :id;
"""

CREATE_GUEST_USER_QUERY = f"""
    INSERT INTO users (id, username, email, password, salt, role, is_guest)
    VALUES (:id, :username, :email, :password, :salt, :role, true)
    RETURNING {USER_COLUMNS};
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

    async def get_user_by_id(self, *, user_id: str, populate: bool = True) -> UserInDB:
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

    async def _create_user_record(self, *, new_user: UserCreate, role: UserRole) -> dict:
        """
        Shared validation + insert used by both register_new_user and
        register_user_for_existing_profile, so the uniqueness checks and
        password hashing only live in one place.
        """
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

        return await self.db.fetch_one(query=REGISTER_NEW_USER_QUERY, values=user_params)

    async def register_new_user(self, *, new_user: UserCreate, role: UserRole = UserRole.client) -> UserInDB:
        created_user = await self._create_user_record(new_user=new_user, role=role)

        await self.profiles_repo.create_owner_profile(
            profile_create=OwnerProfileCreate(user_id=created_user["id"])
        )

        return await self.populate_user(user=UserInDB(**created_user))

    async def register_user_for_existing_profile(
            self, *, new_user: UserCreate, existing_profile_id: str, role: UserRole = UserRole.client
    ) -> UserInDB:
        """
        Lets someone sign up against a profile that already exists --
        e.g. a client record a clinic entered manually before the owner
        ever created an account -- instead of always minting a fresh,
        empty profile the way register_new_user does.
        """
        profile = await self.profiles_repo.get_profile_by_id(id=existing_profile_id)

        if not profile:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="No profile found with that id."
            )

        if profile.user_id is not None:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="This profile is already linked to an account."
            )

        created_user = await self._create_user_record(new_user=new_user, role=role)

        linked_profile = await self.profiles_repo.link_user_to_profile(
            profile_id=existing_profile_id, user_id=created_user["id"]
        )

        if not linked_profile:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="This profile was just claimed by another account. Please try again."
            )

        return await self.populate_user(user=UserInDB(**created_user))

    async def get_or_create_guest_user(
        self, *, email: EmailStr, full_name: Optional[str] = None, phone_number: Optional[str] = None
    ) -> UserInDB:
        """
        Used by the public (no-JWT) booking surface. Looks up an existing
        account by email first -- covers a returning guest booking again,
        or someone who happens to already have a real registered account,
        in which case we just refresh their Profile with whatever contact
        details they typed into the widget this time rather than creating
        a duplicate user.

        A freshly-created guest gets `is_guest=True`, a random unusable
        password (generated, hashed, and then never surfaced anywhere --
        no login endpoint accepts it), and a synthetic username, since
        `username` stays NOT NULL/unique for every row regardless of how
        the account came to exist.
        """
        existing_user = await self.get_user_by_email(email=email, populate=False)

        if existing_user:
            contact_fields = {
                k: v for k, v in {"full_name": full_name, "phone_number": phone_number}.items()
                if v is not None
            }
            if contact_fields:
                await self.profiles_repo.update_profile(
                    profile_update=OwnerProfileUpdate(**contact_fields),
                    requesting_user=existing_user,
                )
            return existing_user

        generated_password = secrets.token_urlsafe(32)
        password_update = self.auth_service.create_salt_and_hashed_password(
            plaintext_password=generated_password
        )

        user_params = {
            "id": str(uuid4()),
            "username": f"guest_{uuid4().hex[:12]}",
            "email": email,
            "password": password_update.password,
            "salt": password_update.salt,
            "role": UserRole.client.value,
        }

        created_user = await self.db.fetch_one(query=CREATE_GUEST_USER_QUERY, values=user_params)
        guest_user = UserInDB(**created_user)

        await self.profiles_repo.create_owner_profile(
            profile_create=OwnerProfileCreate(
                user_id=guest_user.id, full_name=full_name, phone_number=phone_number
            )
        )

        return guest_user

    async def authenticate_user(self, *, email: EmailStr, password: str) -> Optional[UserInDB]:
        user = await self.get_user_by_email(email=email, populate=False)

        if not user or user.is_guest:
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