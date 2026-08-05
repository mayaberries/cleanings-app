from uuid import uuid4

from app.db.repositories.base import BaseRepository
from app.models.owner_profile import OwnerProfileCreate, OwnerProfileUpdate, OwnerProfileInDB
from app.models.user import UserInDB

CREATE_OWNER_PROFILE_QUERY = """
    INSERT INTO owner_profiles (id, full_name, phone_number, bio, image, user_id)
    VALUES (:id, :full_name, :phone_number, :bio, :image, :user_id)
    RETURNING id, full_name, phone_number, bio, image, user_id, created_at, updated_at;
"""

GET_PROFILE_BY_ID_QUERY = """
    SELECT id, full_name, phone_number, bio, image, user_id, created_at, updated_at
    FROM owner_profiles
    WHERE id = :id;
"""

GET_PROFILE_BY_USER_ID_QUERY = """
    SELECT id, full_name, phone_number, bio, image, user_id, created_at, updated_at
    FROM owner_profiles
    WHERE user_id = :user_id;
"""

GET_PROFILE_BY_USERNAME_QUERY = """
    SELECT p.id,
           u.email AS email,
           u.username AS username,
           full_name,
           phone_number,
           bio,
           image,
           user_id,
           p.created_at,
           p.updated_at
    FROM owner_profiles p
        INNER JOIN users u
        ON p.user_id = u.id
    WHERE user_id = (SELECT id FROM users WHERE username = :username);
"""

UPDATE_PROFILE_QUERY = """
    UPDATE owner_profiles
    SET full_name    = :full_name,
        phone_number = :phone_number,
        bio          = :bio,
        image        = :image
    WHERE user_id = :user_id
    RETURNING id, full_name, phone_number, bio, image, user_id, created_at, updated_at;
"""

LINK_USER_TO_PROFILE_QUERY = """
    UPDATE owner_profiles
    SET user_id = :user_id
    WHERE id = :id AND user_id IS NULL
    RETURNING id, full_name, phone_number, bio, image, user_id, created_at, updated_at;
"""


class OwnerProfilesRepository(BaseRepository):
    async def create_owner_profile(self, *, profile_create: OwnerProfileCreate) -> OwnerProfileInDB:
        """Creates an owner profile. profile_create.user_id may be None —
        that's a valid, account-less owner (e.g. added by a clinic, or via
        a public booking form) who can be linked to a User later."""
        values = {**profile_create.model_dump(), "id": str(uuid4())}

        if values.get("image") is not None:
            values["image"] = str(values["image"])

        created_profile = await self.db.fetch_one(
            query=CREATE_OWNER_PROFILE_QUERY,
            values=values,
        )

        return OwnerProfileInDB(**created_profile)

    async def get_profile_by_id(self, *, id: str) -> OwnerProfileInDB:
        profile_record = await self.db.fetch_one(query=GET_PROFILE_BY_ID_QUERY, values={"id": id})

        if profile_record:
            return OwnerProfileInDB(**profile_record)

    async def get_profile_by_user_id(self, *, user_id: str) -> OwnerProfileInDB:
        profile_record = await self.db.fetch_one(query=GET_PROFILE_BY_USER_ID_QUERY, values={"user_id": user_id})

        if not profile_record:
            return None

        return OwnerProfileInDB(**profile_record)

    async def get_profile_by_username(self, *, username: str) -> OwnerProfileInDB:
        profile_record = await self.db.fetch_one(query=GET_PROFILE_BY_USERNAME_QUERY, values={"username": username})

        if profile_record:
            return OwnerProfileInDB(**profile_record)

    async def update_profile(self, *, profile_update: OwnerProfileUpdate,
                             requesting_user: UserInDB) -> OwnerProfileInDB:
        profile = await self.get_profile_by_user_id(user_id=requesting_user.id)

        update_params = profile.model_copy(
            update=profile_update.model_dump(exclude_unset=True))

        values = update_params.model_dump(
            exclude={"id", "created_at", "updated_at", "username", "email"})

        if values.get("image") is not None:
            values["image"] = str(values["image"])

        updated_profile = await self.db.fetch_one(
            query=UPDATE_PROFILE_QUERY,
            values=values,
        )

        return OwnerProfileInDB(**updated_profile)

    async def link_user_to_profile(self, *, profile_id: str, user_id: str) -> OwnerProfileInDB:
        # Attaches a user_id to an existing (account-less) owner profile.
        updated_profile = await self.db.fetch_one(
            query=LINK_USER_TO_PROFILE_QUERY,
            values={"id": profile_id, "user_id": user_id},
        )

        if not updated_profile:
            return None

        return OwnerProfileInDB(**updated_profile)
